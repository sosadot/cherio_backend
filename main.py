import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import stripe
from routes import auth, user, news, leaderboard

# Load env
load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(news.router, prefix="/news", tags=["News"])  # ✅ Add prefix
app.include_router(leaderboard.router, prefix="/user", tags=["leaderboard"])  # ✅ Add prefix

class CreateCheckoutSessionRequest(BaseModel):
    price_id: str

@app.post("/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutSessionRequest):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": request.price_id,
                "quantity": 1,
            }],
            mode="payment",
            success_url=os.getenv("SUCCESS_URL", "http://localhost:8081/success"),
            cancel_url=os.getenv("CANCEL_URL", "http://localhost:8081/cancel"),
        )
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)