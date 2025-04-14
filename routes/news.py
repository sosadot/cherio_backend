from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from db import get_db

router = APIRouter()  # ✅ This is enough

class Article(BaseModel):
    id: int
    slug: str
    title: str
    short_story: str
    full_story: str
    user_id: int
    image: str
    created_at: str
    username: str
    
@router.get("/")
def get_news():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.id,
            a.slug,
            a.title,
            a.short_story,
            a.full_story,
            a.user_id,
            a.image,
            a.created_at,
            u.username
        FROM website_articles a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT 10
    """)

    articles = cursor.fetchall()
    return articles


@router.get("/{article_id}")
def get_article(article_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.id, a.slug, a.title, a.short_story, a.full_story, a.image, a.created_at,
            u.username, u.look, u.gender
        FROM website_articles a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = %s
    """, (article_id,))

    article = cursor.fetchone()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article