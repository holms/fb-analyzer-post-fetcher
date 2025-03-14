from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


# Original Group models (kept for backward compatibility)
class GroupBase(BaseModel):
    fb_group_id: str
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Original Post models (kept for backward compatibility)
class PostBase(BaseModel):
    fb_post_id: str
    content: Optional[str] = None
    author: Optional[str] = None
    post_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    likes_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    shares_count: Optional[int] = 0


class PostCreate(PostBase):
    fb_group_id: int


class PostResponse(PostBase):
    id: int
    fb_group_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# New Page models for Facebook pages
class PageBase(BaseModel):
    fb_page_id: str
    name: str
    description: Optional[str] = None
    page_url: Optional[HttpUrl] = None


class PageCreate(PageBase):
    pass


class Page(PageBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# New Event models for Facebook events
class EventBase(BaseModel):
    fb_event_id: str
    name: str
    description: Optional[str] = None
    event_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    is_online: Optional[bool] = False


class EventCreate(EventBase):
    fb_page_id: int


class EventResponse(EventBase):
    id: int
    fb_page_id: int
    attending_count: int
    interested_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
