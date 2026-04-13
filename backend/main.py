"""
SplitSmart Python Backend — FastAPI
Runs on http://localhost:8000

Routes:
  POST /ocr/scan-receipt      — receipt image → extracted items + total
  POST /categorize             — item names → category map
  POST /compare-prices         — categorized cart → store rankings + per-item best prices
  GET  /health                 — health check
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env before importing modules that need env vars
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ocr import extract_receipt_from_image
from categorizer import categorize_items
from stores import compare_cart_across_stores, ALL_STORES


# ── Pydantic models ──────────────────────────────────────────────────────────

class ScanReceiptRequest(BaseModel):
    image_base64: str                  # base64-encoded JPEG/PNG


class CategorizeRequest(BaseModel):
    items: list[str]                   # ["OxiClean", "Organic Bananas", ...]


class CartItem(BaseModel):
    name: str
    total_price: float
    category: str = "other"


class ComparePricesRequest(BaseModel):
    items: list[CartItem]
    source_store_name: str | None = None
    selected_store_ids: list[str] | None = None  # if None, uses all stores


# ── App setup ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ SplitSmart backend started on http://localhost:8000")
    print(f"   Stores available: {len(ALL_STORES)}")
    yield
    print("SplitSmart backend shutting down")


app = FastAPI(
    title="SplitSmart API",
    description="Price comparison, receipt OCR, and item categorization for the DMV area",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from Expo (localhost dev + LAN IP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # open during development; tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "stores": len(ALL_STORES)}


@app.post("/ocr/scan-receipt")
async def scan_receipt(req: ScanReceiptRequest):
    """
    Parse a receipt image and return structured line items + total.
    Body: { "image_base64": "<base64 string>" }
    """
    if not req.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    try:
        result = await extract_receipt_from_image(req.image_base64)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@app.post("/categorize")
async def categorize(req: CategorizeRequest):
    """
    Categorize a list of grocery item names.
    Body: { "items": ["OxiClean", "Bananas", ...] }
    Returns: { "categories": {"OxiClean": "household", ...} }
    """
    if not req.items:
        return {"categories": {}}
    try:
        categories = await categorize_items(req.items)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")


@app.post("/compare-prices")
async def compare_prices(req: ComparePricesRequest):
    """
    Compare a shopping cart across all DMV stores.
    Body: {
      "items": [{"name": str, "total_price": float, "category": str}],
      "source_store_name": str | null,
      "selected_store_ids": [str] | null
    }
    Returns: { "itemResults": [...], "storeRanking": [...], "totalPaid": float }
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="items list cannot be empty")
    try:
        items_dict = [
            {"name": item.name, "total_price": item.total_price, "category": item.category}
            for item in req.items
        ]
        result = await compare_cart_across_stores(
            items=items_dict,
            source_store_name=req.source_store_name,
            selected_store_ids=req.selected_store_ids,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price comparison failed: {str(e)}")


@app.post("/scan-and-compare")
async def scan_and_compare(req: ScanReceiptRequest):
    """
    Convenience endpoint: OCR a receipt, categorize items, then compare prices.
    One call does it all — used by the scan screen.
    """
    if not req.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")

    # Step 1: Extract receipt
    try:
        receipt = await extract_receipt_from_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

    items = receipt.get("items", [])
    if not items:
        return {**receipt, "comparison": None}

    # Step 2: Categorize items
    try:
        item_names = [i["name"] for i in items]
        categories = await categorize_items(item_names)
    except Exception:
        categories = {i["name"]: "other" for i in items}

    categorized_items = [
        {
            "name": i["name"],
            "total_price": i.get("total_price", 0),
            "category": categories.get(i["name"], "other"),
        }
        for i in items
    ]

    # Step 3: Compare prices
    try:
        comparison = await compare_cart_across_stores(
            items=categorized_items,
            source_store_name=receipt.get("store_name"),
            selected_store_ids=[s.id for s in ALL_STORES],
        )
    except Exception as e:
        comparison = None
        print(f"Comparison failed: {e}")

    return {**receipt, "comparison": comparison}
