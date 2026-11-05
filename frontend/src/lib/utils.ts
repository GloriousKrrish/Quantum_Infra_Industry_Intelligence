import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines clsx and tailwind-merge for conditional class name composition.
 * Resolves Tailwind CSS class conflicts automatically.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency in Indian Rupees (Crores)
 */
export function formatCurrency(value: number): string {
  return `₹${value.toFixed(1)} Cr`;
}

/**
 * Format percentage values
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}
