"""
Receipt OCR — mirrors lib/gemini.ts but uses Claude vision server-side.
Takes a base64-encoded image and returns structured receipt data.
"""

import json
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

PROMPT = """You are a receipt parser. Extract all purchased line items from this receipt image.

Return ONLY valid JSON, no explanation, no markdown, just raw JSON:

{
  "store_name": "string or null",
  "date": "YYYY-MM-DD or null",
  "items": [
    {
      "name": "clean human-readable product name",
      "quantity": 1,
      "unit_price": 0.00,
      "total_price": 0.00
    }
  ],
  "subtotal": 0.00,
  "tax": 0.00,
  "tip": null,
  "total": 0.00
}

Rules:
1. NEVER include subtotal, tax, tip, or total as line items
2. If quantity not shown, use 1
3. All prices are plain numbers in dollars like 4.99 not "$4.99"
4. Expand abbreviations: "ORG 2% MLK" becomes "Organic 2% Milk"
5. If a value is missing use null
6. total must always be a number
7. Clean up product names: remove store codes, PLU numbers, abbreviations"""


async def extract_receipt_from_image(image_base64: str) -> dict:
    """
    Extract receipt data from a base64-encoded image using Claude vision.
    Returns structured receipt data matching the ExtractedReceipt interface.
    """
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": PROMPT,
                        },
                    ],
                }
            ],
        )

        text = "".join(b.text for b in response.content if b.type == "text")

        # Strip any accidental markdown code fences
        cleaned = (
            text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(cleaned)

        # Ensure required fields exist
        parsed.setdefault("store_name", None)
        parsed.setdefault("date", None)
        parsed.setdefault("items", [])
        parsed.setdefault("subtotal", None)
        parsed.setdefault("tax", None)
        parsed.setdefault("tip", None)
        parsed.setdefault("total", 0)

        # Ensure total is a number
        if not isinstance(parsed["total"], (int, float)):
            parsed["total"] = sum(
                item.get("total_price", 0) for item in parsed["items"]
            )

        print(f"OCR extracted {len(parsed['items'])} items from receipt")
        return parsed

    except json.JSONDecodeError as e:
        print(f"OCR JSON parse error: {e}")
        raise ValueError(f"Could not parse receipt data: {e}")
    except Exception as e:
        print(f"OCR error: {e}")
        raise
