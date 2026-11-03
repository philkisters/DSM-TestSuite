"""Expected state of the Chord ring, derived from the actions a scenario has performed."""
from bisect import bisect_left

from dsm_protocol import hash_id

ID_BITS = 256
ID_SPACE = 1 << ID_BITS


class ChordModel:
    def __init__(self) -> None:
        # Sorted by (hash, name), the same order as `Identity.ring_key`.
        self._ring: list[tuple[int, str]] = []

    def join(self, name: str) -> None:
        entry = (hash_id(name), name)
        if entry not in self._ring:
            self._ring.append(entry)
            self._ring.sort()

    def leave(self, name: str) -> None:
        self._ring = [e for e in self._ring if e[1] != name]

    def names(self) -> list[str]:
        return [n for _, n in self._ring]

    def __contains__(self, name: str) -> bool:
        return name in self.names()

    def successor_of_key(self, key: int) -> str:
        i = bisect_left(self._ring, (key % ID_SPACE, ""))
        return self._ring[i % len(self._ring)][1]

    def _index(self, name: str) -> int:
        for i, (_, n) in enumerate(self._ring):
            if n == name:
                return i
        raise KeyError(name)

    def successor(self, name: str) -> str:
        return self._ring[(self._index(name) + 1) % len(self._ring)][1]

    def predecessor(self, name: str) -> str:
        return self._ring[(self._index(name) - 1) % len(self._ring)][1]

    def fingers(self, name: str) -> list[str]:
        """Finger i is the first peer at or after (hash(name) + 2^i) mod 2^256."""
        base = hash_id(name)
        return [self.successor_of_key(base + (1 << i)) for i in range(ID_BITS)]
