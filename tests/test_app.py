import unittest
from app import app, classify_event

class AegisNova AITests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("nebius_configured", response.get_json())

    def test_demo_events(self):
        response = self.client.get("/api/demo-events")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(len(data["events"]), 1)
        self.assertTrue(all(item.get("demo") for item in data["events"]))

    def test_analyze_requires_object(self):
        response = self.client.post("/api/analyze", json=["not", "an", "object"])
        self.assertEqual(response.status_code, 400)

    def test_fallback_classifier(self):
        result = classify_event({"event_type": "motion_detected"})
        self.assertIn(result["level"], {"NORMAL", "ATTENTION", "URGENT"})
        self.assertIn("method", result)

if __name__ == "__main__":
    unittest.main()
