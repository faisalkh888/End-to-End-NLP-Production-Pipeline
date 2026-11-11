from evals.metrics import macro_f1, recall_at_k, wilson_interval, json_validity


def test_recall_macro_f1_and_intervals():
    assert recall_at_k({"a"}, ["a", "b"], 2) == 1
    assert macro_f1(["bug", "bug"], ["bug", "other"]) > 0
    lo, hi = wilson_interval(8, 10)
    assert lo < .8 < hi


def test_json_validity_counts_required_keys():
    assert json_validity(['{"category":"bug","priority":"low","product_area":"x","summary":"y"}', '{oops}']) == .5
