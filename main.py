import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import stripe
from enum import Enum
from babel_middleware import BabelMiddleware
from routes import eye

# Load .env
load_dotenv()

DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en")
supported_locales_str = os.getenv("SUPPORTED_LOCALES_STR", DEFAULT_LOCALE)

# Parse the comma-separated string into a list, stripping whitespace and removing empty entries
SUPPORTED_LOCALES = [
    lang.strip() for lang in supported_locales_str.split(',') if lang.strip()
]
if DEFAULT_LOCALE not in SUPPORTED_LOCALES:
    SUPPORTED_LOCALES.insert(0, DEFAULT_LOCALE) # Add it to the beginning

# Dynamically create Enum members based on the loaded locales
locale_enum_members = {locale: locale for locale in SUPPORTED_LOCALES}
Locale = Enum("Locale", locale_enum_members)

LOCALES_DIR = os.getenv("LOCALES_DIR", "locales")
if not os.path.isdir(LOCALES_DIR):
    # Keep warning about missing locales directory
    print(f"Warning: Locales directory '{LOCALES_DIR}' not found. Translations may not work.")


# Routers are imported after configuration but before app creation usually
from routes import auth, user, news, general, leaderboard, image_proxy

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    print("Warning: STRIPE_SECRET_KEY environment variable not set.")

app = FastAPI(title="Cherio Backend API")

# --- Add Middlewares ---
# Add middleware AFTER app initialization
app.add_middleware(
    BabelMiddleware, # Custom Babel middleware using JSON
    locales_dir=LOCALES_DIR,
    default_locale=DEFAULT_LOCALE,
    supported_locales=SUPPORTED_LOCALES,
    domain="messages" # Base filename for json translation files
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:8081"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], # Ensure 'Accept-Language' is allowed
)
# --- End Middlewares ---


# --- Include Routers with Language Prefix ---
if hasattr(general, 'router'):
    app.include_router(general.router, prefix="/{lang_code}", tags=["General"])
if hasattr(auth, 'router'):
    app.include_router(auth.router, prefix="/{lang_code}/auth", tags=["Auth"])
if hasattr(user, 'router'):
    app.include_router(user.router, prefix="/{lang_code}/user", tags=["User"])
if hasattr(news, 'router'):
    app.include_router(news.router, prefix="/{lang_code}/news", tags=["News"])
if hasattr(leaderboard, 'router'):
    app.include_router(leaderboard.router, prefix="/{lang_code}/user", tags=["leaderboard"])
if hasattr(image_proxy, 'router'):
    app.include_router(image_proxy.router, prefix="/{lang_code}/image-proxy", tags=["Image Proxy"])
if hasattr(eye, 'router'):
    app.include_router(eye.router, prefix="/{lang_code}/eye", tags=["The Eye"])
# if hasattr(shop, 'router'):
#     app.include_router(shop.router, prefix="/{lang_code}/shop", tags=["Shop"])



# --- Uvicorn server execution ---
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 9000))
    reload = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
    # Keep startup info logs
    print(f"Starting server on {host}:{port} with reload={'enabled' if reload else 'disabled'}")
    print(f"Default locale set to: {DEFAULT_LOCALE}")
    print(f"Supported locales loaded from env: {SUPPORTED_LOCALES}") # Updated log
    uvicorn.run(
        "main:app", host=host, port=port, reload=reload,
    )
