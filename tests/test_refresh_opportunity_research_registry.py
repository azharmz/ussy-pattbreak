from pathlib import Path

def test_registry_is_research_only_and_fail_closed():
 text=(Path(__file__).resolve().parents[1]/"scripts"/"refresh_opportunity_research_registry.py").read_text()
 assert 'PREFIX="pattern-breakout/research/opportunity-cohorts"' in text
 assert '"status":"RESEARCH_ONLY"' in text
 assert '"eligibility_rule_defined":False' in text
 assert '"sufficient_for_threshold_selection":False' in text
 assert 'EVENT_PREFIX="pattern-breakout/production/breakout-events-v2/by-signal-date"' in text
