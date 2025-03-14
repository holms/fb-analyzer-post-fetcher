import os
import logging
import json
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas import Group as GroupModel, Post as PostModel, Page as PageModel, Event as EventModel
from app.models import GroupCreate, Group, PostCreate, PostResponse, PageCreate, Page, EventCreate, EventResponse

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


class FacebookService:
    """
    Service for interacting with the Facebook Graph API.
    Uses environment variables for configuration.
    """
    def __init__(self):
        # Get Facebook API credentials from environment variables
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        # Configure Facebook API client
        if not self.app_id or not self.app_secret:
            logger.warning("Facebook app credentials not provided. Some functionality may be limited.")
            
        if not self.access_token:
            logger.warning("Facebook access token not provided. Some functionality may be limited.")
        
        # Base URL for Graph API requests with access token
        self.graph_api_version = "v17.0"
        self.graph_api_base = f"https://graph.facebook.com/{self.graph_api_version}"
        
        # Configure service settings from environment variables
        self.max_pages_per_fetch = int(os.getenv("MAX_PAGES_PER_FETCH", "10"))
        self.max_events_per_page = int(os.getenv("MAX_EVENTS_PER_PAGE", "100"))
    
    # Page-related methods
    def add_page(self, db: Session, page: PageCreate) -> Page:
        """
        Add a new Facebook page to monitor.
        """
        # Check if page already exists
        existing_page = db.query(PageModel).filter(PageModel.fb_page_id == page.fb_page_id).first()
        if existing_page:
            return Page.from_orm(existing_page)
        
        # Try to get page info from Facebook
        try:
            url = f"{self.graph_api_base}/{page.fb_page_id}?fields=name,description,link&access_token={self.access_token}"
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                page_info = response.json()
            
            # Update page data with info from Facebook
            if not page.name and "name" in page_info:
                page.name = page_info["name"]
            if not page.description and "description" in page_info:
                page.description = page_info["description"]
            if not page.page_url and "link" in page_info:
                page.page_url = page_info["link"]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch page info from Facebook: {e}")
            # Continue with provided data
        
        # Create new page in database
        db_page = PageModel(
            fb_page_id=page.fb_page_id,
            name=page.name,
            description=page.description,
            page_url=str(page.page_url) if page.page_url else None,
            is_active=True
        )
        
        db.add(db_page)
        db.commit()
        db.refresh(db_page)
        
        return Page.from_orm(db_page)
    
    def get_pages(self, db: Session, skip: int = 0, limit: int = 100) -> List[Page]:
        """
        Retrieve all monitored Facebook pages.
        """
        db_pages = db.query(PageModel).offset(skip).limit(limit).all()
        return [Page.from_orm(page) for page in db_pages]
    
    def get_page(self, db: Session, page_id: int) -> Optional[Page]:
        """
        Retrieve a specific Facebook page by ID.
        """
        db_page = db.query(PageModel).filter(PageModel.id == page_id).first()
        if db_page:
            return Page.from_orm(db_page)
        return None
    
    def delete_page(self, db: Session, page_id: int) -> bool:
        """
        Delete a Facebook page from monitoring.
        """
        db_page = db.query(PageModel).filter(PageModel.id == page_id).first()
        if not db_page:
            return False
        
        db.delete(db_page)
        db.commit()
        return True
    
    # Event-related methods
    def fetch_events(self, db: Session, db_page: PageModel, limit: int = 10) -> List[EventResponse]:
        """
        Fetch events from a specific Facebook page.
        """
        events = []
        
        try:
            # Get events from Facebook using the Graph API
            fields = "id,name,description,start_time,end_time,place,is_online,attending_count,interested_count"
            url = f"{self.graph_api_base}/{db_page.fb_page_id}/events?fields={fields}&limit={min(limit, self.max_events_per_page)}&access_token={self.access_token}"
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                event_data = response.json()
            
            # Process each event
            for event in event_data.get("data", []):
                # Extract event details
                fb_event_id = event.get("id")
                name = event.get("name", "Unnamed Event")
                description = event.get("description")
                start_time_str = event.get("start_time")
                end_time_str = event.get("end_time")
                is_online = event.get("is_online", False)
                attending_count = event.get("attending_count", 0)
                interested_count = event.get("interested_count", 0)
                
                # Parse dates
                start_time = None
                end_time = None
                try:
                    if start_time_str:
                        # Handle various date formats from Facebook API
                        # Format 1: 2025-03-15T16:00:00+0200 (missing colon in timezone)
                        # Format 2: 2025-03-15T16:00:00Z (UTC timezone)
                        if start_time_str.endswith('Z'):
                            start_time_str = start_time_str.replace("Z", "+00:00")
                        elif '+' in start_time_str and ':' not in start_time_str[-5:]:
                            # Insert colon in timezone: +0200 -> +02:00
                            tz_part = start_time_str[-5:]
                            formatted_tz = f"{tz_part[:3]}:{tz_part[3:]}"
                            start_time_str = start_time_str[:-5] + formatted_tz
                        
                        start_time = datetime.fromisoformat(start_time_str)
                        
                    if end_time_str:
                        # Apply the same formatting to end_time
                        if end_time_str.endswith('Z'):
                            end_time_str = end_time_str.replace("Z", "+00:00")
                        elif '+' in end_time_str and ':' not in end_time_str[-5:]:
                            tz_part = end_time_str[-5:]
                            formatted_tz = f"{tz_part[:3]}:{tz_part[3:]}"
                            end_time_str = end_time_str[:-5] + formatted_tz
                            
                        end_time = datetime.fromisoformat(end_time_str)
                except ValueError as e:
                    logger.warning(f"Failed to parse event time: {e} (value: {start_time_str})")
                
                # Extract location
                location = None
                if "place" in event and "name" in event["place"]:
                    location = event["place"]["name"]
                
                # Create event URL
                event_url = f"https://facebook.com/events/{fb_event_id}"
                
                # Check if event already exists
                db_event = db.query(EventModel).filter(EventModel.fb_event_id == fb_event_id).first()
                
                if not db_event:
                    # Create new event
                    db_event = EventModel(
                        fb_event_id=fb_event_id,
                        fb_page_id=db_page.id,
                        name=name,
                        description=description,
                        event_url=event_url,
                        location=location,
                        start_time=start_time,
                        end_time=end_time,
                        is_online=is_online,
                        attending_count=attending_count,
                        interested_count=interested_count
                    )
                    db.add(db_event)
                else:
                    # Update existing event
                    db_event.name = name
                    db_event.description = description
                    db_event.event_url = event_url
                    db_event.location = location
                    db_event.start_time = start_time
                    db_event.end_time = end_time
                    db_event.is_online = is_online
                    db_event.attending_count = attending_count
                    db_event.interested_count = interested_count
                
                db.commit()
                db.refresh(db_event)
                
                events.append(EventResponse.from_orm(db_event))
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch events from Facebook: {e}")
        
        return events
    
    def get_events(self, db: Session, page_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[EventResponse]:
        """
        Retrieve events, optionally filtered by page.
        """
        query = db.query(EventModel)
        
        if page_id:
            query = query.filter(EventModel.fb_page_id == page_id)
        
        db_events = query.offset(skip).limit(limit).all()
        return [EventResponse.from_orm(event) for event in db_events]
    
    def get_event(self, db: Session, event_id: int) -> Optional[EventResponse]:
        """
        Retrieve a specific event by ID.
        """
        db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
        if db_event:
            return EventResponse.from_orm(db_event)
        return None
    
    # Legacy methods for backward compatibility
    def add_group(self, db: Session, group: GroupCreate) -> Group:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated group functionality. Please migrate to pages and events.")
        existing_group = db.query(GroupModel).filter(GroupModel.fb_group_id == group.fb_group_id).first()
        if existing_group:
            return Group.from_orm(existing_group)
        
        db_group = GroupModel(
            fb_group_id=group.fb_group_id,
            name=group.name,
            description=group.description
        )
        
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        
        return Group.from_orm(db_group)
    
    def get_groups(self, db: Session, skip: int = 0, limit: int = 100) -> List[Group]:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated group functionality. Please migrate to pages and events.")
        db_groups = db.query(GroupModel).offset(skip).limit(limit).all()
        return [Group.from_orm(group) for group in db_groups]
    
    def get_group(self, db: Session, group_id: int) -> Optional[Group]:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated group functionality. Please migrate to pages and events.")
        db_group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
        if db_group:
            return Group.from_orm(db_group)
        return None
    
    def delete_group(self, db: Session, group_id: int) -> bool:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated group functionality. Please migrate to pages and events.")
        db_group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
        if not db_group:
            return False
        
        db.delete(db_group)
        db.commit()
        return True
    
    def fetch_posts(self, db: Session, db_group: GroupModel, limit: int = 10) -> List[PostResponse]:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated post functionality. Please migrate to pages and events.")
        # Return empty list as this functionality is deprecated
        return []
    
    def get_posts(self, db: Session, group_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[PostResponse]:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated post functionality. Please migrate to pages and events.")
        # Return empty list as this functionality is deprecated
        return []
    
    def get_post(self, db: Session, post_id: int) -> Optional[PostResponse]:
        """
        Legacy method for backward compatibility.
        """
        logger.warning("Using deprecated post functionality. Please migrate to pages and events.")
        return None
