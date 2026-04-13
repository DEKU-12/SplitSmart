/**
 * Category constants and pure helper functions.
 * No API calls here — just labels, colors, and math.
 */

export type ItemCategory =
  | 'produce' | 'dairy' | 'meat_seafood' | 'bakery' | 'beverages'
  | 'snacks' | 'frozen' | 'household' | 'personal_care' | 'alcohol'
  | 'pharmacy' | 'deli' | 'pantry' | 'other'

export const CATEGORY_LABELS: Record<ItemCategory, string> = {
  produce:       '🥦 Produce',
  dairy:         '🥛 Dairy',
  meat_seafood:  '🥩 Meat & Seafood',
  bakery:        '🍞 Bakery',
  beverages:     '🥤 Beverages',
  snacks:        '🍿 Snacks',
  frozen:        '🧊 Frozen',
  household:     '🧹 Household',
  personal_care: '🧴 Personal Care',
  alcohol:       '🍺 Alcohol',
  pharmacy:      '💊 Pharmacy',
  deli:          '🥙 Deli',
  pantry:        '🥫 Pantry',
  other:         '📦 Other',
}

export const CATEGORY_COLORS: Record<ItemCategory, string> = {
  produce:       '#4CAF50',
  dairy:         '#2196F3',
  meat_seafood:  '#F44336',
  bakery:        '#FF9800',
  beverages:     '#00BCD4',
  snacks:        '#9C27B0',
  frozen:        '#03A9F4',
  household:     '#795548',
  personal_care: '#E91E63',
  alcohol:       '#FF5722',
  pharmacy:      '#009688',
  deli:          '#FFC107',
  pantry:        '#8BC34A',
  other:         '#9E9E9E',
}

export function summarizeByCategory(
  items: { name: string; total_price: number; category?: string }[]
): { category: ItemCategory; total: number; count: number; percentage: number }[] {
  const totals: Record<string, { total: number; count: number }> = {}
  const grandTotal = items.reduce((s, i) => s + i.total_price, 0)

  for (const item of items) {
    const cat = (item.category as ItemCategory) || 'other'
    if (!totals[cat]) totals[cat] = { total: 0, count: 0 }
    totals[cat].total += item.total_price
    totals[cat].count += 1
  }

  return Object.entries(totals)
    .map(([category, data]) => ({
      category: category as ItemCategory,
      total: parseFloat(data.total.toFixed(2)),
      count: data.count,
      percentage: grandTotal > 0 ? Math.round((data.total / grandTotal) * 100) : 0,
    }))
    .sort((a, b) => b.total - a.total)
}
