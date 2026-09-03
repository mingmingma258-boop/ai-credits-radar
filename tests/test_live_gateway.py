import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from ai_credits_radar.gateway import GatewaySafetyError, invoke_free_only, live_preflight
from ai_credits_radar.inventory import load_inventory, validate_inventory
from ai_credits_radar.providers.aliyun import AliyunBailianAdapter
from ai_credits_radar.providers.base import (
    FreeQuotaExhausted,
    InvocationResult,
    ProviderAdapter,
    ProviderCheck,
    ProviderInvocationError,
)
from ai_credits_radar.worker import build_worker_prompt, run_worker, validate_worker_task

ROOT = Path(__file__).resolve().parents[1]


def safe_inventory(*, confirmed_at=None, stop=True, example=False):
    confirmed_at = confirmed_at or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "example": example,
        "resources": [
            {
                "id": "aliyun-safe",
                "provider": "Alibaba Cloud Model Studio",
                "resource_type": "api",
                "status": "available",
                "free_only": True,
                "billing_state": "free_quota_confirmed",
                "quota_state": "confirmed_available",
                "remaining": 10000,
                "unit": "tokens",
                "expires_at": "2099-01-01",
                "priority": 100,
                "models": [{"id": "qwen-plus", "tier": "A", "enabled": True}],
                "live_use": {
                    "provider_id": "aliyun-bailian",
                    "allow_live": True,
                    "free_quota_only": stop,
                    "paid_fallback_disabled": stop,
                    "confirmed_at": confirmed_at,
                    "max_requests_per_run": 1,
                    "max_output_tokens": 800,
                },
            }
        ],
    }


class FakeAdapter(ProviderAdapter):
    name = "Fake"
    provider_id = "aliyun-bailian"

    def __init__(self, *, exhausted=False):
        self.calls = 0
        self.exhausted = exhausted

    def check_credentials(self):
        return ProviderCheck(True, "configured", "fake")

    def check_region(self):
        return ProviderCheck(True, "configured", "fake")

    def check_quota(self):
        return ProviderCheck(False, "unknown", "gateway owns quota proof")

    def list_models(self):
        return [{"id": "qwen-plus", "tier": "A"}]

    def estimate_cost(self, *, model, max_tokens):
        return ProviderCheck(False, "unknown", "gateway owns billing proof")

    def invoke(self, **kwargs):
        self.calls += 1
        self.assert_authorized = kwargs.get("gateway_authorized") is True
        if self.exhausted:
            raise FreeQuotaExhausted("free quota exhausted")
        return InvocationResult("ok", kwargs["model"], {"prompt_tokens": 10, "completion_tokens": 2})

    def redact_logs(self, text):
        return text


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

    def test_gateway_sends_exactly_one_mocked_request(self):
        adapter = FakeAdapter()
        result = invoke_free_only(
            safe_inventory(),
            prompt="hello",
            max_tokens=5000,
            adapter_factory=lambda provider_id, model: adapter,
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(adapter.calls, 1)
        self.assertTrue(adapter.assert_authorized)
        self.assertEqual(result["preflight"]["max_output_tokens"], 800)

    def test_free_quota_exhaustion_is_hard_stop_without_retry(self):
        adapter = FakeAdapter(exhausted=True)
        with self.assertRaisesRegex(GatewaySafetyError, "free quota exhausted"):
            invoke_free_only(
                safe_inventory(),
                prompt="hello",
                adapter_factory=lambda provider_id, model: adapter,
            )
        self.assertEqual(adapter.calls, 1)


class AliyunAdapterTests(unittest.TestCase):
    def test_direct_adapter_invocation_is_blocked_before_network(self):
        adapter = AliyunBailianAdapter(api_key="secret")
        with patch("ai_credits_radar.providers.aliyun.urlopen") as mocked:
            with self.assertRaisesRegex(ProviderInvocationError, "FREE_ONLY gateway"):
                adapter.invoke(prompt="hello")
            mocked.assert_not_called()

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
        task = {
            "project": "P001",
            "task_id": "TEST",
            "goal": "review",
            "context_files": ["../secret.txt"],
            "tier": "A",
            "max_output_tokens": 100,
        }
        self.assertEqual(validate_worker_task(task), [])
        with self.assertRaisesRegex(ValueError, "unsafe context path"):
            build_worker_prompt(task, repo_root=ROOT)

    def test_worker_dry_run_writes_artifacts_without_provider(self):
        task = {
            "project": "P001",
            "task_id": "TEST",
            "goal": "review routing",
            "context_files": ["src/ai_credits_radar/routing.py"],
            "tier": "A",
            "max_output_tokens": 200,
        }
        inventory = load_inventory(ROOT / "data" / "credits_inventory.example.json")
        with tempfile.TemporaryDirectory() as tmp:
            metadata = run_worker(task, inventory, repo_root=ROOT, output_dir=tmp, dry_run=True)
            self.assertTrue(metadata["dry_run"])
            self.assertTrue((Path(tmp) / "run.json").is_file())
            self.assertTrue((Path(tmp) / "prompt-preview.md").is_file())
            self.assertFalse((Path(tmp) / "model-output.md").exists())


class WorkflowTests(unittest.TestCase):
    def test_worker_workflow_scopes_secret_to_live_step(self):
        text = (ROOT / ".github" / "workflows" / "free-ai-worker.yml").read_text(encoding="utf-8")
        self.assertEqual(text.count("DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}"), 1)
        self.assertIn("WORKER_TASK_TEXT: ${{ inputs.task_text }}", text)
        self.assertNotIn('run: python scripts/free_ai_worker.py "${{ inputs.task_text }}"', text)
        self.assertIn("default: false", text)


if __name__ == "__main__":
    unittest.main()
