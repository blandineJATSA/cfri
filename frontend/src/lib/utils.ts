import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('fr-FR').format(n)
}

export function riskColor(level: 'low' | 'medium' | 'high' | 'critical') {
  const map = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700',
  }
  return map[level]
}

export function riskLabel(level: 'low' | 'medium' | 'high' | 'critical') {
  const map = {
    low: 'Faible',
    medium: 'Moyen',
    high: 'Élevé',
    critical: 'Critique',
  }
  return map[level]
}

export function categoryLabel(category: string) {
  const map: Record<string, string> = {
    delivery: 'Livraison',
    product_quality: 'Qualité produit',
    refund: 'Remboursement',
    customer_service: 'Service client',
    pricing: 'Prix',
    website: 'Site web',
    stock: 'Stock',
    other: 'Autre',
  }
  return map[category] ?? category
}