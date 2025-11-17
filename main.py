import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone

from database import create_document, get_documents, db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Schemas =====
class BlogPost(BaseModel):
    title: str = Field(..., max_length=180)
    slug: str = Field(..., max_length=200)
    excerpt: Optional[str] = Field(None, max_length=300)
    content: str
    cover_image: Optional[str] = None
    tags: List[str] = []
    lang: str = Field("en", description="en or fi")


class PartnerLead(BaseModel):
    venue_name: str
    contact_email: EmailStr
    city: Optional[str] = None
    notes: Optional[str] = None
    source: str = "website"


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str
    topic: Optional[str] = None


# ===== Health =====
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ===== Blog CMS (simple) =====
@app.get("/api/blog", response_model=List[BlogPost])
def list_blog_posts(limit: int = 10, lang: Optional[str] = None):
    if db is None:
        return []
    flt = {}
    if lang:
        flt["lang"] = lang
    docs = get_documents("blogpost", flt, limit)
    # Convert ObjectId and timestamps safely
    results: List[BlogPost] = []
    for d in docs:
        try:
            results.append(BlogPost(**{
                "title": d.get("title", ""),
                "slug": d.get("slug", ""),
                "excerpt": d.get("excerpt"),
                "content": d.get("content", ""),
                "cover_image": d.get("cover_image"),
                "tags": d.get("tags", []),
                "lang": d.get("lang", "en"),
            }))
        except Exception:
            continue
    return results


@app.post("/api/blog", status_code=201)
def create_blog_post(post: BlogPost):
    try:
        _id = create_document("blogpost", post)
        return {"id": _id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Partner Leads =====
@app.post("/api/partners/leads", status_code=201)
def create_partner_lead(lead: PartnerLead):
    try:
        _id = create_document("partnerlead", lead)
        return {"id": _id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Contact Messages =====
@app.post("/api/contact/messages", status_code=201)
def create_contact_message(msg: ContactMessage):
    try:
        _id = create_document("contactmessage", msg)
        return {"id": _id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
