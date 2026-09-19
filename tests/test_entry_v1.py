from datetime import date

from pattern_breakout.entry_v1 import (
    EntryState, TECHNICAL_ELIGIBLE_STAGE,
    decide_pattern_breakout_t1_open, validate_pattern_breakout_entry,
)


def decide(open_price: float):
    return decide_pattern_breakout_t1_open(
        candidate_id="pb-1", security_id="XYZ",
        signal_date=date(2026, 9, 17),
        candidate_stage=TECHNICAL_ELIGIBLE_STAGE,
        pivot_level=100.0, next_session_date=date(2026, 9, 18),
        next_open=open_price,
    )


def test_executes_inside_five_percent_buy_zone():
    x = decide(102.0)
    assert x.entry_state == EntryState.EXECUTED_T1_OPEN
    assert x.fill_price == 102.0
    assert validate_pattern_breakout_entry(x) == []


def test_five_percent_boundary_is_executable():
    assert decide(105.0).entry_state == EntryState.EXECUTED_T1_OPEN


def test_above_five_percent_is_missed_extended():
    assert decide(105.01).entry_state == EntryState.MISSED_EXTENDED_AT_OPEN


def test_below_pivot_does_not_fill():
    assert decide(99.99).entry_state == EntryState.BELOW_PIVOT_AT_OPEN


def test_canslim_stage_alias_is_rejected():
    x = decide_pattern_breakout_t1_open(
        candidate_id="pb-2", security_id="XYZ",
        signal_date=date(2026, 9, 17), candidate_stage="CANSLIM_ELIGIBLE",
        pivot_level=100.0, next_session_date=date(2026, 9, 18), next_open=102.0)
    assert x.entry_state == EntryState.NOT_TECHNICAL_CANDIDATE
    assert x.fill_price is None


def test_no_max_hold_or_fundamental_inputs_exist():
    fields = set(decide(102.0).__dataclass_fields__)
    assert "max_hold" not in fields
    assert "C_state" not in fields
    assert "A_state" not in fields
    assert "fundamental_state" not in fields
