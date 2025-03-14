import os
import pytest
import httpx
from unittest.mock import patch, MagicMock

from app.services.facebook_service import FacebookService


class TestFacebookService:
    """Tests for the FacebookService class."""

    @pytest.fixture
    def facebook_service(self):
        """Create a FacebookService instance for testing."""
        # Set environment variables for testing
        os.environ["FACEBOOK_APP_ID"] = "test_app_id"
        os.environ["FACEBOOK_APP_SECRET"] = "test_app_secret"
        os.environ["FACEBOOK_ACCESS_TOKEN"] = "test_access_token"
        os.environ["MAX_PAGES_PER_FETCH"] = "5"
        os.environ["MAX_EVENTS_PER_PAGE"] = "25"
        
        # Create and return service instance
        service = FacebookService()
        return service
    
    @patch("httpx.Client")
    def test_successful_connection_to_graph_api(self, mock_client, facebook_service):
        """Test successful connection to the Facebook Graph API."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456789",
            "name": "Test Page",
            "link": "https://facebook.com/testpage"
        }
        
        # Configure mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Create test data
        from app.models.schemas import PageCreate
        test_page = PageCreate(
            fb_page_id="123456789",
            name=None,
            page_url=None
        )
        
        # Mock the database session
        mock_db = MagicMock()
        mock_db_page = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Call the method that makes the API request
        result = facebook_service.add_page(mock_db, test_page)
        
        # Verify the API was called correctly
        expected_url = f"{facebook_service.graph_api_base}/123456789?fields=name,description,link&access_token={facebook_service.access_token}"
        mock_client_instance.get.assert_called_once_with(expected_url)
        
        # Verify the response was processed correctly
        assert result.fb_page_id == "123456789"
        assert result.name == "Test Page"
        assert result.page_url == "https://facebook.com/testpage"
    
    @patch("httpx.Client")
    def test_connection_error_handling(self, mock_client, facebook_service):
        """Test handling of connection errors when connecting to the Facebook Graph API."""
        # Configure mock client to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.HTTPError("Connection error")
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Create test data
        from app.models.schemas import PageCreate
        test_page = PageCreate(
            fb_page_id="123456789",
            name="Fallback Name",
            page_url="https://fallback-url.com"
        )
        
        # Mock the database session
        mock_db = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Call the method that makes the API request
        result = facebook_service.add_page(mock_db, test_page)
        
        # Verify the API was called
        expected_url = f"{facebook_service.graph_api_base}/123456789?fields=name,description,link&access_token={facebook_service.access_token}"
        mock_client_instance.get.assert_called_once_with(expected_url)
        
        # Verify that the fallback values were used
        assert result.fb_page_id == "123456789"
        assert result.name == "Fallback Name"
        assert result.page_url == "https://fallback-url.com"
