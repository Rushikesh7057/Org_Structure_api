from django.test import TestCase, Client
from hierarchy.models import Asset

class AssetAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test asset
        self.asset = Asset.objects.create(name="Test Asset")

    def test_get_assets_list(self):
        response = self.client.get('/api/assets/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Asset")

    def test_get_asset_detail(self):
        response = self.client.get(f'/api/assets/{self.asset.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Asset")
