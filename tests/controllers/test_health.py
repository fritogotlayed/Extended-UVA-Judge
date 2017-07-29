import unittest
from extended_uva_judge import server


class TestHealth(unittest.TestCase):

    def setUp(self):
        app, cfg = server.build_app()
        app.testing = True
        self.app = app.test_client()
        self.app_config = cfg

    def tearDown(self):
        pass

    def test_health_returns_200(self):
        rv = self.app.get('/health')
        self.assertEqual(200, rv.status_code)
