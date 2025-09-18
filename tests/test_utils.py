from src.dedupe_core import split_multi, uniq_stable, pick_with_fallback

def test_split_multi():
    assert split_multi("a,b; c") == ["a,b","c"]
    assert split_multi(["x","x","y"]) == ["x","x","y"]

def test_uniq_stable():
    assert uniq_stable(["a","b","a","c","b"]) == ["a","b","c"]

def test_pick_with_fallback():
    recs = [{"val":""},{"val":"x"},{"val":""}]
    assert pick_with_fallback(recs, "val", "latest") == "x"
    assert pick_with_fallback(recs, "val", "initial") == "x"
