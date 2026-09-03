import json
import unittest
from pathlib import Path

from ai_credits_radar.catalog import (
    DEFAULT_DATA_PATH,
    filter_programs,
    load_catalog,
    programs_from,
    summary,
    validate_catalog,
)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(DEFAULT_DATA_PATH)
        cls.programs = programs_from(cls.catalog)

    def test_catalog_is_valid(self):
        self.assertEqual(validate_catalog(self.catalog), [])

    def test_ids_are_unique(self):
        ids = [program["id"] for program in self.programs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_gpu_filter_returns_gpu_records(self):
        records = filter_programs(self.programs, resource_type="gpu")
        self.assertGreaterEqual(len(records), 5)
        self.assertTrue(all("gpu" in record["resource_types"] for record in records))

    def test_application_filter(self):
        records = filter_programs(self.programs, application_only=True)
        self.assertGreaterEqual(len(records), 4)
        self.assertTrue(all(record["access"] == "application" for record in records))

    def test_search_is_case_insensitive(self):
        records = filter_programs(self.programs, query="HUGGINGFACE")
        self.assertEqual([record["id"] for record in records], ["huggingface-zerogpu"])

    def test_summary_is_consistent(self):
        result = summary(self.programs)
        self.assertEqual(result["total"], len(self.programs))
        self.assertEqual(sum(result["by_kind"].values()), len(self.programs))


class ValidationTests(unittest.TestCase):
    def test_duplicate_and_bad_url_are_reported(self):
        catalog = {
            "programs": [
                {
                    "id": "duplicate",
                    "provider": "Provider",
                    "name": "Name",
                    "kind": "api",
                    "resource_types": ["api"],
                    "status": "active",
                    "access": "free-tier",
                    "benefit": "Benefit",
                    "amount_display": "Free",
                    "amount_usd_max": None,
                    "eligibility": ["Anyone"],
                    "requirements": ["Account"],
                    "application_url": "http://example.com",
                    "evidence_url": "https://example.com",
                    "evidence_type": "official",
                    "last_verified": "2026-09-03",
                    "priority": 50,
                    "handoff": "none",
                },
            ]
        }
        errors = validate_catalog(catalog)
        self.assertTrue(any("application_url" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

