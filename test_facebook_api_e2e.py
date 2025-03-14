"""
End-to-End test script for testing Facebook API connection.
This script makes actual API calls to the Facebook Graph API.

To run this test, you need valid Facebook API credentials set in the environment variables:
- FACEBOOK_APP_ID
- FACEBOOK_APP_SECRET
- FACEBOOK_ACCESS_TOKEN

Example usage:
    python test_facebook_api_e2e.py
"""
import os
import sys
import json
import httpx
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_facebook_api_connection():
    """Test direct connection to Facebook Graph API."""
    logger.info("=== Testing Direct Connection to Facebook Graph API ===")
    
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
    
    # Print environment variables (without showing full secrets)
    logger.info("Environment Variables:")
    logger.info(f"FACEBOOK_APP_ID: {app_id[:5]}...")
    logger.info(f"FACEBOOK_APP_SECRET: {app_secret[:5]}...")
    logger.info(f"FACEBOOK_ACCESS_TOKEN: {access_token[:5]}...")
    
    # Set up Graph API base URL
    graph_api_version = "v17.0"
    graph_api_base = f"https://graph.facebook.com/{graph_api_version}"
    logger.info(f"Graph API Base URL: {graph_api_base}")
    
    # Test 1: Verify access token
    logger.info("\nTest 1: Verifying access token...")
    try:
        # For debugging, let's try to use app_id|app_secret as access token for debug_token endpoint
        app_access_token = f"{app_id}|{app_secret}"
        url = f"{graph_api_base}/debug_token?input_token={access_token}&access_token={app_access_token}"
        
        logger.info(f"Making request to: {url.replace(app_access_token, 'APP_ID|APP_SECRET')}")
        
        with httpx.Client() as client:
            response = client.get(url)
            
            # Print response details for debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Try to get JSON response even if status code is not 200
            try:
                response_data = response.json()
                logger.info(f"Response body: {json.dumps(response_data, indent=2)}")
            except Exception as e:
                logger.info(f"Could not parse response as JSON: {e}")
                logger.info(f"Response text: {response.text[:500]}...")
            
            # Now raise for status after logging
            response.raise_for_status()
            token_info = response.json()
            
        if "data" in token_info and "is_valid" in token_info["data"]:
            if token_info["data"]["is_valid"]:
                logger.info("✅ Access token is valid")
                if "expires_at" in token_info["data"]:
                    expires_at = datetime.fromtimestamp(token_info["data"]["expires_at"])
                    logger.info(f"   Token expires at: {expires_at}")
                logger.info(f"   App ID: {token_info['data'].get('app_id', 'N/A')}")
                logger.info(f"   User ID: {token_info['data'].get('user_id', 'N/A')}")
            else:
                logger.error("❌ Access token is invalid")
                return False
        else:
            logger.error("❌ Unexpected response format")
            logger.error(f"Response: {token_info}")
            return False
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error occurred while verifying token: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error occurred while verifying token: {e}")
        return False
    
    # Test 2: Get Facebook Page info
    logger.info("\nTest 2: Getting Facebook Page info...")
    try:
        # Use Facebook's Meta page as a test
        test_page_id = "meta"
        url = f"{graph_api_base}/{test_page_id}?fields=name,about,description,fan_count&access_token={access_token}"
        
        logger.info(f"Making request to: {url.replace(access_token, 'ACCESS_TOKEN')}")
        
        with httpx.Client() as client:
            response = client.get(url)
            
            # Print response details for debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Try to get JSON response even if status code is not 200
            try:
                response_data = response.json()
                logger.info(f"Response body: {json.dumps(response_data, indent=2)}")
            except Exception as e:
                logger.info(f"Could not parse response as JSON: {e}")
                logger.info(f"Response text: {response.text[:500]}...")
            
            # Now raise for status after logging
            response.raise_for_status()
            page_info = response.json()
        
        logger.info("✅ Successfully retrieved page info:")
        logger.info(f"   Page Name: {page_info.get('name', 'N/A')}")
        logger.info(f"   Page ID: {page_info.get('id', 'N/A')}")
        logger.info(f"   Fan Count: {page_info.get('fan_count', 'N/A')}")
        if "about" in page_info:
            logger.info(f"   About: {page_info['about'][:100]}...")
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error occurred while getting page info: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error occurred while getting page info: {e}")
        return False
    
    # Test 3: Get Facebook Page events
    logger.info("\nTest 3: Getting Facebook Page events...")
    try:
        # Use Facebook's Meta page as a test
        test_page_id = "meta"
        fields = "id,name,description,start_time,end_time,place,is_online,attending_count,interested_count"
        url = f"{graph_api_base}/{test_page_id}/events?fields={fields}&limit=5&access_token={access_token}"
        
        logger.info(f"Making request to: {url.replace(access_token, 'ACCESS_TOKEN')}")
        
        with httpx.Client() as client:
            response = client.get(url)
            
            # Print response details for debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Try to get JSON response even if status code is not 200
            try:
                response_data = response.json()
                logger.info(f"Response body: {json.dumps(response_data, indent=2)}")
            except Exception as e:
                logger.info(f"Could not parse response as JSON: {e}")
                logger.info(f"Response text: {response.text[:500]}...")
            
            # Now raise for status after logging
            response.raise_for_status()
            events_data = response.json()
        
        if "data" in events_data:
            events = events_data["data"]
            logger.info(f"✅ Successfully retrieved {len(events)} events")
            
            for i, event in enumerate(events[:3], 1):  # Show first 3 events
                logger.info(f"\nEvent {i}:")
                logger.info(f"   Name: {event.get('name', 'N/A')}")
                logger.info(f"   ID: {event.get('id', 'N/A')}")
                logger.info(f"   Start Time: {event.get('start_time', 'N/A')}")
                if "end_time" in event:
                    logger.info(f"   End Time: {event.get('end_time')}")
                if "place" in event:
                    place_name = event["place"].get("name", "N/A")
                    logger.info(f"   Place: {place_name}")
                logger.info(f"   Attending Count: {event.get('attending_count', 'N/A')}")
            
            if len(events) > 3:
                logger.info(f"\n... and {len(events) - 3} more events")
            elif len(events) == 0:
                logger.info("No events found for this page (this might be normal)")
        else:
            logger.info("No events data returned (this might be normal)")
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error occurred while getting events: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error occurred while getting events: {e}")
        return False
    
    # All tests passed
    logger.info("\n✅ All Facebook API connection tests passed successfully")
    return True



if __name__ == "__main__":
    # Run the test
    logger.info("Running Facebook API E2E tests...")
    success = test_facebook_api_connection()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    if success:
        logger.info("✅ Facebook API connection test PASSED")
        logger.info("The connection to the Facebook Graph API is working correctly")
        sys.exit(0)
    else:
        logger.error("❌ Facebook API connection test FAILED")
        logger.error("Please check the error messages above and verify your API credentials")
        logger.error("Common issues:")
        logger.error("1. Access token may be expired - try generating a new one")
        logger.error("2. App may not have the required permissions")
        logger.error("3. Rate limiting may be in effect - try again later")
        sys.exit(1)
