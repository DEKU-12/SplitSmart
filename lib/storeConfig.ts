/**
 * Store display configs — UI only (id, name, color, emoji).
 * All price logic lives in the Python backend now.
 */

export type StoreId =
  | 'aldi' | 'walmart' | 'giant' | 'trader_joes' | 'kroger'
  | 'target' | 'safeway' | 'harris_teeter' | 'wegmans'
  | 'whole_foods' | 'walgreens'

export interface StoreConfig {
  id: StoreId
  name: string
  color: string
  emoji: string
}

export const ALL_STORES: StoreConfig[] = [
  { id: 'aldi',          name: 'Aldi',          color: '#00539B', emoji: '🔵' },
  { id: 'walmart',       name: 'Walmart',        color: '#0071CE', emoji: '🛒' },
  { id: 'giant',         name: 'Giant Food',     color: '#DA291C', emoji: '🔴' },
  { id: 'trader_joes',   name: "Trader Joe's",   color: '#8B0000', emoji: '🛍️' },
  { id: 'kroger',        name: 'Kroger',         color: '#004990', emoji: '🔷' },
  { id: 'target',        name: 'Target',         color: '#CC0000', emoji: '🎯' },
  { id: 'safeway',       name: 'Safeway',        color: '#E31837', emoji: '🟥' },
  { id: 'harris_teeter', name: 'Harris Teeter',  color: '#E31837', emoji: '🏪' },
  { id: 'wegmans',       name: 'Wegmans',        color: '#7B1113', emoji: '🍎' },
  { id: 'whole_foods',   name: 'Whole Foods',    color: '#00674B', emoji: '🌿' },
  { id: 'walgreens',     name: 'Walgreens',      color: '#E31837', emoji: '💊' },
]

export const STORE_MAP = Object.fromEntries(ALL_STORES.map(s => [s.id, s])) as Record<StoreId, StoreConfig>
