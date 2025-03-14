from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import logging

from app.models import GroupCreate, Group, PostResponse, PageCreate, Page, EventResponse
from app.database import get_db, engine
from app.schemas import Base
from app.services.facebook_service import FacebookService
from app.services.queue_service import QueueService

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FB Analyzer Event Fetcher",
    description="Service for fetching events from Facebook pages",
    version="0.2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
facebook_service = FacebookService()
queue_service = QueueService()


@app.get("/")
async def root():
    return {"message": "FB Analyzer Event Fetcher Service"}


@app.get("/health")
async def health_check():
    # Log environment variables (without sensitive values)
    logger.info(f"DB_HOST: {os.getenv('DB_HOST', 'Not set')}")
    logger.info(f"REDIS_HOST: {os.getenv('REDIS_HOST', 'Not set')}")
    logger.info(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'Not set')}")
    logger.info(f"FETCH_INTERVAL: {os.getenv('FETCH_INTERVAL', 'Not set')}")
    
    # Check if Facebook credentials are available
    has_facebook_credentials = bool(os.getenv("FACEBOOK_ACCESS_TOKEN"))
    
    return {
        "status": "healthy",
        "version": "0.2.0",
        "facebook_credentials": "available" if has_facebook_credentials else "missing"
    }


# New endpoints for Facebook pages
@app.post("/pages/", response_model=Page)
async def create_page(page: PageCreate, db=Depends(get_db)):
    """
    Add a new Facebook page to monitor.
    """
    return facebook_service.add_page(db, page)


@app.get("/pages/", response_model=List[Page])
async def read_pages(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    """
    Retrieve all monitored Facebook pages.
    """
    return facebook_service.get_pages(db, skip=skip, limit=limit)


@app.get("/pages/{page_id}", response_model=Page)
async def read_page(page_id: int, db=Depends(get_db)):
    """
    Retrieve a specific Facebook page by ID.
    """
    db_page = facebook_service.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page


@app.delete("/pages/{page_id}")
async def delete_page(page_id: int, db=Depends(get_db)):
    """
    Delete a Facebook page from monitoring.
    """
    success = facebook_service.delete_page(db, page_id=page_id)
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page deleted successfully"}


@app.post("/pages/{page_id}/fetch", response_model=List[EventResponse])
async def fetch_events(
    page_id: int, 
    background_tasks: BackgroundTasks,
    limit: Optional[int] = 10, 
    db=Depends(get_db)
):
    """
    Fetch events from a specific Facebook page.
    The events will be stored in the database and queued for analysis.
    """
    db_page = facebook_service.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Fetch events synchronously for immediate response
    events = facebook_service.fetch_events(db, db_page, limit=limit)
    
    # Queue the events for analysis in the background
    background_tasks.add_task(
        queue_service.queue_events_for_analysis, 
        [event.id for event in events]
    )
    
    return events


@app.post("/pages/{page_id}/schedule")
async def schedule_page_fetch(page_id: int, db=Depends(get_db)):
    """
    Schedule regular fetching of events from a specific Facebook page.
    """
    db_page = facebook_service.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    
    success = queue_service.schedule_page_fetch(page_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to schedule fetch")
    
    return {"message": f"Scheduled regular fetching for page {page_id}"}


@app.delete("/pages/{page_id}/schedule")
async def unschedule_page_fetch(page_id: int, db=Depends(get_db)):
    """
    Remove a page from scheduled fetching.
    """
    db_page = facebook_service.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    
    success = queue_service.unschedule_page_fetch(page_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unschedule fetch")
    
    return {"message": f"Unscheduled regular fetching for page {page_id}"}


@app.get("/events/", response_model=List[EventResponse])
async def read_events(
    page_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100, 
    db=Depends(get_db)
):
    """
    Retrieve events, optionally filtered by page.
    """
    return facebook_service.get_events(db, page_id=page_id, skip=skip, limit=limit)


@app.get("/events/{event_id}", response_model=EventResponse)
async def read_event(event_id: int, db=Depends(get_db)):
    """
    Retrieve a specific event by ID.
    """
    event = facebook_service.get_event(db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# Legacy endpoints for backward compatibility
@app.post("/groups/", response_model=Group)
async def create_group(group: GroupCreate, db=Depends(get_db)):
    """
    [DEPRECATED] Add a new Facebook group to monitor.
    This endpoint is maintained for backward compatibility.
    Please use /pages/ endpoints instead.
    """
    logger.warning("Using deprecated group endpoint. Please migrate to pages.")
    return facebook_service.add_group(db, group)


@app.get("/groups/", response_model=List[Group])
async def read_groups(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    """
    [DEPRECATED] Retrieve all monitored Facebook groups.
    This endpoint is maintained for backward compatibility.
    Please use /pages/ endpoints instead.
    """
    logger.warning("Using deprecated group endpoint. Please migrate to pages.")
    return facebook_service.get_groups(db, skip=skip, limit=limit)


@app.get("/groups/{group_id}", response_model=Group)
async def read_group(group_id: int, db=Depends(get_db)):
    """
    [DEPRECATED] Retrieve a specific Facebook group by ID.
    This endpoint is maintained for backward compatibility.
    Please use /pages/ endpoints instead.
    """
    logger.warning("Using deprecated group endpoint. Please migrate to pages.")
    db_group = facebook_service.get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@app.delete("/groups/{group_id}")
async def delete_group(group_id: int, db=Depends(get_db)):
    """
    [DEPRECATED] Delete a Facebook group from monitoring.
    This endpoint is maintained for backward compatibility.
    Please use /pages/ endpoints instead.
    """
    logger.warning("Using deprecated group endpoint. Please migrate to pages.")
    success = facebook_service.delete_group(db, group_id=group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}


@app.post("/groups/{group_id}/fetch", response_model=List[PostResponse])
async def fetch_posts(
    group_id: int, 
    background_tasks: BackgroundTasks,
    limit: Optional[int] = 10, 
    db=Depends(get_db)
):
    """
    [DEPRECATED] Fetch posts from a specific Facebook group.
    This endpoint is maintained for backward compatibility.
    Please use /pages/{page_id}/fetch for events instead.
    """
    logger.warning("Using deprecated post endpoint. Please migrate to events.")
    db_group = facebook_service.get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Return empty list as this functionality is deprecated
    return []


@app.post("/groups/{group_id}/schedule")
async def schedule_fetch(group_id: int, db=Depends(get_db)):
    """
    [DEPRECATED] Schedule regular fetching of posts from a specific Facebook group.
    This endpoint is maintained for backward compatibility.
    Please use /pages/{page_id}/schedule for events instead.
    """
    logger.warning("Using deprecated group endpoint. Please migrate to pages.")
    db_group = facebook_service.get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "This functionality is deprecated. Please use /pages/{page_id}/schedule instead."}


@app.get("/posts/", response_model=List[PostResponse])
async def read_posts(
    group_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100, 
    db=Depends(get_db)
):
    """
    [DEPRECATED] Retrieve posts, optionally filtered by group.
    This endpoint is maintained for backward compatibility.
    Please use /events/ endpoints instead.
    """
    logger.warning("Using deprecated post endpoint. Please migrate to events.")
    return []


@app.get("/posts/{post_id}", response_model=PostResponse)
async def read_post(post_id: int, db=Depends(get_db)):
    """
    [DEPRECATED] Retrieve a specific post by ID.
    This endpoint is maintained for backward compatibility.
    Please use /events/{event_id} instead.
    """
    logger.warning("Using deprecated post endpoint. Please migrate to events.")
    raise HTTPException(status_code=404, detail="Post not found")
