from django.test import TestCase, Client
from unittest.mock import patch

class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_liveness(self):
        response = self.client.get('/health/liveness/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "alive"})

    @patch('django.db.connections')
    def test_readiness_ready(self, mock_connections):
        mock_conn = mock_connections['default']
        mock_conn.cursor.return_value = True
        response = self.client.get('/health/readiness/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ready"})

    @patch('django.db.connections')
    def test_readiness_not_ready(self, mock_connections):
        mock_conn = mock_connections['default']
        mock_conn.cursor.side_effect = Exception("DB down")
        response = self.client.get('/health/readiness/')
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "not ready"})
