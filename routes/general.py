# routes/general.py
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import stripe # Assuming stripe is configured in main.py

router = APIRouter()

# --- Pydantic Models ---
class CreateCheckoutSessionRequest(BaseModel):
    price_id: str

# --- Endpoints ---

@router.post("/create-checkout-session", tags=["Payments"])
async def create_checkout_session(request: Request):
    """Creates a Stripe Checkout session."""
    # Access translator via request.state if needed for errors
    _ = request.state.gettext
    req_data: CreateCheckoutSessionRequest = await request.json()

    try:
        success_url = os.getenv("SUCCESS_URL", "http://localhost:8081/success?session_id={CHECKOUT_SESSION_ID}")
        cancel_url = os.getenv("CANCEL_URL", "http://localhost:8081/cancel")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": req_data.price_id, "quantity": 1}],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"id": checkout_session.id}
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        # message = _("Payment processing error: {user_message}", user_message=e.user_message)
        raise HTTPException(status_code=400, detail=f"Payment processing error: {e.user_message}")
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        # message = _("Internal server error creating checkout session.")
        raise HTTPException(status_code=500, detail="Internal server error creating checkout session.")

@router.get("/", tags=["Root"]) # Path relative to prefix
def read_root(request: Request):
    """Root endpoint."""
    # Access translator via request.state if needed
    _ = request.state.gettext
    # message = _("Welcome to the Cherio API")
    return {"message": "Welcome to the Cherio API"}

