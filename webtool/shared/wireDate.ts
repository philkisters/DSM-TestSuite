import { z } from 'zod'

// Backend timestamps are UTC but not always marked, and both `new Date()` and
// zod's coercion read a zone-less "2026-08-18T14:32:00" as local time. Naked
// date-times are stamped UTC before parsing; everything else passes through.
const NAKED_DATE_TIME = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/

export function parseWireDate(value: string | number | Date): Date {
  if (typeof value !== 'string') return new Date(value)
  const trimmed = value.trim()
  if (!NAKED_DATE_TIME.test(trimmed)) return new Date(trimmed)
  return new Date(`${trimmed.replace(' ', 'T')}Z`)
}

// Accepts string | number | Date, always produces a UTC-correct Date.
// Rendering to local time is Intl's default behaviour (see useDateUtils).
export const wireDate = z
  .union([z.string(), z.number(), z.date()])
  .transform(parseWireDate)
  .refine((d) => !Number.isNaN(d.getTime()), { message: 'Invalid date' })
