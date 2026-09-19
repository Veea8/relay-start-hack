# Script: compiler.py
# Purpose: Build the policy of the engine from the mandate that arrives inside a purchase message
# Author: Andrés Gallardo
# Date: September 2026

from decimal import Decimal

from app.config import get_settings
from app.models.policy import Expectations, InternalPolicy
from app.policyc.order_limit import read_order_limit









#### Step 1: Build the policy from a mandate ####

# Copy the instruction, the rules and the uncertainty policy, and read the limit per order from the instruction and the rules.
# Whatever the reader could not settle becomes an open question for the customer, and every other expectation stays at its default.
def build_policy_from_mandate(mandate, overshoot_tolerance_share = None):

    # Take the tolerance from the settings when none is handed in, where a handed-in zero keeps every limit strictly hard
    if overshoot_tolerance_share is None:
        overshoot_tolerance_share = get_settings().overshoot_tolerance_share
    overshoot_tolerance_share = Decimal(str(overshoot_tolerance_share))



    # Read the limit per order without any model, so the policy is ready at once
    order_limit_reading = read_order_limit(mandate.instruction, mandate.hard_rules)
    return InternalPolicy(
        instruction = mandate.instruction,
        hard_rules = tuple(mandate.hard_rules),
        uncertainty_policy = mandate.uncertainty_policy,
        expectations = Expectations(
            per_order_limit_chf = order_limit_reading.limit_chf,
            per_order_limit_inclusive = order_limit_reading.inclusive,
            per_order_limit_reading = order_limit_reading.reading,
            overshoot_tolerance_share = overshoot_tolerance_share,
        ),
        open_questions = order_limit_reading.open_questions,
    )
