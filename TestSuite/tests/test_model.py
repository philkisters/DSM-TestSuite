import pytest

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


def test_images_follow_ring_and_membership_changes():
    m = ChordModel()
    m.join("a")
    for image in ("image-3", "image-1", "image-2", "image-1"):
        m.store_image(image)
    assert m.images("a") == ["image-1", "image-2", "image-3"]

    m.join("b")
    ring = sorted((hash_id(name), name) for name in ("a", "b"))
    expected = {name: [] for _, name in ring}
    for image in ("image-1", "image-2", "image-3"):
        key = (hash_id(image), image)
        owner = next((name for peer_key, name in ring if (peer_key, name) >= key), ring[0][1])
        expected[owner].append(image)
    assert {name: m.images(name) for name in ("a", "b")} == expected

    m.leave("a")
    assert m.images("b") == ["image-1", "image-2", "image-3"]
    with pytest.raises(KeyError):
        m.images("a")
    m.leave("b")
    with pytest.raises(KeyError):
        m.images("b")


def test_image_ownership_wraparound_and_equal_hashes(monkeypatch):
    hashes = {
        "peer-a": 10, "peer-b": 10, "peer-c": 20,
        "before": 5, "peer-aa": 10, "peer-z": 10, "middle": 15, "after": 25,
    }
    monkeypatch.setattr("dsm_testsuite.model.hash_id", hashes.__getitem__)
    m = ChordModel()
    for name in ("peer-a", "peer-b", "peer-c"):
        m.join(name)
    for image in ("before", "peer-a", "peer-aa", "peer-z", "middle", "after"):
        m.store_image(image)

    assert m.images("peer-a") == ["after", "before", "peer-a"]
    assert m.images("peer-b") == ["peer-aa"]
    assert m.images("peer-c") == ["middle", "peer-z"]


def test_stopping_peer_loses_only_its_images(monkeypatch):
    hashes = {"a": 10, "b": 20, "c": 30, "wrap": 35, "middle": 15, "other": 25}
    monkeypatch.setattr("dsm_testsuite.model.hash_id", hashes.__getitem__)
    m = ChordModel()
    for peer in ("a", "b", "c"):
        m.join(peer)
    for image in ("wrap", "middle", "other"):
        m.store_image(image)

    m.stop("a")
    assert m.images("b") == ["middle"]
    assert m.images("c") == ["other"]
    m.join("a")
    assert m.images("a") == []

    m.stop("not-joined")
    assert m.images("b") == ["middle"]
    m.stop("b")
    m.stop("c")
    m.stop("a")
    m.join("a")
    assert m.images("a") == []
