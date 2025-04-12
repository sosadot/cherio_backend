from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Article(BaseModel):
    id: int
    slug: str
    title: str
    short_story: str
    full_story: str
    user_id: int
    image: str
    created_at: str

# ✅ Dummy data for testing
@router.get("/", response_model=List[Article])
def get_articles():
    return [
        {
            "id": 1,
            "slug": "test-article",
            "title": "Test Article",
            "short_story": "This is a test short story.",
            "full_story": "This is the full content of the article.",
            "user_id": 1,
            "image": "/assets/images/articles/test.png",
            "created_at": "2024-01-01 00:00:00",
        }
    ]
