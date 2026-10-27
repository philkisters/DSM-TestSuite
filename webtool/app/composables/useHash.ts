import { sha256 } from '@noble/hashes/sha2.js'
import { bytesToHex } from '@noble/hashes/utils.js'

export const SHORT_HASH_LENGTH = 8

// Matches dsm_protocol.hash_id (SHA-256 of the UTF-8 id).
export function hashId(id: string): string {
  return bytesToHex(sha256(new TextEncoder().encode(id)))
}

export function shortHash(id: string): string {
  return hashId(id).slice(0, SHORT_HASH_LENGTH)
}

export function useHash() {
  return { hashId, shortHash, SHORT_HASH_LENGTH }
}
