import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from ai_credits_radar.catalog import DEFAULT_DATA_PATH, load_catalog, programs_from
from ai_credits_radar.cli import main as cli_main
from ai_credits_radar.eligibility import assess_program, validate_profile
from ai_credits_radar.inventory import inventory_summary, validate_inventory
from ai_credits_radar.providers.aliyun import AliyunBailianAdapter
from ai_credits_radar.review import audit_catalog, render_markdown
from ai_credits_radar.routing import select_free_route


class ReviewTests(unittest.TestCase):
    def test_current_catalog_renders_offline_review(self):
        report = audit_catalog(load_catalog(DEFAULT_DATA_PATH), today=date(2026, 9, 3))
        self.assertEqual(report["validation_errors"], [])
        self.assertEqual(report["total"], len(programs_from(load_catalog(DEFAULT_DATA_PATH))))
        markdown = render_markdown(report)
        self.assertIn("offline catalog audit", markdown)
        self.assertIn("Billing / payment attention", markdown)


class EligibilityTests(unittest.TestCase):
    def test_profile_rejects_unknown_sensitive_style_fields(self):
        errors = validate_profile({"region": "CN", "student": True, "name": "Example"})
        self.assertTrue(any("unsupported profile fields" in error for error in errors))

    def test_startup_program_is_not_match_for_non_startup_profile(self):
        program = {
            "id": "startup-x",
            "provider": "Example",
            "name": "Startup credits",
            "kind": "startup",
            "access": "application",
            "eligibility": ["startup"],
            "requirements": ["application review"],
            "tags": ["startup"],
            "handoff": "application-review",
            "status": "conditional",
            "application_url": "https://example.com/apply",
            "evidence_url": "https://example.com/terms",
        }
        profile = {
            "region": "CN",
            "student": True,
            "independent_developer": True,
            "startup": False,
            "researcher": True,
            "has_student_email": True,
            "has_github": True,
            "allow_payment_method": False,
            "accept_identity_verification": True,
        }
        result = assess_program(program, profile)
        self.assertEqual(result["decision"], "not_match")
        self.assertFalse(result["authoritative"])


class InventoryAndRoutingTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "schema_version": 1,
            "resources": [
                {
                    "id": "expiring-a",
                    "provider": "Example A",
                    "resource_type": "api",
                    "status": "available",
                    "free_only": True,
                    "billing_state": "free_quota_confirmed",
                    "quota_state": "confirmed_available",
                    "remaining": 5000,
                    "unit": "tokens",
                    "expires_at": "2026-09-10",
                    "priority": 60,
                    "models": [{"id": "model-a", "tier": "A", "enabled": True}],
                },
                {
                    "id": "unknown-cheap-looking",
                    "provider": "Example Unknown",
                    "resource_type": "api",
                    "status": "available",
                    "free_only": True,
                    "billing_state": "unknown",
                    "quota_state": "unknown",
                    "remaining": None,
                    "unit": "tokens",
                    "expires_at": None,
                    "priority": 100,
                    "models": [{"id": "model-s", "tier": "S", "enabled": True}],
                },
            ],
        }

    def test_inventory_is_valid_and_summary_is_fail_closed(self):
        self.assertEqual(validate_inventory(self.inventory), [])
        result = inventory_summary(self.inventory, today=date(2026, 9, 3))
        self.assertEqual(result["confirmed_safe_free"], 1)
        self.assertEqual(result["unknown_billing"], 1)

    def test_router_rejects_unknown_billing_and_selects_confirmed_free(self):
        result = select_free_route(self.inventory, required_tier="A", today=date(2026, 9, 3))
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["resource_id"], "expiring-a")
        self.assertTrue(any(item["id"] == "unknown-cheap-looking" for item in result["rejections"]))

    def test_router_hard_stops_when_only_unknown_route_exists(self):
        inventory = {"schema_version": 1, "resources": [self.inventory["resources"][1]]}
        result = select_free_route(inventory, required_tier="A", today=date(2026, 9, 3))
        self.assertEqual(result["status"], "hard_stop")
        self.assertIn("FREE_ONLY", result["reason"])


class AdapterTests(unittest.TestCase):
    def test_aliyun_adapter_never_displays_key(self):
        secret = "super-secret-test-key"
        adapter = AliyunBailianAdapter(api_key=secret)
        check = adapter.check_credentials()
        self.assertTrue(check.ok)
        self.assertNotIn(secret, check.detail)
        self.assertEqual(adapter.redact_logs(f"token={secret}"), "token=[REDACTED]")
        self.assertEqual(adapter.check_quota().state, "unknown")
        with self.assertRaises(RuntimeError):
            adapter.invoke(prompt="hello")

    def test_from_env_key_is_not_echoed(self):
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "hidden-value"}, clear=False):
            adapter = AliyunBailianAdapter.from_env()
            self.assertNotIn("hidden-value", adapter.check_credentials().detail)


class CliIntegrationTests(unittest.TestCase):
    def test_inventory_and_route_commands(self):
        inventory = {
            "schema_version": 1,
            "resources": [
                {
                    "id": "free-a",
                    "provider": "Example",
                    "resource_type": "api",
                    "status": "available",
                    "free_only": True,
                    "billing_state": "free_tier_confirmed",
                    "quota_state": "ongoing_free_tier",
                    "remaining": None,
                    "unit": "requests",
                    "expires_at": None,
                    "priority": 50,
                    "models": [{"id": "model-a", "tier": "A", "enabled": True}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inventory.json"
            path.write_text(json.dumps(inventory), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli_main(["inventory", "--inventory", str(path), "--json"]), 0)
            self.assertIn("confirmed_safe_free", out.getvalue())
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli_main(["route", "--inventory", str(path), "--tier", "A", "--json"]), 0)
            self.assertIn('"status": "selected"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
