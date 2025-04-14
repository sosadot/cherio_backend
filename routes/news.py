from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import get_db
from datetime import datetime # Import datetime

router = APIRouter()  # ✅ This is enough

class ArticleResponse(BaseModel):
    id: int
    slug: str
    title: str
    short_story: str
    full_story: str
    user_id: int
    image: Optional[str] = None
    created_at: datetime
    username: str
    look: Optional[str] = None
    gender: Optional[str] = None


class ArticleSummary(BaseModel):
    id: int
    slug: str
    title: str
    short_story: str
    full_story: str
    user_id: int
    image: Optional[str] = None
    created_at: datetime
    username: str

@router.get("/", response_model=List[ArticleSummary])
def get_news():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.id, a.slug, a.title, a.short_story,
            a.user_id, a.image, a.created_at, u.username
        FROM website_articles a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    articles = cursor.fetchall()
    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.id, a.slug, a.title, a.short_story, a.full_story, a.image, a.created_at,
            a.user_id, -- Added this line
            u.username, u.look, u.gender
        FROM website_articles a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = %s
    """, (article_id,))
    article = cursor.fetchone()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article