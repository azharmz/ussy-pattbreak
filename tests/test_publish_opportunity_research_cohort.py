import hashlib,importlib.util,json
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts"/"publish_opportunity_research_cohort.py"
S=importlib.util.spec_from_file_location("publish_opportunity_research_cohort",P)
M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

def test_contract_prefix_is_research_only():
    assert "/research/" in M.PREFIX
    assert "dashboard" not in M.PREFIX
