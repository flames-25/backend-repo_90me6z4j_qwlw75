import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Friends Memory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MemoryIn(BaseModel):
    author_name: str
    message: str
    photo_url: Optional[str] = None
    tags: Optional[List[str]] = None

class MemoryOut(MemoryIn):
    id: str

@app.get("/")
def read_root():
    return {"message": "Friends Memories Backend Ready"}

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

@app.post("/api/memories", response_model=dict)
def add_memory(payload: MemoryIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        inserted_id = create_document("memory", payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories", response_model=List[MemoryOut])
def list_memories(tag: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        filter_dict = {"tags": {"$in": [tag]}} if tag else {}
        docs = get_documents("memory", filter_dict=filter_dict, limit=100)
        results: List[MemoryOut] = []
        for d in docs:
            results.append(MemoryOut(
                id=str(d.get("_id")),
                author_name=d.get("author_name", ""),
                message=d.get("message", ""),
                photo_url=d.get("photo_url"),
                tags=d.get("tags")
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
