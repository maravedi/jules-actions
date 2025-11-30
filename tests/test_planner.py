import unittest
from unittest.mock import MagicMock, patch
from jules_planner.client import JulesPlanner

class TestJulesPlanner(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        self.repo_owner = "test_owner"
        self.repo_name = "test_repo"
        self.planner = JulesPlanner(self.api_key, self.repo_owner, self.repo_name)

    def test_init(self):
        self.assertEqual(self.planner.api_key, self.api_key)
        self.assertEqual(self.planner.repo_owner, self.repo_owner)
        self.assertEqual(self.planner.repo_name, self.repo_name)
        self.assertEqual(self.planner.base_url, "https://jules.googleapis.com/v1alpha")

    def test_init_missing_key(self):
        with self.assertRaises(ValueError):
            JulesPlanner("", "owner", "repo")

    @patch("requests.request")
    def test_list_sources(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"sources": [{"name": "source1"}]}
        mock_request.return_value = mock_response

        sources = self.planner.list_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["name"], "source1")
        mock_request.assert_called_with(
            "GET",
            "https://jules.googleapis.com/v1alpha/sources",
            headers={'X-Goog-Api-Key': 'test_key', 'Content-Type': 'application/json'},
            timeout=60
        )

    @patch("jules_planner.client.JulesPlanner.list_sources")
    def test_find_source(self, mock_list_sources):
        mock_list_sources.return_value = [
            {
                "name": "target_source",
                "githubRepo": {
                    "owner": self.repo_owner,
                    "repo": self.repo_name
                }
            },
            {
                "name": "other_source",
                "githubRepo": {
                    "owner": "other",
                    "repo": "repo"
                }
            }
        ]

        source_name = self.planner.find_source()
        self.assertEqual(source_name, "target_source")

    @patch("jules_planner.client.JulesPlanner.list_sources")
    def test_find_source_not_found(self, mock_list_sources):
        mock_list_sources.return_value = []
        source_name = self.planner.find_source()
        self.assertIsNone(source_name)

    def test_build_planning_prompt(self):
        context = {
            "title": "Test Issue",
            "body": "This is a test issue.",
            "comment": "@jules plan",
            "number": 1,
            "is_pr": False
        }
        prompt = self.planner._build_planning_prompt(context)
        self.assertIn("Test Issue", prompt)
        self.assertIn("This is a test issue", prompt)
        self.assertIn("Issue #1", prompt)

if __name__ == '__main__':
    unittest.main()
