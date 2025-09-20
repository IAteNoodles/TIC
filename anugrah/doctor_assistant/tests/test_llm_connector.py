import unittest
from unittest.mock import patch, Mock
import sys
import os
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connectors.llm_connector import call_llm

class TestLlmConnector(unittest.TestCase):

    @patch('connectors.llm_connector.requests.post')
    def test_call_llm_success(self, mock_post):
        """
        Test a successful call to the LLM connector.
        """
        # Configure the mock to return a successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "model": "test-model"
        }
        mock_post.return_value = mock_response

        response = call_llm(
            model_name="test-model",
            endpoint="http://fake-endpoint/v1/chat/completions",
            system_prompt="System prompt",
            user_prompt="User prompt"
        )

        # Assertions
        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], "Test response")
        mock_post.assert_called_once()

    @patch('connectors.llm_connector.requests.post')
    def test_call_llm_request_exception(self, mock_post):
        """
        Test the LLM connector's handling of a network request exception.
        """
        # Configure the mock to raise a RequestException
        mock_post.side_effect = requests.exceptions.RequestException("Test network error")

        response = call_llm(
            model_name="test-model",
            endpoint="http://fake-endpoint/v1/chat/completions",
            system_prompt="System prompt",
            user_prompt="User prompt"
        )

        # Assertions
        self.assertIn("error", response)
        self.assertIn("Failed to connect", response["error"])
        mock_post.assert_called_once()

    @patch('connectors.llm_connector.requests.post')
    def test_call_llm_bad_status_code(self, mock_post):
        """
        Test the LLM connector's handling of a non-200 status code.
        """
        # Configure the mock to return a failed response
        mock_response = Mock()
        mock_response.status_code = 500
        # The raise_for_status method is called in the original function
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_post.return_value = mock_response

        response = call_llm(
            model_name="test-model",
            endpoint="http://fake-endpoint/v1/chat/completions",
            system_prompt="System prompt",
            user_prompt="User prompt"
        )

        # Assertions
        self.assertIn("error", response)
        self.assertIn("Failed to connect", response["error"])
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()
