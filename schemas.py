"""
Database Schemas for the SaaS demo

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., User -> "user").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """Auth users collection"""
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    password_hash: str = Field(..., description="SHA256 password hash")
    plan: str = Field("free", description="Subscription plan: free, pro, business")
    is_active: bool = Field(True, description="Whether user is active")

class BlogPost(BaseModel):
    """Marketing blog posts"""
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    published_at: Optional[datetime] = None

class ContactMessage(BaseModel):
    """Contact form submissions"""
    name: str
    email: EmailStr
    message: str
    status: str = Field("new", description="new | read | replied")
