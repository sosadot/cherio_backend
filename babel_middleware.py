# babel_middleware.py
import json
import os
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.datastructures import Headers
from babel import negotiate_locale

class BabelMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        locales_dir: str = "locales",
        default_locale: str = "en",
        supported_locales: list[str] = ["en"],
        domain: str = "messages", # Base filename for json
    ):
        super().__init__(app)
        self.locales_dir = locales_dir
        self.default_locale = default_locale
        self.supported_locales = supported_locales
        self.domain = domain
        # Pre-compile regex for efficiency
        self.lang_code_regex = re.compile(
            r"^/(" + "|".join(re.escape(loc) for loc in supported_locales) + r")(?:/|$)"
        )
        self.translations = self._load_all_translations()
        # Keep initial loading logs
        print(f"[BabelMiddleware] Initialized. Loaded locales: {list(self.translations.keys())}")

    def _load_all_translations(self) -> dict:
        """Loads all JSON translation files into memory."""
        all_translations = {}
        # Keep loading logs
        print(f"[BabelMiddleware] Attempting to load translations from: {self.locales_dir}")
        if not os.path.isdir(self.locales_dir):
             print(f"[BabelMiddleware] ERROR: Locales directory '{self.locales_dir}' not found.")
             return {}

        for locale in self.supported_locales:
            file_path = os.path.join(self.locales_dir, locale, f"{self.domain}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        all_translations[locale] = data
                        print(f"[BabelMiddleware] Successfully loaded translations for locale: '{locale}' (found {len(data)} keys)")
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[BabelMiddleware] ERROR loading translations for locale '{locale}' from {file_path}: {e}") # Keep error log
            else:
                 print(f"[BabelMiddleware] Warning: Translation file not found for locale '{locale}': {file_path}") # Keep warning
        return all_translations


    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        best_locale = self.default_locale
        path_lang = None

        # --- Determine Locale ---
        request_path = request.url.path
        match = self.lang_code_regex.match(request_path)
        if match:
            path_lang = match.group(1)
            best_locale = path_lang
        else:
            headers = Headers(scope=request.scope)
            accept_language = headers.get("accept-language")
            negotiated_locale = negotiate_locale(
                accept_language, self.supported_locales, sep='-'
            )
            if negotiated_locale:
                best_locale = negotiated_locale

        # --- Get Translations for Locale ---
        locale_translations = self.translations.get(best_locale, {}).copy()
        default_translations = self.translations.get(self.default_locale, {}).copy()

        # --- Define gettext function for this specific request ---
        def gettext(key: str, **kwargs) -> str:
            message = locale_translations.get(key, default_translations.get(key, key))
            try:
                return message.format(**kwargs) if kwargs else message
            except KeyError as e:
                # Keep formatting error logs
                print(f"[BabelMiddleware] ERROR: Missing format key '{e}' for message key '{key}'")
                return message
            except Exception as e:
                 print(f"[BabelMiddleware] ERROR during formatting for key '{key}': {e}")
                 return message

        # --- Attach to request state ---
        request.state.gettext = gettext
        request.state.locale = best_locale

        # --- Call next middleware/route ---
        response = await call_next(request)
        return response
