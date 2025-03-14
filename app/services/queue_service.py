import os
import logging
import json
import redis
from typing import List, Optional

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


class QueueService:
    """
    Service for interacting with Redis queue.
    Uses environment variables for configuration.
    """
    def __init__(self):
        # Get Redis connection parameters from environment variables
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_url = os.getenv("REDIS_URL", f"redis://{self.redis_host}:{self.redis_port}")
        
        # Connect to Redis
        try:
            self.redis = redis.from_url(self.redis_url)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    def queue_events_for_analysis(self, event_ids: List[int]) -> bool:
        """
        Queue events for analysis by the event analyzer service.
        """
        if not self.redis:
            logger.error("Redis connection not available")
            return False
        
        try:
            # Add each event ID to the events_to_analyze queue
            for event_id in event_ids:
                self.redis.lpush("events_to_analyze", event_id)
            
            logger.info(f"Queued {len(event_ids)} events for analysis")
            return True
        except Exception as e:
            logger.error(f"Failed to queue events for analysis: {e}")
            return False
    
    def schedule_page_fetch(self, page_id: int) -> bool:
        """
        Schedule regular fetching of events from a specific Facebook page.
        """
        if not self.redis:
            logger.error("Redis connection not available")
            return False
        
        try:
            # Add page ID to the scheduled_pages set
            self.redis.sadd("scheduled_pages", page_id)
            
            # Store fetch interval in seconds (from environment variable)
            fetch_interval = int(os.getenv("FETCH_INTERVAL", "3600"))  # Default: 1 hour
            
            # Store page fetch configuration
            config = {
                "page_id": page_id,
                "interval": fetch_interval,
                "last_fetch": 0  # Will be updated by the scheduler
            }
            
            self.redis.hset("page_fetch_config", page_id, json.dumps(config))
            
            logger.info(f"Scheduled regular fetching for page {page_id} every {fetch_interval} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule page fetch: {e}")
            return False
    
    def unschedule_page_fetch(self, page_id: int) -> bool:
        """
        Remove a page from the scheduled fetching.
        """
        if not self.redis:
            logger.error("Redis connection not available")
            return False
        
        try:
            # Remove page ID from the scheduled_pages set
            self.redis.srem("scheduled_pages", page_id)
            
            # Remove page fetch configuration
            self.redis.hdel("page_fetch_config", page_id)
            
            logger.info(f"Unscheduled regular fetching for page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unschedule page fetch: {e}")
            return False
    
    def get_scheduled_pages(self) -> List[int]:
        """
        Get list of page IDs that are scheduled for regular fetching.
        """
        if not self.redis:
            logger.error("Redis connection not available")
            return []
        
        try:
            # Get all page IDs from the scheduled_pages set
            page_ids = self.redis.smembers("scheduled_pages")
            return [int(page_id) for page_id in page_ids]
        except Exception as e:
            logger.error(f"Failed to get scheduled pages: {e}")
            return []
    
    # Legacy methods for backward compatibility
    def queue_posts_for_analysis(self, post_ids: List[int]) -> bool:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated post functionality. Please migrate to pages and events.")
        return True
    
    def schedule_group_fetch(self, group_id: int) -> bool:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated group functionality. Please migrate to pages and events.")
        return True
