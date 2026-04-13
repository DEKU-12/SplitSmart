"""
Kroger API client — mirrors lib/kroger.ts but runs server-side.
Handles OAuth token caching, store lookup, and product price search.
"""

import os
import base64
import time
from dataclasses import dataclass
import httpx

KROGER_BASE_URL = "https://api.kroger.com/v1"
CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")

# Token cache (in-memory, per process)
_access_token: str | None = None
_token_expiry: float = 0


@dataclass
class KrogerPrice:
    product_name: str
    price: float | None
    regular_price: float | None
    on_sale: bool
    store_name: str
    savings: float


async def get_access_token() -> str:
    global _access_token, _token_expiry
    if _access_token and time.time() < _token_expiry:
        return _access_token

    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KROGER_BASE_URL}/connect/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials&scope=product.compact",
        )
        data = response.json()

    _access_token = data["access_token"]
    _token_expiry = time.time() + data.get("expires_in", 1800) - 60
    return _access_token


async def get_nearby_store_id(zip_code: str = "20001") -> str | None:
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KROGER_BASE_URL}/locations",
            params={
                "filter.zipCode.near": zip_code,
                "filter.radiusInMiles": 15,
                "filter.limit": 1,
            },
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        data = response.json()
    locations = data.get("data", [])
    return locations[0]["locationId"] if locations else None


async def search_kroger_price(
    item_name: str,
    user_paid_price: float,
    zip_code: str = "20001",
) -> KrogerPrice | None:
    try:
        token = await get_access_token()
        location_id = await get_nearby_store_id(zip_code)
        if not location_id:
            return None

        # Clean search term — same logic as TypeScript version
        words = [
            w for w in item_name.lower().replace("-", " ").split()
            if len(w) > 2 and w.isalpha()
        ]
        search_term = " ".join(words[:3])
        if not search_term:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KROGER_BASE_URL}/products",
                params={
                    "filter.term": search_term,
                    "filter.locationId": location_id,
                    "filter.limit": 1,
                },
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
            data = response.json()

        product = (data.get("data") or [None])[0]
        if not product:
            return None

        price_info = (product.get("items") or [{}])[0].get("price", {})
        promo = price_info.get("promo")
        regular = price_info.get("regular")
        kroger_price = promo or regular

        return KrogerPrice(
            product_name=product.get("description", item_name),
            price=kroger_price,
            regular_price=regular,
            on_sale=bool(promo and regular and promo < regular),
            store_name="Harris Teeter / Kroger",
            savings=round(user_paid_price - kroger_price, 2) if kroger_price else 0,
        )

    except Exception as e:
        print(f"Kroger search error for '{item_name}': {e}")
        return None
