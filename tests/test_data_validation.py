"""
Tests for data validation and mock data consistency
Law 3: min 1 success + 1 failure per function
Law 6: every output number traceable to source ±0.01
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'watchdog'))

from validate_data import validate_checksum, range_check


# ============================================================================
# validate_checksum
# ============================================================================

class TestValidateChecksum:
    def test_checksum_store_and_verify(self, tmp_path, monkeypatch):
        """Success: stored checksum matches on re-verification"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog/data_checksums", exist_ok=True)
        os.makedirs("watchdog", exist_ok=True)
        # Create audit.log so log_audit works
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [{"store": "Bondi", "revenue": 100000}]
        assert validate_checksum("test_data", data, store=True) is True
        assert validate_checksum("test_data", data, store=False) is True

    def test_checksum_mismatch(self, tmp_path, monkeypatch):
        """Failure: changed data causes checksum mismatch"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog/data_checksums", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        original = [{"store": "Bondi", "revenue": 100000}]
        validate_checksum("test_mismatch", original, store=True)

        modified = [{"store": "Bondi", "revenue": 999999}]
        assert validate_checksum("test_mismatch", modified, store=False) is False


# ============================================================================
# range_check
# ============================================================================

class TestRangeCheck:
    def test_range_check_valid(self, tmp_path, monkeypatch):
        """Success: values within range pass"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [
            {"revenue": 50000},
            {"revenue": 100000},
            {"revenue": 200000}
        ]
        assert range_check(data, "revenue", min_val=0, max_val=500000) is True

    def test_range_check_negative_revenue(self, tmp_path, monkeypatch):
        """Failure: negative revenue flagged"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [
            {"revenue": 50000},
            {"revenue": -100}  # Invalid
        ]
        assert range_check(data, "revenue", min_val=0) is False

    def test_range_check_exceeds_max(self, tmp_path, monkeypatch):
        """Failure: value exceeding max flagged"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [{"qty": 200000}]
        assert range_check(data, "qty", max_val=100000) is False

    def test_range_check_null_not_allowed(self, tmp_path, monkeypatch):
        """Failure: null values flagged when not allowed"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [{"revenue": None}]
        assert range_check(data, "revenue", min_val=0, allow_null=False) is False

    def test_range_check_null_allowed(self, tmp_path, monkeypatch):
        """Success: null values accepted when allowed"""
        monkeypatch.chdir(tmp_path)
        os.makedirs("watchdog", exist_ok=True)
        with open("watchdog/audit.log", "w") as f:
            f.write("")

        data = [{"revenue": None}, {"revenue": 50000}]
        assert range_check(data, "revenue", min_val=0, allow_null=True) is True


# ============================================================================
# Mock data consistency (seeded random)
# ============================================================================

class TestMockDataConsistency:
    def test_sales_data_deterministic(self):
        """Success: same seed produces same data"""
        import numpy as np
        import pandas as pd

        def generate(seed):
            rng = np.random.RandomState(seed)
            dates = pd.date_range(end="2026-02-13", periods=5, freq='D')
            data = []
            for date in dates:
                revenue = 8000 + rng.normal(0, 8000 * 0.15)
                data.append({"date": date, "revenue": max(0, revenue)})
            return data

        run1 = generate(42)
        run2 = generate(42)
        for r1, r2 in zip(run1, run2):
            assert abs(r1["revenue"] - r2["revenue"]) < 0.01

    def test_different_seed_different_data(self):
        """Success: different seeds produce different data"""
        import numpy as np

        rng1 = np.random.RandomState(42)
        rng2 = np.random.RandomState(99)

        val1 = rng1.normal(0, 1000)
        val2 = rng2.normal(0, 1000)
        assert val1 != val2
