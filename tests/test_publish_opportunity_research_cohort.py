from pathlib import Path

def test_contract_prefix_is_research_only():
    text=(Path(__file__).resolve().parents[1]/"scripts"/"publish_opportunity_research_cohort.py").read_text()
    assert 'PREFIX="pattern-breakout/research/opportunity-cohorts"' in text
    assert '"status":"RESEARCH_ONLY"' in text
    assert '"eligibility_rule_defined":False' in text
