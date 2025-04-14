from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/shop")
async def get_shop_items():
    # Dummy shop items
    items = [
        {"id": 1, "name": "VIP Membership", "price": 4.99, "currency": "USD"},
        {"id": 2, "name": "Diamonds Pack", "price": 9.99, "currency": "USD"},
        {"id": 3, "name": "Pixel Hat", "price": 2.49, "currency": "USD"}
    ]
    return JSONResponse(content={"items": items})
