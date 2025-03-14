from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class Group(Base):
    """
    SQLAlchemy model for Facebook groups.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    fb_group_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with posts
    posts = relationship("Post", back_populates="group", cascade="all, delete-orphan")


class Post(Base):
    """
    SQLAlchemy model for Facebook posts.
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    fb_post_id = Column(String(255), unique=True, index=True)
    fb_group_id = Column(Integer, ForeignKey("groups.id"))
    content = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    post_url = Column(String(255), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with group
    group = relationship("Group", back_populates="posts")


class Page(Base):
    """
    SQLAlchemy model for Facebook pages.
    """
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    fb_page_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    page_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with events
    events = relationship("Event", back_populates="page", cascade="all, delete-orphan")


class Event(Base):
    """
    SQLAlchemy model for Facebook events.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    fb_event_id = Column(String(255), unique=True, index=True)
    fb_page_id = Column(Integer, ForeignKey("pages.id"))
    name = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    event_url = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    timezone = Column(String(50), nullable=True)
    is_online = Column(Boolean, default=False)
    attending_count = Column(Integer, default=0)
    interested_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with page
    page = relationship("Page", back_populates="events")
