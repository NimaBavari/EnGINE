import os
import unittest
from unittest.mock import MagicMock, patch

from api.custom_exc import DocumentRetrievalError
from api.main import app, get_recommendations, redis_instance, repo  # noqa: F401
from flask import Flask  # noqa: F401


class SearchTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        os.environ["MLAPI_BASE_URL"] = "localhost:5070"
        os.environ["ES_CONN_STR"] = None
        os.environ["REDIS_RESULTS_CONN_STR"] = None

    def tearDown(self) -> None:
        del os.environ["MLAPI_BASE_URL"]
        del os.environ["ES_CONN_STR"]
        del os.environ["REDIS_RESULTS_CONN_STR"]

    @patch("api.main.redis_instance")
    @patch("api.main.requests.get")
    @patch("api.main.requests.post")
    @patch("api.main.repo.get_documents")
    @patch("api.main.get_recommendations")
    def test_search_success(self, mock_get_recommendations, mock_get_documents, mock_post, mock_get, mock_redis):
        # Mock request parameters
        query = "test query"
        sorted_query = "query+test"

        # Mock Redis
        mock_redis.get.return_value = None
        mock_redis.set = MagicMock()

        # Mock external API calls
        mock_get.return_value = MagicMock(status_code=404)
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"id": 1})

        # Mock repository response
        mock_get_documents.return_value = (
            {"1": {"content": "content", "id": "1"}},
            1.0,
            {"test": {"freqs": {"1": 1}, "idf": 1.0}, "query": {"freqs": {"1": 1}, "idf": 1.0}},
        )

        # Mock recommendations
        mock_get_recommendations.return_value = []

        # Make GET request to /search
        response = self.app.get("/search?q=" + query)

        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn("pages", response_data)
        self.assertIsInstance(response_data["pages"], list)
        mock_redis.set.assert_called_with(sorted_query, response_data["pages"])

    @patch("api.main.redis_instance")
    def test_search_cached_result(self, mock_redis):
        # Mock cached result
        cached_result = [{"id": "1", "content": "cached content", "score": 1}]
        mock_redis.get.return_value = cached_result

        # Make GET request to /search
        response = self.app.get("/search?q=test")

        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data, cached_result)

    def test_search_malformed_query(self):
        # Make GET request with incorrect query param
        response = self.app.get("/search?wrong_param=test")
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "Malformed query params")

    @patch("api.main.repo.get_documents")
    def test_search_document_retrieval_error(self, mock_get_documents):
        # Mock exception in document retrieval
        mock_get_documents.side_effect = DocumentRetrievalError("Test error")

        # Make GET request to /search
        response = self.app.get("/search?q=test")
        self.assertEqual(response.status_code, 500)
        response_data = response.get_json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "Something went wrong while fetching results.")


if __name__ == "__main__":
    unittest.main()
