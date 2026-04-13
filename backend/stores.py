"""
Multi-store price comparison engine — mirrors lib/stores.ts but runs server-side.

Store price indices are calibrated against the DMV market average (1.0)
using USDA food price surveys and BLS consumer price data for the DC metro area.
"""

import asyncio
from dataclasses import dataclass, field
from kroger import search_kroger_price, KrogerPrice


@dataclass
class StoreConfig:
    id: str
    name: str
    color: str
    emoji: str
    price_index: float          # overall index relative to DMV avg (1.0)
    category_modifiers: dict    # per-category overrides
    uses_kroger_api: bool
    kroger_multiplier: float = 1.0


ALL_STORES: list[StoreConfig] = [
    StoreConfig("aldi",         "Aldi",          "#00539B", "🔵", 0.74,
                {"produce":0.68,"dairy":0.72,"meat_seafood":0.78,"pantry":0.70,
                 "frozen":0.73,"bakery":0.72,"snacks":0.76}, False),

    StoreConfig("walmart",      "Walmart",        "#0071CE", "🛒", 0.88,
                {"produce":0.85,"dairy":0.86,"meat_seafood":0.90,
                 "household":0.82,"personal_care":0.84,"snacks":0.87}, False),

    StoreConfig("giant",        "Giant Food",     "#DA291C", "🔴", 0.97,
                {"produce":0.95,"dairy":0.96,"meat_seafood":0.97,"pantry":0.96}, False),

    StoreConfig("trader_joes",  "Trader Joe's",   "#8B0000", "🛍️", 0.99,
                {"produce":0.94,"dairy":0.97,"frozen":0.91,"snacks":0.94,"pantry":0.96}, False),

    StoreConfig("kroger",       "Kroger",         "#004990", "🔷", 0.96,
                {}, True, 1.0),

    StoreConfig("target",       "Target",         "#CC0000", "🎯", 1.02,
                {"household":0.98,"personal_care":0.99,"snacks":1.03,"beverages":1.04}, False),

    StoreConfig("safeway",      "Safeway",        "#E31837", "🟥", 1.03,
                {}, False),

    StoreConfig("harris_teeter","Harris Teeter",  "#E31837", "🏪", 1.05,
                {"produce":1.04,"dairy":1.03,"meat_seafood":1.06,"deli":1.08},
                True, 1.05),

    StoreConfig("wegmans",      "Wegmans",        "#7B1113", "🍎", 1.08,
                {"produce":1.05,"dairy":1.05,"bakery":1.10,"deli":1.12,"meat_seafood":1.08}, False),

    StoreConfig("whole_foods",  "Whole Foods",    "#00674B", "🌿", 1.22,
                {"produce":1.20,"dairy":1.18,"meat_seafood":1.28,
                 "bakery":1.22,"pantry":1.20,"deli":1.25}, False),

    StoreConfig("walgreens",    "Walgreens",      "#E31837", "💊", 1.18,
                {"pharmacy":1.05,"personal_care":1.15,
                 "beverages":1.28,"snacks":1.22,"household":1.20}, False),
]

STORE_MAP = {s.id: s for s in ALL_STORES}


def detect_source_store(store_name: str | None) -> StoreConfig | None:
    if not store_name:
        return None
    lower = store_name.lower()
    keywords: dict[str, list[str]] = {
        "aldi":         ["aldi"],
        "walmart":      ["walmart", "wal-mart"],
        "giant":        ["giant", "giant food"],
        "trader_joes":  ["trader joe"],
        "kroger":       ["kroger"],
        "target":       ["target"],
        "safeway":      ["safeway"],
        "harris_teeter":["harris teeter", " ht "],
        "wegmans":      ["wegmans"],
        "whole_foods":  ["whole foods", "wfm"],
        "walgreens":    ["walgreens"],
    }
    for store_id, kws in keywords.items():
        if any(kw in lower for kw in kws):
            return STORE_MAP.get(store_id)
    return None


@dataclass
class StorePriceResult:
    store_id: str
    store_name: str
    store_color: str
    store_emoji: str
    price: float
    is_estimated: bool
    is_on_sale: bool = False
    product_match: str | None = None


@dataclass
class ItemComparisonResult:
    item_name: str
    paid_price: float
    category: str
    store_prices: list[StorePriceResult]
    cheapest_store: str
    cheapest_store_name: str
    cheapest_price: float
    most_expensive_store: str
    most_expensive_price: float
    avg_price: float
    paid_at_store: str | None = None


@dataclass
class TripComparisonResult:
    store_id: str
    store_name: str
    store_color: str
    store_emoji: str
    total_cost: float
    savings_vs_paid: float
    items_found: int
    rank: int = 0


async def compare_item_across_stores(
    item_name: str,
    paid_price: float,
    category: str = "other",
    source_store_name: str | None = None,
    selected_store_ids: list[str] | None = None,
) -> ItemComparisonResult:
    stores_to_check = (
        [s for s in ALL_STORES if s.id in selected_store_ids]
        if selected_store_ids
        else ALL_STORES
    )

    # Back-calculate market average price from source store
    source_store = detect_source_store(source_store_name)
    source_index = (
        source_store.category_modifiers.get(category, source_store.price_index)
        if source_store else 1.0
    )
    market_avg_price = paid_price / source_index

    # Try Kroger API for a real reference price
    kroger_api_price: float | None = None
    kroger_product_name: str | None = None
    kroger_on_sale = False

    try:
        result: KrogerPrice | None = await search_kroger_price(item_name, paid_price)
        if result and result.price:
            kroger_api_price = result.price
            kroger_product_name = result.product_name
            kroger_on_sale = result.on_sale
    except Exception as e:
        print(f"Kroger API unavailable for '{item_name}': {e}")

    # Build per-store prices
    store_prices: list[StorePriceResult] = []
    for store in stores_to_check:
        if store.uses_kroger_api and kroger_api_price is not None:
            price = round(kroger_api_price * store.kroger_multiplier, 2)
            store_prices.append(StorePriceResult(
                store_id=store.id,
                store_name=store.name,
                store_color=store.color,
                store_emoji=store.emoji,
                price=price,
                is_estimated=(store.id == "harris_teeter"),
                is_on_sale=(store.id == "kroger" and kroger_on_sale),
                product_match=(kroger_product_name if store.id == "kroger" else None),
            ))
        else:
            # Model estimate — use Kroger price as reference if available
            kroger_store = STORE_MAP.get("kroger")
            reference = (
                kroger_api_price / (kroger_store.price_index if kroger_store else 1.0)
                if kroger_api_price is not None
                else market_avg_price
            )
            cat_mod = store.category_modifiers.get(category, store.price_index)
            estimated = round(reference * cat_mod, 2)
            store_prices.append(StorePriceResult(
                store_id=store.id,
                store_name=store.name,
                store_color=store.color,
                store_emoji=store.emoji,
                price=estimated,
                is_estimated=True,
            ))

    cheapest = min(store_prices, key=lambda x: x.price)
    priciest = max(store_prices, key=lambda x: x.price)
    avg = round(sum(s.price for s in store_prices) / len(store_prices), 2)

    return ItemComparisonResult(
        item_name=item_name,
        paid_price=paid_price,
        category=category,
        store_prices=store_prices,
        cheapest_store=cheapest.store_id,
        cheapest_store_name=cheapest.store_name,
        cheapest_price=cheapest.price,
        most_expensive_store=priciest.store_id,
        most_expensive_price=priciest.price,
        avg_price=avg,
        paid_at_store=source_store.id if source_store else None,
    )


async def compare_cart_across_stores(
    items: list[dict],
    source_store_name: str | None = None,
    selected_store_ids: list[str] | None = None,
) -> dict:
    """
    Compare all items in a cart across all DMV stores.
    items: [{"name": str, "total_price": float, "category": str}]
    Returns: {"item_results": [...], "store_ranking": [...], "total_paid": float}
    """
    total_paid = sum(i["total_price"] for i in items)
    to_compare = items[:10]  # cap at 10 to avoid Kroger rate limits

    item_results: list[ItemComparisonResult] = []
    for item in to_compare:
        result = await compare_item_across_stores(
            item_name=item["name"],
            paid_price=item["total_price"],
            category=item.get("category", "other"),
            source_store_name=source_store_name,
            selected_store_ids=selected_store_ids,
        )
        item_results.append(result)
        await asyncio.sleep(0.25)  # small delay between Kroger API calls

    # Sum per-store cart totals
    store_totals: dict[str, float] = {}
    for result in item_results:
        for sp in result.store_prices:
            store_totals[sp.store_id] = round(
                store_totals.get(sp.store_id, 0) + sp.price, 2
            )

    store_ranking: list[TripComparisonResult] = sorted(
        [
            TripComparisonResult(
                store_id=store_id,
                store_name=STORE_MAP[store_id].name,
                store_color=STORE_MAP[store_id].color,
                store_emoji=STORE_MAP[store_id].emoji,
                total_cost=total,
                savings_vs_paid=round(total_paid - total, 2),
                items_found=len(item_results),
            )
            for store_id, total in store_totals.items()
            if store_id in STORE_MAP
        ],
        key=lambda x: x.total_cost,
    )
    for i, r in enumerate(store_ranking):
        r.rank = i + 1

    # Serialize to plain dicts for JSON response
    def item_result_to_dict(r: ItemComparisonResult) -> dict:
        return {
            "itemName": r.item_name,
            "paidPrice": r.paid_price,
            "category": r.category,
            "cheapestStore": r.cheapest_store,
            "cheapestStoreName": r.cheapest_store_name,
            "cheapestPrice": r.cheapest_price,
            "mostExpensiveStore": r.most_expensive_store,
            "mostExpensivePrice": r.most_expensive_price,
            "avgPrice": r.avg_price,
            "paidAtStore": r.paid_at_store,
            "storePrices": [
                {
                    "storeId": sp.store_id,
                    "storeName": sp.store_name,
                    "storeColor": sp.store_color,
                    "storeEmoji": sp.store_emoji,
                    "price": sp.price,
                    "isEstimated": sp.is_estimated,
                    "isOnSale": sp.is_on_sale,
                    "productMatch": sp.product_match,
                }
                for sp in r.store_prices
            ],
        }

    def ranking_to_dict(r: TripComparisonResult) -> dict:
        return {
            "storeId": r.store_id,
            "storeName": r.store_name,
            "storeColor": r.store_color,
            "storeEmoji": r.store_emoji,
            "totalCost": r.total_cost,
            "savingsVsPaid": r.savings_vs_paid,
            "itemsFound": r.items_found,
            "rank": r.rank,
        }

    return {
        "itemResults": [item_result_to_dict(r) for r in item_results],
        "storeRanking": [ranking_to_dict(r) for r in store_ranking],
        "totalPaid": total_paid,
    }
