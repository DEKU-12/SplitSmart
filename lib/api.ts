/**
 * SplitSmart Python Backend API Client
 *
 * All AI, OCR, and price comparison logic now runs in the Python FastAPI
 * backend at localhost:8000. This file is the single place the frontend
 * calls the backend — no more direct Groq / Kroger calls from TypeScript.
 */

// Change this to your LAN IP (e.g. "http://192.168.1.x:8000") when testing
// on a physical device connected to the same WiFi.
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'

// ── Types ──────────────────────────────────────────────────────────────────

export interface ExtractedItem {
  name: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface ExtractedReceipt {
  store_name: string | null
  date: string | null
  items: ExtractedItem[]
  subtotal: number | null
  tax: number | null
  tip: number | null
  total: number
}

export interface StorePriceResult {
  storeId: string
  storeName: string
  storeColor: string
  storeEmoji: string
  price: number
  isEstimated: boolean
  isOnSale: boolean
  productMatch?: string
}

export interface ItemComparisonResult {
  itemName: string
  paidPrice: number
  category: string
  storePrices: StorePriceResult[]
  cheapestStore: string
  cheapestStoreName: string
  cheapestPrice: number
  mostExpensiveStore: string
  mostExpensivePrice: number
  avgPrice: number
  paidAtStore?: string | null
}

export interface TripComparisonResult {
  storeId: string
  storeName: string
  storeColor: string
  storeEmoji: string
  totalCost: number
  savingsVsPaid: number
  itemsFound: number
  rank: number
}

export interface CartComparisonResponse {
  itemResults: ItemComparisonResult[]
  storeRanking: TripComparisonResult[]
  totalPaid: number
}

export interface ScanAndCompareResponse extends ExtractedReceipt {
  comparison: CartComparisonResponse | null
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function post<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `API error ${response.status}`)
  }

  return response.json() as Promise<T>
}

// ── API functions ──────────────────────────────────────────────────────────

/**
 * Scan a receipt image and extract line items + total.
 * @param imageBase64 - base64-encoded JPEG/PNG (no data: prefix needed)
 */
export async function scanReceipt(imageBase64: string): Promise<ExtractedReceipt> {
  return post<ExtractedReceipt>('/ocr/scan-receipt', { image_base64: imageBase64 })
}

/**
 * Categorize a list of grocery item names (e.g. "OxiClean" → "household").
 * @param items - array of item name strings
 */
export async function categorizeItems(items: string[]): Promise<Record<string, string>> {
  const res = await post<{ categories: Record<string, string> }>('/categorize', { items })
  return res.categories
}

/**
 * Compare a shopping cart across all DMV stores.
 * Returns store rankings (cheapest first) and per-item best prices.
 */
export async function compareCart(
  items: { name: string; total_price: number; category?: string }[],
  sourceStoreName?: string | null,
): Promise<CartComparisonResponse> {
  return post<CartComparisonResponse>('/compare-prices', {
    items: items.map(i => ({
      name: i.name,
      total_price: i.total_price,
      category: i.category || 'other',
    })),
    source_store_name: sourceStoreName || null,
    selected_store_ids: null,   // null = all stores
  })
}

/**
 * One-shot endpoint: OCR → categorize → compare prices.
 * Used by the scan screen to do everything in a single request.
 */
export async function scanAndCompare(imageBase64: string): Promise<ScanAndCompareResponse> {
  return post<ScanAndCompareResponse>('/scan-and-compare', { image_base64: imageBase64 })
}

/**
 * Health check — returns true if the backend is reachable.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`)
    return res.ok
  } catch {
    return false
  }
}
