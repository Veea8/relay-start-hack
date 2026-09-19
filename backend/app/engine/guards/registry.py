# Script: registry.py
# Purpose: List the 23 guards with their number, id and family, and build them in the order the pipeline runs them
# Author: Andrés Gallardo
# Date: September 2026

from dataclasses import dataclass

from app.engine.guards.base import PlaceholderGuard
from app.models.decision import GuardFamily









#### Step 1: List the 23 guards ####

# Describe one row of the guard table
@dataclass(frozen = True)
class GuardTableRow:
    guard_number: int
    guard_id: str
    family: GuardFamily



# State how many guards the pipeline has
EXPECTED_GUARD_COUNT = 23



# List every guard once, grouped by the family the customer sees on screen
GUARD_TABLE = (
    GuardTableRow(1, "authority", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(2, "arithmetic_integrity", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(3, "per_order_limit", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(4, "period_budget", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(5, "split_order", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(20, "issuer_settings", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(23, "price_against_last_time", GuardFamily.SPENDING_LIMITS),
    GuardTableRow(6, "category_scope", GuardFamily.ITEM_AND_TERMS),
    GuardTableRow(7, "addon", GuardFamily.ITEM_AND_TERMS),
    GuardTableRow(18, "item_match", GuardFamily.ITEM_AND_TERMS),
    GuardTableRow(19, "order_terms", GuardFamily.ITEM_AND_TERMS),
    GuardTableRow(21, "item_shop_consistency", GuardFamily.ITEM_AND_TERMS),
    GuardTableRow(8, "merchant_type", GuardFamily.SELLER),
    GuardTableRow(9, "lookalike_merchant", GuardFamily.SELLER),
    GuardTableRow(10, "merchant_familiarity", GuardFamily.SELLER),
    GuardTableRow(11, "device", GuardFamily.SESSION),
    GuardTableRow(12, "velocity", GuardFamily.SESSION),
    GuardTableRow(13, "geo", GuardFamily.SESSION),
    GuardTableRow(14, "session_integrity", GuardFamily.SESSION),
    GuardTableRow(22, "usual_purchase_pattern", GuardFamily.SESSION),
    GuardTableRow(15, "duplicate_order", GuardFamily.REPEATS_AND_MANIPULATION),
    GuardTableRow(16, "goal_fulfilled", GuardFamily.REPEATS_AND_MANIPULATION),
    GuardTableRow(17, "injection", GuardFamily.REPEATS_AND_MANIPULATION),
)



# State the order in which the guards run.
# Guard 22 runs before guard 14, because guard 14 combines the signals of guards 10 to 13 and 22.
EXECUTION_ORDER = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 22, 14, 15, 16, 17, 18, 19, 20, 21, 23)









#### Step 2: Build the pipeline ####

# Build the 23 guards in execution order, where every guard is still a placeholder
def build_guard_pipeline():

    # Check the table, which must hold 23 guards with the numbers 1 to 23 and no id twice
    guard_numbers = [table_row.guard_number for table_row in GUARD_TABLE]
    guard_ids = [table_row.guard_id for table_row in GUARD_TABLE]
    assert len(GUARD_TABLE) == EXPECTED_GUARD_COUNT, "Expected 23 guards, found " + str(len(GUARD_TABLE))
    assert sorted(guard_numbers) == list(range(1, EXPECTED_GUARD_COUNT + 1)), "The guard numbers must be 1 to 23, each exactly once"
    assert len(set(guard_ids)) == EXPECTED_GUARD_COUNT, "A guard id appears twice"
    assert sorted(EXECUTION_ORDER) == sorted(guard_numbers), "The execution order must name every guard exactly once"



    # Build one guard per table row and put the guards in execution order
    table_rows_by_number = {table_row.guard_number: table_row for table_row in GUARD_TABLE}
    return [
        PlaceholderGuard(
            guard_number = table_rows_by_number[guard_number].guard_number,
            guard_id = table_rows_by_number[guard_number].guard_id,
            family = table_rows_by_number[guard_number].family,
        )
        for guard_number in EXECUTION_ORDER
    ]



# List the ids of the guards that are still placeholders, in execution order
def list_placeholder_guard_ids(guards):
    return [guard.guard_id for guard in guards if isinstance(guard, PlaceholderGuard)]
