"""Tests for the database leakage rule."""

from pathlib import Path

from sentinel.manifest.loader import load_manifest
from sentinel.violation_engine import analyze_repository

FIXTURES = Path(__file__).parent / "fixtures"
LEAK = FIXTURES / "LEAK"
GOOD = FIXTURES / "GOOD"
BAD = FIXTURES / "BAD"
MANIFEST = FIXTURES / "manifest.yaml"


def _db_leakage(result):
    return [v for v in result.violations if v.rule == "database-leakage"]


class TestDatabaseLeakage:
    def test_detects_direct_dependency_to_repository(self):
        manifest = load_manifest(MANIFEST)
        result = analyze_repository(LEAK, manifest)
        leaks = _db_leakage(result)
        assert len(leaks) == 1
        assert leaks[0].components == (
            "presentation/app.ts",
            "repository/user_repo.ts",
        )
        assert leaks[0].severity.value == "error"

    def test_no_leakage_in_good_fixture(self):
        manifest = load_manifest(MANIFEST)
        result = analyze_repository(GOOD, manifest)
        leaks = _db_leakage(result)
        assert leaks == []

    def test_no_false_positives_from_bad_fixture(self):
        manifest = load_manifest(MANIFEST)
        result = analyze_repository(BAD, manifest)
        leaks = _db_leakage(result)
        assert leaks == []
