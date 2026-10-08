import unittest
from datetime import datetime, timezone

import numpy as np

from backend.ingest_one_hour import (
    biological_gate_mask,
    list_scan_objects,
    scan_time_from_key,
)


class ScanTimeTests(unittest.TestCase):
    def test_parses_a_level_two_object_key(self):
        scan_time = scan_time_from_key(
            "2026/08/11/KRAX/KRAX20260811_100530_V06"
        )
        self.assertEqual(scan_time, datetime(2026, 8, 11, 10, 5, 30, tzinfo=timezone.utc))

    def test_ignores_non_scan_object_keys(self):
        self.assertIsNone(scan_time_from_key("2026/08/11/KRAX/metadata.txt"))

    def test_lists_only_the_requested_hour(self):
        class Paginator:
            def paginate(self, **kwargs):
                self.arguments = kwargs
                return [
                    {
                        "Contents": [
                            {"Key": f"2026/08/11/KRAX/KRAX20260811_{scan}_V06"}
                            for scan in ("095959", "100000", "105959", "110000")
                        ]
                    }
                ]

        class S3:
            def __init__(self):
                self.paginator = Paginator()

            def get_paginator(self, operation):
                self.operation = operation
                return self.paginator

        s3 = S3()
        scans = list_scan_objects(s3)
        self.assertEqual(
            [scan_time.strftime("%H%M%S") for _, scan_time in scans],
            ["100000", "105959"],
        )
        self.assertEqual(s3.paginator.arguments["Prefix"], "2026/08/11/KRAX/")


class BiologicalGateTests(unittest.TestCase):
    def test_accepts_threshold_boundaries(self):
        result = biological_gate_mask(
            np.array([0.35, 0.85]), np.array([2.0, 4.0]), np.array([5.0, 35.0])
        )
        self.assertEqual(result.tolist(), [True, True])

    def test_rejects_values_outside_any_threshold(self):
        result = biological_gate_mask(
            np.array([0.34, 0.5, 0.5, np.nan]),
            np.array([3.0, 1.99, 3.0, 3.0]),
            np.array([20.0, 20.0, 35.01, 20.0]),
        )
        self.assertEqual(result.tolist(), [False, False, False, False])

    def test_rejects_masked_measurements(self):
        result = biological_gate_mask(
            np.ma.array([0.5], mask=[True]),
            np.array([3.0]),
            np.array([20.0]),
        )
        self.assertEqual(result.tolist(), [False])


if __name__ == "__main__":
    unittest.main()
