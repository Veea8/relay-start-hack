# Script: compiler.py
# Purpose: Build the policy of the engine from the mandate that arrives inside a purchase message
# Author: Andrés Gallardo
# Date: September 2026

from decimal import Decimal

from app.config import get_settings
from app.models.policy import Expectations, InternalPolicy
from app.policyc.item_scope import read_item_scope
from app.policyc.order_limit import read_order_limit
from app.state.item_catalogue import get_default_item_catalogue









#### Step 1: Build the policy from a mandate ####

# Copy the instruction, the rules and the uncertainty policy, and read the limit per order and the kinds of goods from the instruction and the rules.
# Whatever a reader could not settle becomes an open question for the customer, and every other expectation stays at its default.
def build_policy_from_mandate(mandate, overshoot_tolerance_share = None, item_catalogue = None):

    # Take the tolerance from the settings when none is handed in, where a handed-in zero keeps every limit strictly hard
    if overshoot_tolerance_share is None:
        overshoot_tolerance_share = get_settings().overshoot_tolerance_share
    overshoot_tolerance_share = Decimal(str(overshoot_tolerance_share))



    # Take the catalogue that is loaded once per process when none is handed in
    if item_catalogue is None:
        item_catalogue = get_default_item_catalogue()



    # Read the limit per order and the kinds of goods without any model, so the policy is ready at once.
    # The open questions about the limit come first, then those about the goods.
    order_limit_reading = read_order_limit(mandate.instruction, mandate.hard_rules)
    item_scope_reading = read_item_scope(mandate.instruction, mandate.hard_rules, item_catalogue)
    return InternalPolicy(
        instruction = mandate.instruction,
        hard_rules = tuple(mandate.hard_rules),
        uncertainty_policy = mandate.uncertainty_policy,
        expectations = Expectations(
            per_order_limit_chf = order_limit_reading.limit_chf,
            per_order_limit_inclusive = order_limit_reading.inclusive,
            per_order_limit_reading = order_limit_reading.reading,
            overshoot_tolerance_share = overshoot_tolerance_share,
            allowed_item_categories = item_scope_reading.allowed_item_categories,
            prohibited_item_categories = item_scope_reading.prohibited_item_categories,
        ),
        open_questions = order_limit_reading.open_questions + item_scope_reading.open_questions,
    )
