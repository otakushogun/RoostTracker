import unittest

from geoalchemy2 import Geometry

from backend.models import Base


class DatabaseModelTests(unittest.TestCase):
    def test_postgis_models_match_initialized_tables(self):
        tables = Base.metadata.tables
        self.assertEqual(set(tables), {"radar_scans", "bio_gates", "roost_centroids"})
        self.assertIsInstance(tables["bio_gates"].c.geom.type, Geometry)
        self.assertEqual(tables["bio_gates"].c.geom.type.geometry_type, "POLYGON")
        self.assertEqual(tables["roost_centroids"].c.geom.type.geometry_type, "POINT")


if __name__ == "__main__":
    unittest.main()
