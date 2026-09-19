# Script: test_replay_events.py
# Purpose: Check that the offline replay builds valid live-shaped messages, keeps the state of a run and scores the two baselines and the engine as expected
# Author: Andrés Gallardo
# Date: September 2026

import itertools
import json
from decimal import Decimal

import pytest

import replay
from app.models.events import read_purchase_message









#### Step 1: Define the shared helpers and fixtures ####

# Answer step_up on every purchase, to exercise the simulated customer, without looking at the earlier purchases
def decide_always_step_up(event, earlier_purchases):
    return replay.ReplayDecision(
        decision = "step_up",
        reason_codes = ("STUB_STEP_UP",),
        customer_message = "Please review this purchase.",
    )



# Replay all scenarios with one decision function
def replay_all_scenarios(replay_tables, decide_purchase, resolve_mode = "ask"):
    return replay.replay_scenarios(
        replay_tables = replay_tables,
        scenario_ids = replay.list_scenario_ids(replay_tables),
        decide_purchase = decide_purchase,
        resolve_mode = resolve_mode,
    )



# Index the messages of a run by the source identifier of their purchase
def index_messages_by_source_id(purchase_results):
    return {
        purchase_result["record"]["source_authorization_id"]: purchase_result["message"]
        for purchase_result in purchase_results
    }



# List the source identifiers of the purchases with a given decision
def list_sources_with_decision(result_table, decision_name):
    return sorted(result_table.query("decision == @decision_name")["source_authorization_id"])



# Report whether every message of a scenario carries the exact sum of the earlier purchases of that scenario
def spend_grows_purchase_by_purchase(purchase_results, scenario_id):
    scenario_results = [purchase_result for purchase_result in purchase_results if purchase_result["record"]["scenario_id"] == scenario_id]
    scenario_amounts = [Decimal(str(purchase_result["record"]["billing_amount_chf"])) for purchase_result in scenario_results]
    running_totals = list(itertools.accumulate(scenario_amounts, initial = Decimal("0")))
    expected_spend_values = [float(running_total) for running_total in running_totals[:-1]]
    observed_spend_values = [purchase_result["message"]["context"]["approved_spend_in_period_chf"] for purchase_result in scenario_results]
    return observed_spend_values == expected_spend_values



# Load the published tables once for all tests
@pytest.fixture(scope = "module")
def replay_tables():
    return replay.load_replay_tables()



# Replay all scenarios once with the baseline that approves everything
@pytest.fixture(scope = "module")
def results_without_control(replay_tables):
    return replay_all_scenarios(replay_tables, replay.choose_decision_function("none"))



# Replay all scenarios once with the baseline that only checks the order limit
@pytest.fixture(scope = "module")
def results_with_limit_only(replay_tables):
    return replay_all_scenarios(replay_tables, replay.choose_decision_function("limit_only"))



# Replay all scenarios once with the engine, which decides when no baseline is named
@pytest.fixture(scope = "module")
def results_with_engine(replay_tables):
    return replay_all_scenarios(replay_tables, replay.choose_decision_function())









#### Step 2: Check the built messages ####

# Check that all 45 messages build and pass the published schema and the strict reader
def test_all_messages_build_and_pass_both_validators(results_without_control, event_schema_validator):
    assert len(results_without_control) == 45
    schema_problem_counts = [
        len(list(event_schema_validator.iter_errors(purchase_result["message"])))
        for purchase_result in results_without_control
    ]
    assert schema_problem_counts == [0] * 45
    typed_events = [read_purchase_message(purchase_result["message"]) for purchase_result in results_without_control]
    assert len(typed_events) == 45



# Check the value types of the connection check purchase field by field
def test_first_purchase_keeps_the_live_value_types(results_without_control):
    authorization = index_messages_by_source_id(results_without_control)["AU0001"]["authorization"]
    assert authorization["amount"] == 20.0
    assert isinstance(authorization["amount"], float)
    assert authorization["merchant"]["merchant_mcc"] == "5411"
    assert authorization["merchant"]["recurring_capable"] == "false"
    assert authorization["order_returnable"] == "false"
    assert authorization["spend_in_period_before_chf"] is None
    assert authorization["delivery_by"] == "2026-08-10"
    assert isinstance(authorization["replay_order"], int)
    assert isinstance(authorization["items"][0]["quantity"], int)
    assert isinstance(authorization["items"][0]["unit_price"], float)



# Check that an empty delivery date becomes None on exactly 34 messages
def test_delivery_date_is_none_on_exactly_34_messages(results_without_control):
    messages_without_delivery_date = [
        purchase_result
        for purchase_result in results_without_control
        if purchase_result["message"]["authorization"]["delivery_by"] is None
    ]
    assert len(messages_without_delivery_date) == 34



# Check that the rebuilt list of recent purchases agrees with the published count on every message
def test_recent_authorizations_match_the_published_count(results_without_control):
    disagreeing_sources = [
        purchase_result["record"]["source_authorization_id"]
        for purchase_result in results_without_control
        if len(purchase_result["message"]["context"]["recent_authorizations"]) != purchase_result["message"]["authorization"]["recent_attempt_count_10m"]
    ]
    assert disagreeing_sources == []



# Check that the mandate and the authorization carry the same local identifiers
def test_mandate_and_authorization_share_their_identifiers(results_without_control):
    disagreeing_sources = [
        purchase_result["record"]["source_authorization_id"]
        for purchase_result in results_without_control
        if purchase_result["message"]["authorization"]["mandate_id"] != purchase_result["message"]["mandate"]["mandate_id"]
        or purchase_result["message"]["authorization"]["profile_id"] != purchase_result["message"]["mandate"]["profile_id"]
    ]
    assert disagreeing_sources == []



# Check that the one related purchase points to a live identifier and not to the source text
def test_related_purchase_points_to_the_live_identifier(results_without_control):
    messages_by_source_id = index_messages_by_source_id(results_without_control)
    sources_with_a_related_purchase = [
        source_authorization_id
        for source_authorization_id, message in messages_by_source_id.items()
        if message["authorization"]["related_authorization_id"] is not None
    ]
    assert sources_with_a_related_purchase == ["AU0042"]
    related_live_id = messages_by_source_id["AU0042"]["authorization"]["related_authorization_id"]
    assert related_live_id == messages_by_source_id["AU0037"]["authorization"]["authorization_id"]
    assert related_live_id != "AU0037"
    assert messages_by_source_id["AU0042"]["authorization"]["related_authorization_status"] == "declined"



# Check that two runs differ in their live identifiers and agree in everything the files state
def test_two_runs_differ_only_in_their_live_identifiers(replay_tables):
    first_run = replay_all_scenarios(replay_tables, replay.choose_decision_function("none"))
    second_run = replay_all_scenarios(replay_tables, replay.choose_decision_function("none"))
    first_live_ids = {purchase_result["record"]["authorization_id"] for purchase_result in first_run}
    second_live_ids = {purchase_result["record"]["authorization_id"] for purchase_result in second_run}
    assert len(first_live_ids) == 45
    assert len(second_live_ids) == 45
    assert first_live_ids.isdisjoint(second_live_ids)

    stable_facts_of_first_run = [
        (
            purchase_result["message"]["authorization"]["source_authorization_id"],
            purchase_result["message"]["authorization"]["amount"],
            purchase_result["message"]["authorization"]["billing_amount_chf"],
            purchase_result["message"]["authorization"]["timestamp"],
        )
        for purchase_result in first_run
    ]
    stable_facts_of_second_run = [
        (
            purchase_result["message"]["authorization"]["source_authorization_id"],
            purchase_result["message"]["authorization"]["amount"],
            purchase_result["message"]["authorization"]["billing_amount_chf"],
            purchase_result["message"]["authorization"]["timestamp"],
        )
        for purchase_result in second_run
    ]
    assert stable_facts_of_first_run == stable_facts_of_second_run









#### Step 3: Check the two baselines ####

# Check that the baseline without control approves all 45 purchases
def test_baseline_without_control_approves_everything(results_without_control):
    result_table = replay.build_result_table(results_without_control)
    summary = replay.summarize_replay(result_table)
    assert list_sources_with_decision(result_table, "approve") == sorted(result_table["source_authorization_id"])
    assert (result_table["final_status"] == "approved").all()
    assert result_table["reason_codes"].tolist() == [["NO_CONTROL"]] * 45
    assert summary["total_approved_chf"] == Decimal("8925.73")
    assert summary["total_all_chf"] == Decimal("8925.73")
    assert summary["total_declined_or_pending_chf"] == Decimal("0.00")



# Check that the limit baseline declines exactly the six purchases above their order limit
def test_limit_baseline_declines_exactly_the_purchases_above_the_limit(results_with_limit_only):
    result_table = replay.build_result_table(results_with_limit_only)
    summary = replay.summarize_replay(result_table)
    assert list_sources_with_decision(result_table, "decline") == ["AU0004", "AU0010", "AU0021", "AU0034", "AU0037", "AU0041"]
    assert list_sources_with_decision(result_table, "step_up") == []
    assert summary["total_declined_or_pending_chf"] == Decimal("1726.00")
    declined_reason_codes = result_table.query("decision == 'decline'")["reason_codes"].tolist()
    assert declined_reason_codes == [["OVER_ORDER_LIMIT"]] * 6



# Check that a purchase at exactly its order limit is approved
def test_limit_baseline_approves_a_purchase_at_exactly_the_limit(results_with_limit_only):
    decisions_by_source_id = (
        replay.build_result_table(results_with_limit_only)
        .set_index("source_authorization_id")
        .loc[:, "decision"]
    )
    messages_by_source_id = index_messages_by_source_id(results_with_limit_only)
    assert messages_by_source_id["AU0001"]["authorization"]["billing_amount_chf"] == 20.0
    assert messages_by_source_id["AU0003"]["authorization"]["billing_amount_chf"] == 120.0
    assert decisions_by_source_id["AU0001"] == "approve"
    assert decisions_by_source_id["AU0003"] == "approve"



# Check that the order limit is read correctly from each of the five public instructions
def test_order_limit_is_read_from_the_five_public_instructions(replay_tables):
    instructions_by_scenario_id = (
        replay_tables.joined_attempts
        .drop_duplicates(subset = ["scenario_id"])
        .set_index("scenario_id")
        .loc[:, "cardholder_instruction"]
    )
    order_limits_by_scenario_id = {
        scenario_id: replay.read_order_limit_for_baseline(instruction)
        for scenario_id, instruction in instructions_by_scenario_id.items()
    }
    assert order_limits_by_scenario_id == {
        "SCEN0000": Decimal("20"),
        "SCEN0001": Decimal("120"),
        "SCEN0002": Decimal("200"),
        "SCEN0003": Decimal("250"),
        "SCEN0004": Decimal("400"),
    }



# Check that a sentence without an amount raises a clear error
def test_order_limit_raises_on_a_sentence_without_an_amount():
    with pytest.raises(ValueError, match = "no amount"):
        replay.read_order_limit_for_baseline("Buy whatever seems reasonable. Ask me when uncertain.")









#### Step 4: Check the engine ####

# Check that the engine is chosen exactly when no baseline is named
def test_engine_decides_when_no_baseline_is_named():
    assert replay.choose_decision_function() is replay.decide_with_engine
    assert replay.choose_decision_function(None) is replay.decide_with_engine
    assert replay.choose_decision_function("none") is replay.decide_with_no_control
    assert replay.parse_command_line(["--all"]).baseline is None
    assert replay.parse_command_line(["--all", "--baseline", "limit_only"]).baseline == "limit_only"



# Check that the engine asks and declines on the order limit, the budget, a split order, the kind of goods, the extras, the kind of shop,
# the requested item and the return terms, and approves the rest.
# Three small overshoots of the order limit, one of the budget, three orders that look split in two, two carts with an extra line outside the instruction
# and one order whose shop does not state its return policy ask.
# Three large overshoots, one shop of the wrong kind, one cart with nothing the customer asked for, shoes in the wrong size, trail-running shoes,
# a helmet, a final sale and a return period of 7 days decline.
def test_engine_asks_and_declines_on_limits_budget_split_orders_goods_extras_and_the_kind_of_shop(results_with_engine):
    result_table = replay.build_result_table(results_with_engine)
    summary = replay.summarize_replay(result_table)
    assert len(result_table) == 45
    assert len(list_sources_with_decision(result_table, "approve")) == 25
    assert list_sources_with_decision(result_table, "step_up") == ["AU0004", "AU0006", "AU0007", "AU0009", "AU0016", "AU0018", "AU0021", "AU0030", "AU0034", "AU0036"]
    assert list_sources_with_decision(result_table, "decline") == ["AU0010", "AU0013", "AU0014", "AU0015", "AU0017", "AU0020", "AU0022", "AU0037", "AU0041", "AU0043"]
    assert "trace" not in result_table.columns
    assert replay.count_guards_not_built() == (14, 23)

    # Expect the reasons of each decision, the strictest first, and no reason on an approval
    reason_codes_by_source_id = dict(zip(result_table["source_authorization_id"], result_table["reason_codes"]))
    assert result_table.query("decision == 'approve'")["reason_codes"].tolist() == [[]] * 25
    assert {source_id: reason_codes for source_id, reason_codes in reason_codes_by_source_id.items() if reason_codes != []} == {
        "AU0004": ["SMALL_OVERSHOOT"],
        "AU0006": ["SPLIT_ORDER_SUSPECTED"],
        "AU0007": ["OFF_SCOPE_ITEM", "UNREQUESTED_ADDON"],
        "AU0009": ["SMALL_OVERSHOOT"],
        "AU0010": ["OVER_PER_ORDER_LIMIT", "OVER_PERIOD_LIMIT"],
        "AU0013": ["ITEM_MISMATCH"],
        "AU0014": ["RETURN_TERMS_UNMET"],
        "AU0015": ["RETURN_TERMS_UNMET"],
        "AU0016": ["RETURN_TERMS_UNKNOWN"],
        "AU0017": ["ITEM_MISMATCH"],
        "AU0018": ["OFF_SCOPE_ITEM", "UNREQUESTED_ADDON", "ITEM_SHOP_MISMATCH"],
        "AU0020": ["ITEM_MISMATCH"],
        "AU0021": ["SMALL_OVERSHOOT"],
        "AU0022": ["MERCHANT_TYPE_MISMATCH"],
        "AU0030": ["SPLIT_ORDER_SUSPECTED"],
        "AU0034": ["SMALL_OVERSHOOT"],
        "AU0036": ["SPLIT_ORDER_SUSPECTED"],
        "AU0037": ["OVER_PER_ORDER_LIMIT"],
        "AU0041": ["OVER_PER_ORDER_LIMIT", "UNREQUESTED_ADDON", "OFF_SCOPE_ITEM", "ITEM_SHOP_MISMATCH"],
        "AU0043": ["OFF_SCOPE_ITEM", "ITEM_MISMATCH"],
    }

    # Expect an unanswered question to stay pending, so its amount counts as not approved
    assert (result_table.query("decision == 'approve'")["final_status"] == "approved").all()
    assert (result_table.query("decision == 'step_up'")["final_status"] == "pending").all()
    assert (result_table.query("decision == 'decline'")["final_status"] == "declined").all()
    assert summary["total_approved_chf"] == Decimal("5000.73")
    assert summary["total_declined_or_pending_chf"] == Decimal("3925.00")



# Check that every record of an engine run carries a full decision record with 23 guards and the identifiers of its purchase
def test_every_engine_record_carries_a_trace_with_23_guards(results_with_engine):
    records = [purchase_result["record"] for purchase_result in results_with_engine]
    guard_counts = [len(record["trace"]["guards"]) for record in records]
    assert guard_counts == [23] * 45
    disagreeing_sources = [
        record["source_authorization_id"]
        for record in records
        if record["trace"]["ids"]["authorization_id"] != record["authorization_id"]
        or record["trace"]["ids"]["source_authorization_id"] != record["source_authorization_id"]
        or record["trace"]["decision"] != record["decision"]
    ]
    assert disagreeing_sources == []
    assert json.loads(json.dumps(records[0]["trace"])) == records[0]["trace"]



# Check that a baseline record carries no decision record
def test_baseline_records_carry_no_trace(results_with_limit_only):
    records_with_a_trace = [purchase_result["record"]["source_authorization_id"] for purchase_result in results_with_limit_only if "trace" in purchase_result["record"]]
    assert records_with_a_trace == []



# Check that the engine builds one policy per mandate, which means one per scenario run
def test_engine_builds_one_policy_per_mandate(results_with_engine):
    mandate_ids_of_the_run = {purchase_result["message"]["mandate"]["mandate_id"] for purchase_result in results_with_engine}
    assert len(mandate_ids_of_the_run) == 5
    assert mandate_ids_of_the_run <= set(replay.POLICIES_BY_MANDATE_ID)









#### Step 5: Check the state of the run and the simulated customer ####

# Check that an unanswered step_up stays pending and never counts as approved spend
def test_unanswered_step_up_stays_pending_and_adds_no_spend(replay_tables):
    purchase_results = replay_all_scenarios(replay_tables, decide_always_step_up, resolve_mode = "ask")
    result_table = replay.build_result_table(purchase_results)
    assert (result_table["decision"] == "step_up").all()
    assert (result_table["final_status"] == "pending").all()
    approved_spend_values = [purchase_result["message"]["context"]["approved_spend_in_period_chf"] for purchase_result in purchase_results]
    assert approved_spend_values == [0.0] * 45
    recent_statuses = [
        recent_authorization["status"]
        for purchase_result in purchase_results
        for recent_authorization in purchase_result["message"]["context"]["recent_authorizations"]
    ]
    assert len(recent_statuses) > 0
    assert set(recent_statuses) == {"pending"}
    assert replay.summarize_replay(result_table)["total_approved_chf"] == Decimal("0.00")



# Check that a step_up answered with approve grows the approved spend purchase by purchase
def test_approved_step_up_grows_the_spend_purchase_by_purchase(replay_tables):
    purchase_results = replay_all_scenarios(replay_tables, decide_always_step_up, resolve_mode = "approve")
    result_table = replay.build_result_table(purchase_results)
    assert (result_table["decision"] == "step_up").all()
    assert (result_table["final_status"] == "approved").all()

    # Expect each message to carry the exact sum of the earlier purchases of its own scenario
    disagreeing_scenarios = [
        scenario_id
        for scenario_id in replay.list_scenario_ids(replay_tables)
        if not spend_grows_purchase_by_purchase(purchase_results, scenario_id)
    ]
    assert disagreeing_scenarios == []

    # Expect the spend to actually grow, from zero on the first purchase of a scenario to more on its last
    household_results = [purchase_result for purchase_result in purchase_results if purchase_result["record"]["scenario_id"] == "SCEN0001"]
    assert household_results[0]["message"]["context"]["approved_spend_in_period_chf"] == 0.0
    assert household_results[1]["message"]["context"]["approved_spend_in_period_chf"] == 44.5
    assert household_results[-1]["message"]["context"]["approved_spend_in_period_chf"] == 715.0



# Check that a step_up answered with decline keeps both the engine decision and the final status
def test_declined_step_up_keeps_decision_and_final_status(replay_tables):
    purchase_results = replay_all_scenarios(replay_tables, decide_always_step_up, resolve_mode = "decline")
    result_table = replay.build_result_table(purchase_results)
    assert (result_table["decision"] == "step_up").all()
    assert (result_table["final_status"] == "declined").all()









#### Step 6: Check the comparison and the files ####

# Check the number of matches of each baseline against the reference decisions
def test_comparison_counts_the_matches_of_both_baselines(results_without_control, results_with_limit_only):
    compared_without_control = replay.compare_with_reference_decisions(replay.build_result_table(results_without_control))
    compared_with_limit_only = replay.compare_with_reference_decisions(replay.build_result_table(results_with_limit_only))
    assert len(compared_without_control) == 45
    assert len(compared_with_limit_only) == 45
    assert int((compared_without_control["decision_match"] == "match").sum()) == 17
    assert int((compared_with_limit_only["decision_match"] == "match").sum()) == 20
    decision_position = list(compared_with_limit_only.columns).index("decision")
    assert list(compared_with_limit_only.columns)[decision_position:decision_position + 3] == ["decision", "decision_on_own_facts", "decision_match"]



# Check that the engine matches 36 of 45 reference decisions with its nine built guards
def test_comparison_counts_the_matches_of_the_engine(results_with_engine):
    compared_with_engine = replay.compare_with_reference_decisions(replay.build_result_table(results_with_engine))
    assert len(compared_with_engine) == 45
    assert int((compared_with_engine["decision_match"] == "match").sum()) == 36



# Check that the reference file is named only inside the comparison function of the replay script
def test_reference_file_is_named_only_inside_the_comparison_function():
    script_lines = (replay.REPOSITORY_FOLDER / "scripts" / "replay.py").read_text(encoding = "utf-8").splitlines()
    function_start = script_lines.index("def compare_with_reference_decisions(result_table, reference_path = None):")
    lines_after_start = list(enumerate(script_lines))[function_start + 1:]
    function_end = next(
        line_number
        for line_number, line_text in lines_after_start
        if line_text.strip() != "" and not line_text.startswith(" ")
    )
    lines_naming_the_reference_file = [
        line_number
        for line_number, line_text in enumerate(script_lines)
        if "purchase_verdicts" in line_text.lower()
    ]
    assert len(lines_naming_the_reference_file) > 0
    assert all(function_start < line_number < function_end for line_number in lines_naming_the_reference_file)



# Check that a command line run writes its two files into the given folder and nowhere else
def test_command_line_run_writes_both_files(tmp_path, capsys):
    result_table = replay.main(["--scenario", "SCEN0001", "--baseline", "limit_only", "--compare"], output_folder = tmp_path)
    written_names = sorted(written_path.name for written_path in tmp_path.iterdir())
    assert len(result_table) == 10
    assert len(written_names) == 2
    assert written_names[0].startswith("SCEN0001_limit_only_") and written_names[0].endswith(".jsonl")
    assert written_names[1].startswith("SCEN0001_limit_only_") and written_names[1].endswith(".md")
    purchase_lines = (tmp_path / written_names[0]).read_text(encoding = "utf-8").splitlines()
    assert len(purchase_lines) == 10
    printed_summary = capsys.readouterr().out
    assert "matches" in printed_summary
    assert "baseline limit_only" in printed_summary
    assert "Guards not built yet" not in printed_summary



# Check that a command line run without a baseline lets the engine decide and names its files after the engine
def test_command_line_run_without_baseline_uses_the_engine(tmp_path, capsys):
    result_table = replay.main(["--scenario", "SCEN0001", "--compare"], output_folder = tmp_path)
    written_names = sorted(written_path.name for written_path in tmp_path.iterdir())
    assert len(result_table) == 10
    assert len(list_sources_with_decision(result_table, "approve")) == 5
    assert list_sources_with_decision(result_table, "step_up") == ["AU0004", "AU0006", "AU0007", "AU0009"]
    assert list_sources_with_decision(result_table, "decline") == ["AU0010"]
    assert len(written_names) == 2
    assert written_names[0].startswith("SCEN0001_engine_") and written_names[0].endswith(".jsonl")
    assert written_names[1].startswith("SCEN0001_engine_") and written_names[1].endswith(".md")

    # Expect every line of the purchase file to carry the full decision record
    purchase_lines = (tmp_path / written_names[0]).read_text(encoding = "utf-8").splitlines()
    guard_counts = [len(json.loads(purchase_line)["record"]["trace"]["guards"]) for purchase_line in purchase_lines]
    assert guard_counts == [23] * 10

    # Expect the line about the guards in the printed summary and in the markdown report, and no trace column in the report
    printed_summary = capsys.readouterr().out
    markdown_report = (tmp_path / written_names[1]).read_text(encoding = "utf-8")
    assert "Guards not built yet - 14 of 23" in printed_summary
    assert "Guards not built yet - 14 of 23" in markdown_report
    assert "trace_version" not in markdown_report
