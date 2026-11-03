from dsm_protocol import hash_id

from dsm_testsuite.model import ID_BITS, ChordModel


def test_single_peer_points_at_itself():
    m = ChordModel()
    m.join("a")
    assert m.successor("a") == m.predecessor("a") == "a"
    assert m.fingers("a") == ["a"] * ID_BITS


def test_ring_follows_hash_order_and_leave():
    m = ChordModel()
    for n in ("a", "b", "c", "d"):
        m.join(n)
    order = sorted(["a", "b", "c", "d"], key=lambda n: (hash_id(n), n))
    assert m.names() == order
    for i, n in enumerate(order):
        assert m.successor(n) == order[(i + 1) % 4]
        assert m.predecessor(n) == order[i - 1]
    m.leave(order[0])
    assert m.names() == order[1:]


def test_fingers_match_definition():
    m = ChordModel()
    for n in ("a", "b", "c"):
        m.join(n)
    ring = sorted((hash_id(n), n) for n in ("a", "b", "c"))
    fingers = m.fingers("a")
    for i in (0, 100, 255):
        key = (hash_id("a") + (1 << i)) % (1 << ID_BITS)
        expected = next((n for h, n in ring if h >= key), ring[0][1])
        assert fingers[i] == expected
    assert fingers[0] == m.successor("a")
