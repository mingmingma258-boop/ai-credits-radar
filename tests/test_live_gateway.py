import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from ai_credits_radar.gateway import GatewaySafetyError, invoke_free_only, live_preflight
from ai_credits_radar.inventory import load_inventory
from ai_credits_radar.providers.aliyun import AliyunBailianAdapter
from ai_credits_radar.providers.base import FreeQuotaExhausted, InvocationResult, ProviderAdapter, ProviderCheck, ProviderInvocationError
from ai_credits_radar.worker import build_worker_prompt, run_worker, validate_worker_task

ROOT = Path(__file__).resolve().parents[1]


def safe_inventory(*, confirmed_at=None, stop=True, example=False):
    confirmed_at = confirmed_at or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "example": example,
        "resources": [{
            "id": "aliyun-safe", "provider": "Alibaba Cloud Model Studio", "resource_type": "api",
            "status": "available", "free_only": True, "billing_state": "free_quota_confirmed",
            "quota_state": "confirmed_available", "remaining": 10000, "unit": "tokens",
            "expires_at": "2099-01-01", "priority": 100,
            "models": [{"id": "qwen3.8-max", "tier": "A", "enabled": True}],
            "live_use": {"provider_id": "aliyun-bailian", "allow_live": True, "free_quota_only": stop,
                         "paid_fallback_disabled": stop, "confirmed_at": confirmed_at,
                         "max_requests_per_run": 1, "max_output_tokens": 800},
        }],
    }


class FakeAdapter(ProviderAdapter):
    name = "Fake"
    provider_id = "aliyun-bailian"

    def __init__(self, *, exhausted=False, provider_error=False):
        self.calls = 0
        self.exhausted = exhausted
        self.provider_error = provider_error
        self.last_kwargs = {}

    def check_credentials(self): return ProviderCheck(True, "configured", "fake")
    def check_region(self): return ProviderCheck(True, "configured", "fake")
    def check_quota(self): return ProviderCheck(False, "unknown", "gateway owns quota proof")
    def list_models(self): return [{"id": "qwen3.8-max", "tier": "A"}]
    def estimate_cost(self, *, model, max_tokens): return ProviderCheck(False, "unknown", "gateway owns billing proof")

    def invoke(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        if self.exhausted:
            raise FreeQuotaExhausted("free quota exhausted")
        if self.provider_error:
            raise ProviderInvocationError("simulated timeout")
        return InvocationResult("ok", kwargs["model"], {"prompt_tokens": 10, "completion_tokens": 2})

    def redact_logs(self, text): return text


class FakeHTTPResponse(io.BytesIO):
    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = {"x-request-id": "req-test"}


class GatewayTests(unittest.TestCase):
    def test_example_inventory_can_dry_run_but_never_live(self):
        inventory = load_inventory(ROOT / "data" / "credits_inventory.example.json")
        dry = invoke_free_only(inventory, prompt="hello", dry_run=True)
        self.assertEqual(dry["status"], "dry_run")
        self.assertFalse(dry["request_sent"])
        with self.assertRaises(GatewaySafetyError):
            invoke_free_only(inventory, prompt="hello", dry_run=False)

    def test_missing_stop_protection_hard_stops(self):
        with self.assertRaisesRegex(GatewaySafetyError, "stop protection"):
            live_preflight(safe_inventory(stop=False))

    def test_stale_confirmation_hard_stops(self):
        stale = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        with self.assertRaisesRegex(GatewaySafetyError, "stale"):
            live_preflight(safe_inventory(confirmed_at=stale))

    def test_oversized_prompt_stops_before_adapter(self):
        adapter = FakeAdapter()
        with self.assertRaisesRegex(GatewaySafetyError, "character FREE_ONLY safety cap"):
            invoke_free_only(safe_inventory(), prompt="x" * 50001, adapter_factory=lambda provider_id, model: adapter)
        self.assertEqual(adapter.calls, 0)

    def test_gateway_defaults_to_fast_no_thinking(self):
        adapter = FakeAdapter()
        result = invoke_free_only(safe_inventory(), prompt="hello", adapter_factory=lambda provider_id, model: adapter)
        self.assertEqual(result["status"], "success")
        self.assertEqual(adapter.calls, 1)
        self.assertIs(adapter.last_kwargs["enable_thinking"], False)
        self.assertIsNone(adapter.last_kwargs["thinking_budget"])
        self.assertEqual(result["preflight"]["thinking_mode"], "fast")

    def test_reasoning_profile_passes_bounded_budget(self):
        adapter = FakeAdapter()
        invoke_free_only(safe_inventory(), prompt="hard", enable_thinking=True, thinking_budget=256,
                         adapter_factory=lambda provider_id, model: adapter)
        self.assertIs(adapter.last_kwargs["enable_thinking"], True)
        self.assertEqual(adapter.last_kwargs["thinking_budget"], 256)

    def test_free_quota_exhaustion_is_hard_stop_without_retry(self):
        adapter = FakeAdapter(exhausted=True)
        with self.assertRaisesRegex(GatewaySafetyError, "free quota exhausted"):
            invoke_free_only(safe_inventory(), prompt="hello", adapter_factory=lambda provider_id, model: adapter)
        self.assertEqual(adapter.calls, 1)


class AliyunAdapterTests(unittest.TestCase):
    def test_direct_adapter_invocation_is_blocked_before_network(self):
        adapter = AliyunBailianAdapter(api_key="secret")
        with patch("ai_credits_radar.providers.aliyun.urlopen") as mocked:
            with self.assertRaisesRegex(ProviderInvocationError, "FREE_ONLY gateway"):
                adapter.invoke(prompt="hello")
            mocked.assert_not_called()

    def test_fast_mode_explicitly_disables_thinking_in_http_payload(self):
        adapter = AliyunBailianAdapter(api_key="secret", model="qwen3.8-max")
        response = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}], "usage": {"total_tokens": 12}})
        with patch("ai_credits_radar.providers.aliyun.urlopen", return_value=response) as mocked:
            result = adapter.invoke(prompt="hello", max_tokens=200, enable_thinking=False, gateway_authorized=True)
        request = mocked.call_args.args[0]
        payload = json.loads(request.data.decode())
        self.assertIs(payload["enable_thinking"], False)
        self.assertNotIn("thinking_budget", payload)
        self.assertEqual(payload["max_tokens"], 200)
        self.assertEqual(result.content, "ok")

    def test_reasoning_mode_includes_budget(self):
        adapter = AliyunBailianAdapter(api_key="secret", model="qwen3.8-max")
        response = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}], "usage": {}})
        with patch("ai_credits_radar.providers.aliyun.urlopen", return_value=response) as mocked:
            adapter.invoke(prompt="hello", enable_thinking=True, thinking_budget=256, gateway_authorized=True)
        payload = json.loads(mocked.call_args.args[0].data.decode())
        self.assertIs(payload["enable_thinking"], True)
        self.assertEqual(payload["thinking_budget"], 256)

    def test_403_free_tier_only_is_recognized_without_retry(self):
        adapter = AliyunBailianAdapter(api_key="secret")
        body = io.BytesIO(json.dumps({"code": "AllocationQuota.FreeTierOnly"}).encode())
        error = HTTPError("https://example.test", 403, "forbidden", {}, body)
        with patch("ai_credits_radar.providers.aliyun.urlopen", side_effect=error) as mocked:
            with self.assertRaises(FreeQuotaExhausted):
                adapter.invoke(prompt="hello", gateway_authorized=True)
            self.assertEqual(mocked.call_count, 1)


class WorkerTests(unittest.TestCase):
    def test_worker_rejects_context_traversal(self):
        task = {"project": "P001", "task_id": "TEST", "goal": "review", "context_files": ["../secret.txt"], "tier": "A", "max_output_tokens": 100}
        self.assertEqual(validate_worker_task(task), [])
        with self.assertRaisesRegex(ValueError, "unsafe context path"):
            build_worker_prompt(task, repo_root=ROOT)

    def test_worker_rejects_local_private_context_even_when_allowlisted(self):
        task = {"project": "P001", "task_id": "TEST", "goal": "review", "context_files": ["data/profile.local.json"], "tier": "A", "max_output_tokens": 100}
        with self.assertRaisesRegex(ValueError, "local/private"):
            build_worker_prompt(task, repo_root=ROOT)

    def test_worker_dry_run_writes_artifacts_without_provider(self):
        task = {"project": "P001", "task_id": "TEST", "goal": "review routing", "context_files": ["src/ai_credits_radar/routing.py"], "tier": "A", "max_output_tokens": 200, "thinking_mode": "fast"}
        inventory = load_inventory(ROOT / "data" / "credits_inventory.example.json")
        with tempfile.TemporaryDirectory() as tmp:
            metadata = run_worker(task, inventory, repo_root=ROOT, output_dir=tmp, dry_run=True)
            self.assertTrue(metadata["dry_run"])
            self.assertEqual(metadata["thinking_mode"], "fast")
            self.assertTrue((Path(tmp) / "run.json").is_file())
            self.assertTrue((Path(tmp) / "prompt-preview.md").is_file())

    def test_provider_failure_still_leaves_audit_artifact(self):
        task = {"project": "P001", "task_id": "TEST", "goal": "review routing", "context_files": ["src/ai_credits_radar/routing.py"], "tier": "A", "max_output_tokens": 200, "thinking_mode": "fast"}
        inventory = safe_inventory()
        adapter = FakeAdapter(provider_error=True)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("ai_credits_radar.gateway._adapter_for", return_value=adapter):
                with self.assertRaises(ProviderInvocationError):
                    run_worker(task, inventory, repo_root=ROOT, output_dir=tmp)
            metadata = json.loads((Path(tmp) / "run.json").read_text())
            self.assertEqual(metadata["gateway_status"], "provider_error")
            self.assertTrue(metadata["request_may_have_been_sent"])
            self.assertTrue((Path(tmp) / "failure.md").is_file())


class WorkflowTests(unittest.TestCase):
    def test_worker_workflow_scopes_secret_and_defaults_fast(self):
        text = (ROOT / ".github" / "workflows" / "free-ai-worker.yml").read_text(encoding="utf-8")
        self.assertEqual(text.count("DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}"), 1)
        self.assertIn("WORKER_THINKING_MODE: ${{ inputs.thinking_mode }}", text)
        self.assertIn("options: [fast, reasoning]", text)
        self.assertIn('default: "200"', text)


if __name__ == "__main__":
    unittest.main()
