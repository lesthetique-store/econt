import unittest

from api import Econt
from status_codes import StatusCode

class TestEcont(unittest.TestCase):

    def setUp(self):
        self.econt = Econt("iasp-dev", "iasp-dev")

    def test_get_countries(self):
        result = self.econt.get_countries()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_cities(self):
        result = self.econt.get_cities()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_offices(self):
        result = self.econt.get_offices()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_streets(self):
        result = self.econt.get_streets()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_streets_by_city(self):
        result = self.econt.get_streets_by_city(city_post_code="1407")
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_offices_by_city(self):
        result = self.econt.get_offices_by_city(city_post_code="1407")
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_quarters(self):
        result = self.econt.get_quarters()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_seller_addresses(self):
        result = self.econt.get_seller_addresses()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_regions(self):
        result = self.econt.get_regions()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_zones(self):
        result = self.econt.get_zones()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

    def test_get_clients(self):
        result = self.econt.get_clients()
        self.assertEqual(result["status"], StatusCode.STATUS_OK)

if __name__ == '__main__':
    unittest.main()