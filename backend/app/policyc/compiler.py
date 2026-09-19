# Script: compiler.py
# Purpose: Build the policy of the engine from the mandate that arrives inside a purchase message
# Author: Andrés Gallardo
# Date: September 2026

from app.models.policy import Expectations, InternalPolicy









#### Step 1: Build the policy from a mandate ####

# Copy the instruction, the rules and the uncertainty policy, and leave every expectation at its default.
# Reading the instruction text is added later, so for now the policy expects nothing beyond the mandate itself.
def build_policy_from_mandate(mandate):
    return InternalPolicy(
        instruction = mandate.instruction,
        hard_rules = tuple(mandate.hard_rules),
        uncertainty_policy = mandate.uncertainty_policy,
        expectations = Expectations(),
        open_questions = (),
    )
