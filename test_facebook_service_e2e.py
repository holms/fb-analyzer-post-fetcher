"""
End-to-End test script for the FacebookService class.
This script tests the FacebookService with real API credentials.

To run this test, you need valid Facebook API credentials set in the environment variables:
- FACEBOOK_APP_ID
- FACEBOOK_APP_SECRET
- FACEBOOK_ACCESS_TOKEN
- MAX_PAGES_PER_FETCH (optional, defaults to 10)
- MAX_EVENTS_PER_PAGE (optional, defaults to 100)

Example usage:
    python test_facebook_service_e2e.py
"""
import os
import sys
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Import the FacebookService class
try:
    from app.services.facebook_service import FacebookService
    from app.models import PageCreate, Page
    logger.info("✅ Successfully imported FacebookService")
except ImportError as e:
    logger.error(f"❌ Error importing FacebookService: {e}")
    logger.error("Make sure you're running this script from the correct directory")
    sys.exit(1)

def test_facebook_service():
    """Test the FacebookService class with real API credentials."""
    logger.info("\n=== Testing FacebookService with Real Credentials ===")
    
    # Check if required environment variables are set
    required_vars = [
        "FACEBOOK_APP_ID", 
        "FACEBOOK_APP_SECRET", 
        "FACEBOOK_ACCESS_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the test")
        return False
    
    # Get API credentials from environment variables
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    max_pages = int(os.getenv("MAX_PAGES_PER_FETCH", "10"))
    max_events = int(os.getenv("MAX_EVENTS_PER_PAGE", "100"))
    
    # Print environment variables (without showing full secrets)
    logger.info("Environment Variables:")
    logger.info(f"FACEBOOK_APP_ID: {app_id[:5]}...")
    logger.info(f"FACEBOOK_APP_SECRET: {app_secret[:5]}...")
    logger.info(f"FACEBOOK_ACCESS_TOKEN: {access_token[:5]}...")
    logger.info(f"MAX_PAGES_PER_FETCH: {max_pages}")
    logger.info(f"MAX_EVENTS_PER_PAGE: {max_events}")
    
    try:
        # Initialize the FacebookService
        logger.info("\nInitializing FacebookService...")
        service = FacebookService()
        logger.info("✅ FacebookService initialized successfully")
        logger.info(f"Graph API Base URL: {service.graph_api_base}")
        
        # Create a mock database session
        class MockDB:
            def add(self, obj):
                # Set required fields for the Page model
                obj.id = 1
                obj.created_at = datetime.now()
                obj.updated_at = datetime.now()
            
            def commit(self):
                pass
            
            def refresh(self, obj):
                pass
            
            def query(self, *args, **kwargs):
                return self
            
            def filter(self, *args, **kwargs):
                return self
            
            def first(self):
                return None
        
        mock_db = MockDB()
        
        # Test 1: Add a Facebook page
        logger.info("\nTest 1: Adding a Facebook page...")
        try:
            # Use Korniha Band Facebook page as a test
            test_page_id = "kornihaband"
            
            # Create a page object
            page_create = PageCreate(
                fb_page_id=test_page_id,
                name="Korniha Band",  # Provide a default name
                description="Ukrainian folk metal band",
                page_url="https://www.facebook.com/kornihaband/"
            )
            
            # Call the add_page method
            page = service.add_page(mock_db, page_create)
            logger.info("✅ Successfully added page:")
            logger.info(f"   Page Name: {page.name}")
            logger.info(f"   Page ID: {page.fb_page_id}")
            if hasattr(page, 'description') and page.description:
                logger.info(f"   Description: {page.description[:100]}...")
            if hasattr(page, 'page_url') and page.page_url:
                logger.info(f"   URL: {page.page_url}")
        except Exception as e:
            logger.error(f"❌ Error adding page: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Fetch events from the page
        logger.info("\nTest 2: Fetching events from the page...")
        try:
            # Create a mock page with the needed attributes
            mock_page = MagicMock()
            mock_page.id = 1
            mock_page.fb_page_id = test_page_id
            mock_page.name = "Korniha Band"
            
            # Call the fetch_events method
            events = service.fetch_events(mock_db, mock_page, limit=5)
            
            if events:
                logger.info(f"✅ Successfully fetched {len(events)} events")
                
                for i, event in enumerate(events[:3], 1):  # Show first 3 events
                    logger.info(f"\nEvent {i}:")
                    logger.info(f"   Name: {event.name}")
                    logger.info(f"   ID: {event.fb_event_id}")
                    logger.info(f"   Start Time: {event.start_time}")
                    if event.end_time:
                        logger.info(f"   End Time: {event.end_time}")
                    if hasattr(event, 'location') and event.location:
                        logger.info(f"   Place: {event.location}")
                    logger.info(f"   Attending Count: {event.attending_count}")
                
                if len(events) > 3:
                    logger.info(f"\n... and {len(events) - 3} more events")
            else:
                logger.info("No events found for this page (this might be normal)")
        except Exception as e:
            logger.error(f"❌ Error fetching events: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # All tests passed
        logger.info("\n✅ All FacebookService tests passed successfully")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_token_validity():
    """Check if the Facebook access token is valid."""
    logger.info("\n=== Checking Facebook Access Token Validity ===")
    
    # Check if required environment variables are set
    required_vars = [
        "FACEBOOK_APP_ID", 
        "FACEBOOK_APP_SECRET", 
        "FACEBOOK_ACCESS_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the test")
        return False
    
    # Get API credentials from environment variables
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    try:
        # Import httpx here to avoid dependency on the main service
        import httpx
        
        # Set up Graph API base URL
        graph_api_version = "v17.0"
        graph_api_base = f"https://graph.facebook.com/{graph_api_version}"
        
        # Use app_id|app_secret as access token for debug_token endpoint
        app_access_token = f"{app_id}|{app_secret}"
        url = f"{graph_api_base}/debug_token?input_token={access_token}&access_token={app_access_token}"
        
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            token_info = response.json()
            
        if "data" in token_info:
            if "is_valid" in token_info["data"]:
                if token_info["data"]["is_valid"]:
                    logger.info("✅ Access token is valid")
                    
                    # Check expiration
                    if "expires_at" in token_info["data"]:
                        expires_at = datetime.fromtimestamp(token_info["data"]["expires_at"])
                        logger.info(f"   Token expires at: {expires_at}")
                        
                        # Check if token expires soon (within 7 days)
                        now = datetime.now()
                        days_until_expiry = (expires_at - now).days
                        if days_until_expiry < 7:
                            logger.warning(f"⚠️ Token will expire in {days_until_expiry} days")
                            logger.warning("   Consider generating a new token soon")
                    
                    # Check scopes
                    if "scopes" in token_info["data"]:
                        scopes = token_info["data"]["scopes"]
                        logger.info(f"   Token scopes: {', '.join(scopes)}")
                        
                        # Check for required scopes
                        required_scopes = ["pages_show_list", "page_events"]
                        missing_scopes = [scope for scope in required_scopes if scope not in scopes]
                        if missing_scopes:
                            logger.warning(f"⚠️ Token is missing required scopes: {', '.join(missing_scopes)}")
                            logger.warning("   This may limit functionality")
                    
                    return True
                else:
                    logger.error("❌ Access token is invalid")
                    if "error" in token_info["data"]:
                        error = token_info["data"]["error"]
                        logger.error(f"   Error code: {error.get('code')}")
                        logger.error(f"   Error message: {error.get('message')}")
                    return False
            else:
                logger.error("❌ Could not determine if token is valid")
                logger.error(f"   Response: {token_info}")
                return False
        else:
            logger.error("❌ Unexpected response format")
            logger.error(f"   Response: {token_info}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking token validity: {e}")
        import traceback
        traceback.print_exc()
        return False



if __name__ == "__main__":
    # First check if the token is valid
    token_valid = check_token_validity()
    
    if not token_valid:
        logger.error("\n❌ Facebook access token is invalid or expired")
        logger.error("Please update your FACEBOOK_ACCESS_TOKEN environment variable with a valid token")
        sys.exit(1)
    
    # If token is valid, run the service test
    success = test_facebook_service()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    if success:
        logger.info("✅ FacebookService E2E test PASSED")
        logger.info("The FacebookService is working correctly with real Facebook API credentials")
        sys.exit(0)
    else:
        logger.error("❌ FacebookService E2E test FAILED")
        logger.error("Please check the error messages above")
        sys.exit(1)
