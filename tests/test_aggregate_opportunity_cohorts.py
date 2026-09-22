from scripts.aggregate_opportunity_cohorts import aggregate

def cohort(day, eligible=10, hits=2):
    return {"cohorts":{day:{"bands":{"1":{"eligible":eligible,"later_breakout":hits}}}}}

def test_only_mature_cohorts_are_pooled(tmp_path):
    import json
    a=tmp_path/"a.json"; b=tmp_path/"b.json"
    a.write_text(json.dumps(cohort("2026-09-18",10,2)))
    b.write_text(json.dumps(cohort("2026-09-21",20,5)))
    x=aggregate([a,b],3,"2026-09-22")
    assert x["cohort_count"]==2
    assert x["mature_cohort_dates"]==["2026-09-18"]
    assert x["pooled_mature_bands"]["1"]["eligible"]==10
    assert x["decision"]["opportunity_rule_defined"] is False
    assert x["decision"]["sufficient_for_threshold_selection"] is False

def test_conflicting_same_date_fails_closed(tmp_path):
    import json,pytest
    a=tmp_path/"a.json"; b=tmp_path/"b.json"
    a.write_text(json.dumps(cohort("2026-09-18",10,2)))
    b.write_text(json.dumps(cohort("2026-09-18",11,2)))
    with pytest.raises(ValueError,match="conflicting cohort"):
        aggregate([a,b],3,"2026-09-22")
