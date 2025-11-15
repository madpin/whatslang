import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format as dateFnsFormat } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Safely format a date, handling null/undefined/invalid values
 */
export function formatDate(date: string | Date | null | undefined, formatStr: string, fallback: string = 'N/A'): string {
  if (!date) return fallback
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    // Check if date is valid
    if (isNaN(dateObj.getTime())) {
      return fallback
    }
    
    return dateFnsFormat(dateObj, formatStr)
  } catch (error) {
    console.warn('Invalid date:', date, error)
    return fallback
  }
}

