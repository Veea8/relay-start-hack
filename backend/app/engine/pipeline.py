# Script: pipeline.py
# Purpose: Decide one purchase by running every guard in order, timing each one and recording the whole decision
# Author: Andrés Gallardo
# Date: September 2026

import time
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

from app.engine.aggregate import aggregate
from app.engine.facts import build_fact_sheet
from app.engine.guards.base import DecisionInput
from app.engine.guards.registry import get_default_guard_pipeline
from app.models.decision import (
    DecisionTrace,
    EvidenceItem,
    GuardResult,
    GuardVerdict,
    ReasonCode,
    TraceAmounts,
    TraceFacts,
    TraceIdentifiers,
    TraceLanguageModel,
    TraceMerchant,
    TraceTimings,
)









#### Step 1: Read the clock and measure time ####

# Read the real clock in UTC, which a test replaces to fix the time
def read_utc_clock():
    return datetime.now(timezone.utc)



# Measure the milliseconds since a starting point of the performance counter
def measure_elapsed_ms(started_at):
    return round((time.perf_counter() - started_at) * 1000, 3)



# Measure the milliseconds left between the decision and the deadline, which is negative when the deadline has passed
def measure_margin_ms(deadline_at, decided_at):
    return (deadline_at - decided_at) / timedelta(milliseconds = 1)









#### Step 2: Copy the identifiers and the facts into the record ####

# Copy the five identifiers of the purchase into the record.
# This is the only place of the engine that names them, and nothing in the engine ever branches on an identifier.
def collect_trace_identifiers(event):
    return TraceIdentifiers(
        authorization_id = event.authorization.authorization_id,
        source_authorization_id = event.authorization.source_authorization_id,
        request_id = event.request_id,
        mandate_id = event.authorization.mandate_id,
        scenario_id = event.authorization.scenario_id,
    )



# Copy the amounts and the shop of the purchase into the record
def collect_trace_facts(event):
    return TraceFacts(
        amounts = TraceAmounts(
            amount = event.authorization.amount,
            currency = event.authorization.currency,
            billing_amount_chf = event.authorization.billing_amount_chf,
        ),
        merchant = TraceMerchant(
            merchant_id = event.authorization.merchant.merchant_id,
            merchant_name = event.authorization.merchant.merchant_name,
            merchant_category = event.authorization.merchant.merchant_category,
            merchant_country = event.authorization.merchant.merchant_country,
        ),
    )









#### Step 3: Run one guard safely ####

# Record a guard that failed as UNCERTAIN with one evidence item that says what went wrong
def build_guard_error_result(guard, evidence_fact, evidence_value):
    return GuardResult(
        guard_number = guard.guard_number,
        guard_id = guard.guard_id,
        family = guard.family,
        verdict = GuardVerdict.UNCERTAIN,
        reason_code = ReasonCode.GUARD_ERROR,
        evidence = [
            EvidenceItem(
                fact = evidence_fact,
                value = evidence_value,
                comparator = None,
                threshold = None,
                source = "engine",
            ),
        ],
    )



# Run one guard and time it, where any exception and any result under a foreign identity becomes a recorded failure
def run_one_guard(guard, decision_input, earlier_results):
    started_at = time.perf_counter()

    # Call the guard and catch whatever it raises, so one broken guard never stops the decision
    try:
        guard_result = guard.check(decision_input, earlier_results)
    except Exception as guard_exception:
        guard_result = build_guard_error_result(guard, "guard_exception_type", type(guard_exception).__name__)



    # Refuse an answer that is not a guard result or that carries the number or the id of another guard
    if not isinstance(guard_result, GuardResult):
        guard_result = build_guard_error_result(guard, "guard_returned_type", type(guard_result).__name__)
    elif guard_result.guard_number != guard.guard_number or guard_result.guard_id != guard.guard_id:
        guard_result = build_guard_error_result(guard, "guard_returned_identity", str(guard_result.guard_number) + " " + guard_result.guard_id)

    return guard_result.model_copy(update = {"elapsed_ms": measure_elapsed_ms(started_at)})









#### Step 4: Decide one purchase ####

# Decide one purchase and return the complete record, where every guard appears whatever happened.
# The clock is read for the received and decided moments, the margin and the timings only, and no guard sees it.
def decide(event, policy, state, guards = None, read_clock = None):

    # Fall back to the full pipeline, which is built once per process, and to the real clock
    if guards is None:
        guards = get_default_guard_pipeline()
    if read_clock is None:
        read_clock = read_utc_clock
    guard_ids = [guard.guard_id for guard in guards]
    assert len(set(guard_ids)) == len(guard_ids), "A guard id appears twice in the pipeline"



    # Note when the purchase arrived and start the timer of the whole decision
    received_at = read_clock()
    decision_started_at = time.perf_counter()



    # Build the fact sheet once and hand it to every guard, so all guards compare the same exact decimals.
    # A message whose facts cannot be built raises here, and the exception leaves this function unchanged.
    fact_sheet = build_fact_sheet(event)
    decision_input = DecisionInput(event = event, policy = policy, facts = fact_sheet, state = state)



    # Run the guards one after the other, because each guard receives the results of the guards before it.
    # Each guard receives a read-only copy, so it sees no later result and cannot change an earlier one.
    results_by_guard_id = {}
    for guard in guards:
        earlier_results = MappingProxyType(dict(results_by_guard_id))
        results_by_guard_id[guard.guard_id] = run_one_guard(guard, decision_input, earlier_results)
    guard_results = list(results_by_guard_id.values())



    # Combine the results into one decision under the customer's uncertainty policy
    aggregation_outcome = aggregate(guard_results, policy.uncertainty_policy)



    # Note when the decision was made and assemble the record
    decided_at = read_clock()
    return DecisionTrace(
        ids = collect_trace_identifiers(event),
        received_at = received_at,
        decided_at = decided_at,
        deadline_at = event.deadline_at,
        margin_ms = measure_margin_ms(event.deadline_at, decided_at),
        decision = aggregation_outcome.decision,
        reason_codes = aggregation_outcome.reason_codes,
        customer_message = aggregation_outcome.customer_message,
        notes = aggregation_outcome.notes,
        facts = collect_trace_facts(event),
        guards = guard_results,
        aggregation = aggregation_outcome.aggregation_record,
        llm = TraceLanguageModel(),
        timings = TraceTimings(total_ms = measure_elapsed_ms(decision_started_at)),
    )
