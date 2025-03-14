import os
import pytest
import httpx
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.facebook_service import FacebookService


class TestFacebookEventFetching:
    """Tests for event fetching functionality in the FacebookService class."""

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
    def test_fetch_events_successful(self, mock_client, facebook_service):
        """Test successful fetching of events from a Facebook page."""
        # Create mock response with sample event data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "123456789",
                    "name": "Test Event",
                    "description": "This is a test event",
                    "start_time": "2025-04-01T18:00:00+0000",
                    "end_time": "2025-04-01T21:00:00+0000",
                    "place": {
                        "name": "Test Venue",
                        "location": {
                            "city": "Test City",
                            "country": "Test Country",
                            "latitude": 37.4847,
                            "longitude": -122.1477,
                            "street": "123 Test St"
                        }
                    },
                    "is_online": False,
                    "attending_count": 10,
                    "interested_count": 20
                }
            ],
            "paging": {
                "cursors": {
                    "before": "before_cursor",
                    "after": "after_cursor"
                },
                "next": "https://graph.facebook.com/v17.0/next_page"
            }
        }
        
        # Configure mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Create mock database page
        mock_db_page = MagicMock()
        mock_db_page.id = 1
        mock_db_page.fb_page_id = "page123"
        mock_db_page.name = "Test Page"
        
        # Mock the database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing event
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Call the method to fetch events
        events = facebook_service.fetch_events(mock_db, mock_db_page, limit=10)
        
        # Verify the API was called correctly
        fields = "id,name,description,start_time,end_time,place,is_online,attending_count,interested_count"
        expected_url = f"{facebook_service.graph_api_base}/{mock_db_page.fb_page_id}/events?fields={fields}&limit=10&access_token={facebook_service.access_token}"
        mock_client_instance.get.assert_called_once_with(expected_url)
        
        # Verify the events were processed correctly
        assert len(events) == 1
        assert events[0].name == "Test Event"
        assert events[0].description == "This is a test event"
        assert events[0].location == "Test Venue, Test City, Test Country"
        assert events[0].is_online == False
        assert events[0].attending_count == 10
        assert events[0].interested_count == 20
    
    @patch("httpx.Client")
    def test_fetch_events_api_error(self, mock_client, facebook_service):
        """Test handling of API errors when fetching events."""
        # Configure mock client to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.HTTPError("API error")
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Create mock database page
        mock_db_page = MagicMock()
        mock_db_page.id = 1
        mock_db_page.fb_page_id = "page123"
        mock_db_page.name = "Test Page"
        
        # Mock the database session
        mock_db = MagicMock()
        
        # Call the method to fetch events
        events = facebook_service.fetch_events(mock_db, mock_db_page, limit=10)
        
        # Verify the API was called
        fields = "id,name,description,start_time,end_time,place,is_online,attending_count,interested_count"
        expected_url = f"{facebook_service.graph_api_base}/{mock_db_page.fb_page_id}/events?fields={fields}&limit=10&access_token={facebook_service.access_token}"
        mock_client_instance.get.assert_called_once_with(expected_url)
        
        # Verify that an empty list is returned when there's an error
        assert events == []
    
    @patch("httpx.Client")
    def test_fetch_events_empty_response(self, mock_client, facebook_service):
        """Test handling of empty response when fetching events."""
        # Create mock response with no events
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [],
            "paging": {
                "cursors": {
                    "before": "before_cursor",
                    "after": "after_cursor"
                }
            }
        }
        
        # Configure mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Create mock database page
        mock_db_page = MagicMock()
        mock_db_page.id = 1
        mock_db_page.fb_page_id = "page123"
        mock_db_page.name = "Test Page"
        
        # Mock the database session
        mock_db = MagicMock()
        
        # Call the method to fetch events
        events = facebook_service.fetch_events(mock_db, mock_db_page, limit=10)
        
        # Verify the API was called correctly
        fields = "id,name,description,start_time,end_time,place,is_online,attending_count,interested_count"
        expected_url = f"{facebook_service.graph_api_base}/{mock_db_page.fb_page_id}/events?fields={fields}&limit=10&access_token={facebook_service.access_token}"
        mock_client_instance.get.assert_called_once_with(expected_url)
        
        # Verify that an empty list is returned when there are no events
        assert events == []
