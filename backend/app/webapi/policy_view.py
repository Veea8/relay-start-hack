# Script: policy_view.py
# Purpose: Show a compiled policy to the customer as the rules stored with the platform and the checks the engine adds, before anything is confirmed
# Author: Jonas Lüthi
# Date: September 2026

from app.models.events import MandateRule
from app.models.policy import InternalPolicy









#### Step 1: Build the rules stored with the platform ####

# Write the limit per order in the platform's rule format, which is the part of the policy the platform can store
def build_hard_rules_from_policy(policy):
    expectations = policy.expectations
    rules = [rule.model_dump(mode = "json", exclude_none = True) for rule in policy.hard_rules]
    if expectations.per_order_limit_reading == "read" and expectations.per_order_limit_chf is not None:
        limit_rule = {
            "field": "authorization.billing_amount_chf",
            "operator": "<=" if expectations.per_order_limit_inclusive else "<",
            "value": float(expectations.per_order_limit_chf),
            "currency": "CHF",
            "scope": "purchase",
        }
        if limit_rule not in rules:
            rules.append(limit_rule)
    return rules









#### Step 2: Build the check list ####

# Describe one check in plain words
def describe_check(label, detail, stored_with_platform):
    return {"label": label, "detail": detail, "stored_with_platform": stored_with_platform}



# Turn the policy into the two groups of checks the confirm screen shows
def build_check_list(policy):
    expectations = policy.expectations
    checks = []



    # Describe the limit per order, which is the one expectation the deterministic compiler reads today
    if expectations.per_order_limit_reading == "read":
        comparison = "at most" if expectations.per_order_limit_inclusive else "under"
        tolerance_percent = int(expectations.overshoot_tolerance_share * 100)
        detail = "Each order " + comparison + " CHF " + f"{expectations.per_order_limit_chf:.2f}" + ", delivery included."
        if tolerance_percent > 0:
            detail = detail + " Up to " + str(tolerance_percent) + " percent over asks you, more declines."
        else:
            detail = detail + " Any amount over declines."
        checks.append(describe_check("Limit per order", detail, True))
    elif expectations.per_order_limit_reading == "unclear":
        checks.append(describe_check("Limit per order", "Your instruction names a limit that could not be read. Every purchase asks you until it is settled.", False))
    else:
        checks.append(describe_check("Limit per order", "Your instruction names no limit per order.", False))



    # Describe how uncertainty is handled
    uncertainty_detail = {
        "ask": "When a check cannot be settled from the facts, the purchase asks you.",
        "decline": "When a check cannot be settled from the facts, the purchase is declined.",
        "approve": "When a check cannot be settled from the facts, the purchase goes ahead. A timeout still never approves.",
    }[policy.uncertainty_policy]
    checks.append(describe_check("When uncertain", uncertainty_detail, True))



    # Describe the checks the engine always runs
    checks.append(describe_check("Shop text is data", "Text from the shop can never loosen a decision. An attempt to instruct the agent asks you and is quoted.", False))
    checks.append(describe_check("One purchase, one decision", "A purchase delivered twice is decided once and counted once. A question counts only after you approve it.", False))
    return checks



# Describe the compiled policy for the interface, with the rules, the checks and the open questions
def describe_policy(policy):
    return {
        "instruction": policy.instruction,
        "uncertainty_policy": policy.uncertainty_policy,
        "hard_rules": build_hard_rules_from_policy(policy),
        "checks": build_check_list(policy),
        "open_questions": list(policy.open_questions),
        "expectations": policy.expectations.model_dump(mode = "json"),
    }









#### Step 3: Read a mandate from the interface ####

# Hold what the compiler needs of a mandate, which is the instruction, the rules and the uncertainty policy
class MandateContent:

    def __init__(self, instruction, hard_rules, uncertainty_policy):
        self.instruction = instruction
        self.hard_rules = tuple(MandateRule.model_validate(rule) for rule in hard_rules)
        self.uncertainty_policy = uncertainty_policy
