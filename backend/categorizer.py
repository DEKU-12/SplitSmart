"""
Item categorization — Groq AI with keyword fallback.
Mirrors the logic from lib/categorizer.ts but runs server-side.
"""

import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VALID_CATEGORIES = [
    "produce", "dairy", "meat_seafood", "bakery", "beverages",
    "snacks", "frozen", "household", "personal_care", "alcohol",
    "pharmacy", "deli", "pantry", "other"
]

# Keyword fallback map — same as TypeScript version
KEYWORD_MAP: dict[str, list[str]] = {
    "produce": ["apple","banana","orange","grape","strawberry","blueberry","lettuce",
                "spinach","kale","tomato","onion","garlic","pepper","broccoli","carrot",
                "celery","cucumber","avocado","lemon","lime","mango","peach","berry",
                "veggie","vegetable","fruit","salad","herb","cilantro","parsley",
                "mushroom","zucchini","squash","corn","potato","sweet potato"],
    "dairy": ["milk","cheese","yogurt","butter","cream","egg","eggs","sour cream",
              "cottage","mozzarella","cheddar","parmesan","brie","half & half",
              "whipped cream","creamer"],
    "meat_seafood": ["chicken","beef","pork","turkey","salmon","tuna","shrimp","fish",
                     "steak","ground","sausage","bacon","ham","lamb","tilapia","cod",
                     "lobster","crab","scallop"],
    "bakery": ["bread","bagel","muffin","donut","croissant","roll","bun","cake","pie",
               "cookie","brownie","pastry","baguette","tortilla","pita"],
    "beverages": ["water","juice","soda","coffee","tea","drink","gatorade","lemonade",
                  "sparkling","kombucha","smoothie","milk tea","energy drink",
                  "coconut water","almond milk","oat milk","soy milk"],
    "snacks": ["chip","pretzel","popcorn","cracker","granola","protein bar","trail mix",
               "nuts","almond","cashew","peanut","candy","chocolate","gummy",
               "marshmallow","rice cake"],
    "frozen": ["frozen","ice cream","popsicle","gelato","sorbet","pizza","burrito",
               "nugget","waffle","pancake mix"],
    "household": ["detergent","soap","dish","paper towel","toilet paper","trash bag",
                  "laundry","bleach","cleaner","sponge","foil","plastic wrap",
                  "zip lock","storage bag","napkin","oxiclean","tide","downy","gain"],
    "personal_care": ["shampoo","conditioner","body wash","lotion","toothpaste",
                      "deodorant","razor","sunscreen","face wash","makeup",
                      "moisturizer","lip","mascara","cologne","perfume"],
    "alcohol": ["beer","wine","vodka","whiskey","rum","tequila","gin","hard","cider",
                "ale","lager","champagne","prosecco","seltzer","truly","white claw"],
    "pharmacy": ["vitamin","medicine","aspirin","ibuprofen","tylenol","advil","allergy",
                 "bandage","supplement","melatonin","probiotic","fiber","antacid",
                 "cold medicine"],
    "deli": ["deli","prepared","rotisserie","hot","soup","sub","sandwich","salad bar","sushi"],
    "pantry": ["pasta","rice","cereal","oat","flour","sugar","salt","pepper","sauce",
               "salsa","ketchup","mustard","mayo","olive oil","oil","vinegar","honey",
               "syrup","jam","peanut butter","canned","bean","lentil","spice",
               "seasoning","broth","stock"],
}


def keyword_fallback(item_name: str) -> str:
    lower = item_name.lower()
    for category, keywords in KEYWORD_MAP.items():
        if any(kw in lower for kw in keywords):
            return category
    return "other"


async def categorize_items(items: list[str]) -> dict[str, str]:
    """
    Categorize a list of grocery item names.
    Tries Groq AI first, falls back to keyword matching.
    Returns {item_name: category} mapping.
    """
    if not items:
        return {}

    prompt = f"""You are a grocery item classifier. Categorize each item into exactly one category.

Items:
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(items))}

Valid categories (use exactly these strings):
produce, dairy, meat_seafood, bakery, beverages, snacks, frozen, household, personal_care, alcohol, pharmacy, deli, pantry, other

Rules:
- produce = fresh fruits and vegetables
- dairy = milk, cheese, yogurt, eggs, butter, cream
- meat_seafood = all fresh/packaged meat and fish
- bakery = bread, pastries, desserts
- beverages = non-alcoholic drinks (include plant milks here)
- snacks = chips, candy, nuts, bars, crackers
- frozen = frozen meals, ice cream, frozen vegetables
- household = cleaning, paper goods, trash bags, laundry, OxiClean, detergent
- personal_care = shampoo, soap, skincare, cosmetics
- alcohol = beer, wine, spirits, hard seltzer
- pharmacy = medicines, vitamins, supplements, bandages
- deli = prepared/hot foods, rotisserie
- pantry = canned goods, pasta, rice, oils, spices, condiments, sauces
- other = anything that doesn't fit above

Respond with ONLY a valid JSON object mapping item name to category. Example:
{{"Organic Bananas": "produce", "2% Milk Gallon": "dairy", "Tide Pods": "household"}}"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
        )

        raw = response.choices[0].message.content or "{}"
        result = json.loads(raw)

        # Validate and clean — fallback for anything Groq got wrong
        cleaned: dict[str, str] = {}
        for item in items:
            category = result.get(item, "")
            if category in VALID_CATEGORIES:
                cleaned[item] = category
            else:
                cleaned[item] = keyword_fallback(item)
        return cleaned

    except Exception as e:
        print(f"Groq categorizer error, using keyword fallback: {e}")
        return {item: keyword_fallback(item) for item in items}
