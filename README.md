<div align="center">

# ⚡ SplitSmart

**Scan a grocery receipt. Split the bill. Track the spend.**

Receipt photo → Claude vision → structured items → split by item, percent or equally → shared group ledger → spending analytics

AI receipt OCR · multi-way bill splitting · debt simplification · Supabase-backed groups · React Native + FastAPI

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Expo SDK 54](https://img.shields.io/badge/Expo-SDK%2054-000020?logo=expo&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
![Claude](https://img.shields.io/badge/AI-Claude-D97757)

</div>

## 🎬 Demo



https://github.com/user-attachments/assets/8d04cd07-7791-44d4-879c-ca4c2bfbb3df




*40-second walkthrough recorded from the running app: upload a receipt, Claude reads it, split by item, saved to the group, bill detail, analytics.*

| Review scanned items | Split by item | Analytics |
|---|---|---|
| <img src="docs/screens/review.jpg" width="240"> | <img src="docs/screens/split.png" width="240"> | <img src="docs/screens/analytics.jpg" width="240"> |

## Contents

- [Highlights](#-highlights)
- [Measured results](#-measured-results)
- [How it works](#️-how-it-works)
- [Quick start](#-quick-start)
- [Configuration](#-configuration)
- [API](#-api)
- [Database](#️-database)
- [Evaluation](#-evaluation)
- [Project structure](#-project-structure)
- [Roadmap](#-roadmap)

## ✨ Highlights

- **Photo in, itemized bill out.** Upload a receipt or use the camera. Claude vision returns structured JSON: store, date, every line item (name, quantity, unit and total price), subtotal, tax, tip and total.
- **Review before you split.** A review screen lets you fix names, quantities and prices, or add a missing item. A manual-entry flow covers anything without a receipt (restaurant, gas, rent).
- **Five ways to split.** Equal, exact amounts, percent, shares, or **by item** (tap who had what; tax is shared automatically).
- **Groups and a shared ledger.** Create groups, add expenses, and open any bill to see the payer, each person's share and every scanned item.
- **Debt simplification.** Settle Up collapses everyone's balances into the fewest payments (`lib/debt-calculator.ts`) and records settlements.
- **AI categories.** Every item is categorized (produce, dairy, meat and seafood, household, alcohol and more) by Claude, with a keyword fallback if the API call fails.
- **Spending analytics.** Total spent, bill count, average bill, monthly spend, and spending by category and by group.
- **Price Compass.** Compares a cart across 11 DMV-area stores (Aldi, Walmart, Giant, Trader Joe's, Kroger, Target, Safeway, Harris Teeter, Wegmans, Whole Foods, Walgreens). Kroger's reference price comes from the live Kroger Product API; the other stores are estimated from a category-level DMV price index and labeled "est." in the app.
- **Keys stay server-side.** The app never calls the AI model directly; OCR, categorization and price lookups go through the FastAPI backend.

## 📊 Measured results

Numbers from running this repo, not from a published benchmark:

| Metric | Result | How it was measured |
|---|---|---|
| OCR API latency | **3.5 s** median | 3 calls to `/ocr/scan-receipt` with one Harris Teeter receipt photo (348×348 px), `claude-sonnet-5-5` |
| Receipt accuracy | **3 / 3** runs matched the receipt's items, tax ($0.08) and total ($3.06) | same 3 calls |
| Stores in the price index | **11** | `GET /health` |
| API endpoints | **5** | `backend/main.py` |

This is a smoke test on a single low-resolution receipt, not a labeled benchmark. Model choice mattered on that image: `claude-sonnet-5-5` read it correctly every time, while `claude-haiku-4-5` invented line items, so Sonnet is the default OCR model.

## ⚙️ How it works

```
 Receipt photo (camera / gallery / upload)
          │
          ▼
 [1] Expo app ───────────── picks the image, sends base64 to the backend
          │
          ▼
 [2] FastAPI /ocr/scan-receipt ── Claude vision → { store, date, items[], subtotal, tax, tip, total }
          │
          ▼
 [3] Review screen ──────── user fixes any item, price or quantity
          │
          ▼
 [4] Split ──────────────── equal · exact · percent · shares · by item (tax shared)
          │
          ▼
 [5] Supabase ───────────── bills + bill_items + bill_splits saved to the group
          │
          ▼
 [6] Ledger and insights ── bill detail · settle up (debt simplification) · analytics
                            /categorize (Claude) · /compare-prices (Kroger + DMV index)
```

```
Expo app (iOS / Android / web)
   │
   ├── REST (JSON) ──────► FastAPI backend (:8000)
   │                          ├── Claude (receipt OCR + item categorization)
   │                          ├── Kroger Product API (live reference price)
   │                          └── Store price index (11 stores)
   │
   └── supabase-js ──────► Supabase (Postgres + Auth)
```

| Layer | Technology |
|---|---|
| Mobile app | React Native 0.81, Expo SDK 54, expo-router, TypeScript |
| Backend | Python 3.12, FastAPI, Uvicorn, httpx |
| AI | Anthropic Claude (vision for OCR, text for categorization) |
| Database and auth | Supabase (Postgres, Auth) |
| Prices | Kroger Product API (OAuth2) plus a modeled DMV store index |

## 🚀 Quick start

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- A [Supabase](https://supabase.com) project
- An [Anthropic API key](https://console.anthropic.com)
- Optional: Kroger developer credentials ([developer.kroger.com](https://developer.kroger.com)) for live reference prices
- To run on the iOS Simulator you need Xcode. Otherwise use Expo Go on a phone, or the web build.

### 1. Clone and install

```bash
git clone https://github.com/DEKU-12/SplitSmart.git
cd SplitSmart
npm install --legacy-peer-deps
```

### 2. Add your keys

Create `.env` in the project root:

```env
EXPO_PUBLIC_SUPABASE_URL=https://<your-project-id>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<your publishable / anon key>
EXPO_PUBLIC_API_URL=http://localhost:8000
```

Use your Mac's LAN IP instead of `localhost` when running on a physical phone.

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5-5
# Optional: live Kroger reference prices
KROGER_CLIENT_ID=
KROGER_CLIENT_SECRET=
```

Both files are git-ignored. Never put a Supabase `service_role` key or an `sk-ant-` key in an `EXPO_PUBLIC_` variable, because those are bundled into the app.

### 3. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Check it: `curl localhost:8000/health` returns `{"status":"ok","stores":11}`.

### 4. Start the app

```bash
npx expo start
```

Press `i` for the iOS Simulator, `w` for web, or scan the QR code with Expo Go. On web, use **Upload Photo** (the camera option is native-only).

## 🔧 Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `EXPO_PUBLIC_SUPABASE_URL` | `.env` | none | Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | `.env` | none | Supabase publishable / anon key |
| `EXPO_PUBLIC_API_URL` | `.env` | `http://localhost:8000` | Backend base URL (use your LAN IP on a phone) |
| `ANTHROPIC_API_KEY` | `backend/.env` | none | Claude key for OCR and categorization |
| `ANTHROPIC_MODEL` | `backend/.env` | `claude-sonnet-5-5` (OCR), `claude-haiku-4-5` (categorizer) | Model override; one value applies to both |
| `KROGER_CLIENT_ID` / `KROGER_CLIENT_SECRET` | `backend/.env` | none | Optional live Kroger prices |

## 📡 API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check and store count |
| `POST` | `/ocr/scan-receipt` | `{image_base64}` → extracted receipt JSON |
| `POST` | `/categorize` | `{items: [...]}` → `{categories: {name: category}}` |
| `POST` | `/compare-prices` | Categorized cart → per-store totals and per-item best prices |
| `POST` | `/scan-and-compare` | OCR, categorize and compare in one call |

## 🗄️ Database

Tables the app reads and writes (taken from the queries in `app/` and `lib/`):

```
profiles       id, full_name, avatar_url, phone, created_at
groups         id, name, description, created_by, created_at
group_members  group_id, user_id, role, joined_at
bills          id, group_id, paid_by, description, total_amount, split_type, created_at
bill_items     id, bill_id, name, quantity, unit_price, total_price, category
bill_splits    id, bill_id, user_id, amount_owed
settlements    payments recorded by Settle Up
```

Create these in your own Supabase project and enable Row Level Security with policies (for example, group members can read and write their group's bills) so the publishable key can only see rows its user is allowed to.

## 🧪 Evaluation

Reproduce the OCR latency and accuracy check with any receipt photo:

```bash
B64=$(base64 -i receipt.jpg | tr -d '\n')
for i in 1 2 3; do
  curl -s -w '\n%{time_total}s\n' -X POST localhost:8000/ocr/scan-receipt \
    -H 'content-type: application/json' \
    -d "{\"image_base64\":\"$B64\"}"
done
```

Each call prints the extracted items, subtotal, tax and total, followed by the request time. Compare them with the receipt.

Check the backend and store index:

```bash
curl localhost:8000/health
curl -X POST localhost:8000/categorize -H 'content-type: application/json' \
  -d '{"items":["Organic Bananas","2% Milk Gallon","Tide Pods"]}'
```

## 📁 Project structure

```
SplitSmart/
├── app/                          # Expo Router screens
│   ├── (auth)/                   # login, signup
│   └── (tabs)/
│       ├── home.tsx              # balances, quick actions, recent bills
│       ├── scan.tsx              # upload / camera → review → split → save
│       ├── analytics.tsx         # spending insights
│       ├── price-compass.tsx     # cross-store cart comparison
│       ├── groups.tsx            # group list and creation
│       ├── profile.tsx
│       └── group/                # [id], add-expense, bill-detail, settle
├── lib/
│   ├── api.ts                    # backend client
│   ├── supabase.ts               # Supabase client
│   ├── debt-calculator.ts        # debt simplification
│   ├── categories.ts, storeConfig.ts, types.ts
├── backend/
│   ├── main.py                   # FastAPI routes
│   ├── ocr.py                    # Claude vision receipt parser
│   ├── categorizer.py            # Claude categorization + keyword fallback
│   ├── stores.py                 # 11-store price index and cart comparison
│   ├── kroger.py                 # Kroger Product API client
│   └── requirements.txt
├── docs/                         # demo video and screenshots
├── app.json, package.json, tsconfig.json
└── README.md
```

## 🧭 Roadmap

- [ ] Commit the Supabase schema and Row Level Security policies so a fresh project is a one-command setup
- [ ] Match products by size and unit before comparing prices in Price Compass
- [ ] Labeled receipt set (50+ receipts across stores) with an accuracy script and a CI check
- [ ] Self-correction loop: re-prompt the model when line items don't sum to the receipt total
- [ ] Activity feed of recent group transactions
- [ ] Member invites by link or email
- [ ] Automated tests for the backend routes and the debt-simplification logic
- [ ] Push notifications for new expenses and settle-up reminders

## License

MIT
