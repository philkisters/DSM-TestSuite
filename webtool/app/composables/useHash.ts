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

export function replicationHashes(id: string, replicationFactor: number): string[] {
  const hashes: string[] = []
  let digest = sha256(new TextEncoder().encode(id))
  for (let level = 0; level < replicationFactor; level++) {
    hashes.push(bytesToHex(digest))
    if (level + 1 < replicationFactor) digest = sha256(digest)
  }
  return hashes
}

export function useHash() {
  return { hashId, shortHash, replicationHashes, SHORT_HASH_LENGTH }
}
