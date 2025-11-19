import os
import hashlib
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from database import db, create_document, get_documents

app = FastAPI(title="SaaS Landing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Models (Request/Response)
# -----------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str

class BlogResponse(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    author: str
    published_at: Optional[datetime] = None
    tags: List[str] = []


# -----------------------------
# Helpers
# -----------------------------

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_sample_blog_posts():
    """Seed a few blog posts if none exist yet."""
    count = db["blogpost"].count_documents({}) if db else 0
    if count == 0 and db is not None:
        samples = [
            {
                "title": "Designing With Pastels: A Gentle UI Aesthetic",
                "slug": "designing-with-pastels",
                "excerpt": "How soft color palettes can increase trust and readability in fintech apps.",
                "content": "<p>Pastels bring calm to complex financial interfaces...</p>",
                "author": "Team",
                "tags": ["design", "ux"],
                "published_at": datetime.utcnow(),
            },
            {
                "title": "Pricing Psychology for SaaS",
                "slug": "pricing-psychology-saas",
                "excerpt": "Anchoring, decoys and how to present value tiers.",
                "content": "<p>Great pricing pages tell a story of value...</p>",
                "author": "Team",
                "tags": ["growth", "pricing"],
                "published_at": datetime.utcnow(),
            },
            {
                "title": "Frictionless Onboarding",
                "slug": "frictionless-onboarding",
                "excerpt": "Best practices for sign-up and authentication flows.",
                "content": "<p>Every extra field reduces conversions...</p>",
                "author": "Team",
                "tags": ["product", "auth"],
                "published_at": datetime.utcnow(),
            },
        ]
        for post in samples:
            # Use create_document helper to add timestamps
            create_document("blogpost", post)


# -----------------------------
# Core Routes
# -----------------------------
@app.get("/")
def root():
    return {"message": "SaaS Landing API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# -----------------------------
# Pricing
# -----------------------------
@app.get("/api/pricing")
def get_pricing():
    return {
        "plans": [
            {
                "name": "Free",
                "price": 0,
                "period": "mo",
                "features": ["Basic analytics", "Community support", "1 project"],
                "cta": "Get started",
                "highlight": False,
            },
            {
                "name": "Pro",
                "price": 19,
                "period": "mo",
                "features": ["Unlimited projects", "Email support", "Custom domains"],
                "cta": "Start Pro",
                "highlight": True,
            },
            {
                "name": "Business",
                "price": 49,
                "period": "mo",
                "features": ["Team seats", "SLA support", "SSO"],
                "cta": "Contact sales",
                "highlight": False,
            },
        ]
    }


# -----------------------------
# Auth (simple demo)
# -----------------------------
@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    # Ensure unique email
    existing = db["user"].find_one({"email": payload.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": sha256(payload.password),
        "plan": "free",
        "is_active": True,
    }
    user_id = create_document("user", user_doc)
    return {"id": user_id, "name": payload.name, "email": payload.email, "plan": "free"}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = db["user"].find_one({"email": payload.email}) if db else None
    if not user or user.get("password_hash") != sha256(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": str(user.get("_id")), "name": user.get("name"), "email": user.get("email"), "plan": user.get("plan", "free")}


# -----------------------------
# Blog
# -----------------------------
@app.get("/api/blog")
def list_blog(limit: int = 6):
    ensure_sample_blog_posts()
    docs = get_documents("blogpost", {}, limit)
    items = []
    for d in docs:
        items.append({
            "title": d.get("title"),
            "slug": d.get("slug"),
            "excerpt": d.get("excerpt"),
            "author": d.get("author", "Team"),
            "published_at": d.get("published_at"),
            "tags": d.get("tags", []),
        })
    return {"posts": items}


@app.get("/api/blog/{slug}")
def get_blog(slug: str):
    doc = db["blogpost"].find_one({"slug": slug}) if db else None
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "title": doc.get("title"),
        "slug": doc.get("slug"),
        "excerpt": doc.get("excerpt"),
        "content": doc.get("content"),
        "author": doc.get("author", "Team"),
        "published_at": doc.get("published_at"),
        "tags": doc.get("tags", []),
    }


# -----------------------------
# Contact
# -----------------------------
@app.post("/api/contact")
def contact(payload: ContactRequest):
    doc = {
        "name": payload.name,
        "email": payload.email,
        "message": payload.message,
        "status": "new",
    }
    message_id = create_document("contactmessage", doc)
    return {"id": message_id, "status": "received"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
