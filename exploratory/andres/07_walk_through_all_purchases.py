# Script: 07_walk_through_all_purchases.py
# Purpose: Lay the facts of all 45 scenario purchases next to their reasoned verdict, check the verdicts, and work the grocery budget through every customer answer
# Author: Andrés Gallardo
# Date: September 2026

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from console_output import save_printed_output

# Save everything this script prints into a text file next to it, so the results can be read without running it.
save_printed_output(__file__)

# Locate the case data and the verdict table relative to this file so the script runs from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FOLDER = PROJECT_ROOT / "data" / "raw" / "2026-09-18_viseca-2026" / "data"
VERDICT_FILE = PROJECT_ROOT / "data" / "processed" / "purchase_verdicts.csv"

# Widen the console output so wide tables print without being cut off.
pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 70)
pd.set_option("display.max_rows", 200)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {"scenario_id": str, "authorization_id": str, "merchant_id": str, "item_id": str}

LOCAL_TIME_ZONE = "Europe/Zurich"

# The order limit each customer states in the instruction, in francs, read from the scenario catalogue by hand.
ORDER_LIMIT_CHF = {"SCEN0000": 20, "SCEN0001": 120, "SCEN0002": 200, "SCEN0003": 250, "SCEN0004": 400}

# The rolling budget the grocery customer states in the instruction.
GROCERY_SCENARIO_ID = "SCEN0001"
GROCERY_PERIOD_LIMIT_CHF = 300
GROCERY_PERIOD_DAYS = 7

# An overshoot of a limit up to this share asks the customer, and a larger one declines.
OVERSHOOT_TOLERANCE_SHARE = 0.10



# Join the values of a column into one readable string, in their original order.
def join_values(values):
    return ", ".join(values)









#### Step 1: Load the purchases, their cart lines and the verdict table ####

# Read the scenario purchases with their local Swiss time and the order limit of their scenario.
purchase_attempts = (
    pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(
        timestamp_utc=lambda table: pd.to_datetime(table["timestamp"], utc=True),
        local_time=lambda table: table["timestamp_utc"].dt.tz_convert(LOCAL_TIME_ZONE).dt.strftime("%d %b %H.%M"),
        order_limit_chf=lambda table: table["scenario_id"].map(ORDER_LIMIT_CHF),
        is_over_order_limit=lambda table: table["billing_amount_chf"] > table["order_limit_chf"],
        is_large_overshoot=lambda table: table["billing_amount_chf"] > table["order_limit_chf"] * (1 + OVERSHOOT_TOLERANCE_SHARE),
        is_small_overshoot=lambda table: table["is_over_order_limit"] & ~table["is_large_overshoot"],
    )
)
purchase_attempt_items = pd.read_csv(DATA_FOLDER / "purchase_attempt_items.csv", dtype=IDENTIFIER_COLUMNS)
merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
purchase_verdicts = pd.read_csv(VERDICT_FILE, dtype=IDENTIFIER_COLUMNS)



# Check that the verdict table covers every purchase exactly once and uses only the agreed words.
assert len(purchase_verdicts) == 45, len(purchase_verdicts)
assert purchase_verdicts["authorization_id"].is_unique
assert set(purchase_verdicts["authorization_id"]) == set(purchase_attempts["authorization_id"])
assert set(purchase_verdicts["verdict"]) <= {"ordinary", "unwanted", "unclear"}
assert set(purchase_verdicts["decision_on_own_facts"]) <= {"approve", "decline", "step_up"}
assert set(purchase_verdicts["decision_in_sequence"]) <= {"approve", "decline", "step_up"}
print("--- Verdict table ---")
print(f"{len(purchase_verdicts)} purchases, each with one verdict")
print()



# Put the items of each purchase on one line and attach the merchant name and the verdict.
items_per_purchase = (
    purchase_attempt_items
    .groupby("authorization_id")
    .agg(items=("item_name", join_values))
    .reset_index()
)

purchase_walk = (
    purchase_attempts
    .merge(merchants[["merchant_id", "merchant_name"]], on="merchant_id", how="left")
    .merge(items_per_purchase, on="authorization_id", how="left")
    .merge(purchase_verdicts.drop(columns=["scenario_id", "replay_order"]), on="authorization_id", how="left")
    .sort_values(["scenario_id", "replay_order"])
)









#### Step 2: The walk through all purchases, one scenario at a time ####

# Print the facts and the verdict of every purchase in delivery order.
print("--- All purchases with their verdict ---")
print(
    purchase_walk
    [[
        "scenario_id", "replay_order", "authorization_id", "local_time", "billing_amount_chf", "order_limit_chf",
        "merchant_name", "items", "verdict", "problem_kind", "decision_on_own_facts", "decision_in_sequence",
    ]]
    .to_string(index=False)
)
print()









#### Step 3: Checks that the verdicts agree with the hard facts ####

# A large overshoot of the order limit must be a decline, a small one must ask, and no ordinary purchase may be over its limit.
assert (purchase_walk.query("is_large_overshoot")["decision_on_own_facts"] == "decline").all()
assert (purchase_walk.query("is_small_overshoot")["decision_on_own_facts"] == "step_up").all()
assert not purchase_walk.query("verdict == 'ordinary'")["is_over_order_limit"].any()

# An ordinary purchase is approved on its own facts, an unwanted one never is, and an unclear one always asks.
assert (purchase_walk.query("verdict == 'ordinary'")["decision_on_own_facts"] == "approve").all()
assert (purchase_walk.query("verdict == 'unwanted'")["decision_on_own_facts"] != "approve").all()
assert (purchase_walk.query("verdict == 'unclear'")["decision_on_own_facts"] == "step_up").all()

# Judging in sequence may only make a decision stricter, never looser.
severity = {"approve": 0, "step_up": 1, "decline": 2}
assert (purchase_walk["decision_in_sequence"].map(severity) >= purchase_walk["decision_on_own_facts"].map(severity)).all()
print("--- Checks passed ---")
print("large overshoots are declines, small overshoots ask, ordinary purchases are approvals, unclear purchases ask, sequence only tightens")
print()









#### Step 4: The grocery budget worked through every customer answer ####

# Take the grocery orders in time order as plain arrays, since each decision depends on the approvals before it.
grocery_orders = purchase_walk.query("scenario_id == @GROCERY_SCENARIO_ID").reset_index(drop=True)
grocery_times = grocery_orders["timestamp_utc"].to_numpy()
grocery_amounts = grocery_orders["billing_amount_chf"].to_numpy()
# Vary the customer answer for the two orders that are questionable for what they contain, and assume a decline for a small overshoot.
grocery_asks_customer = grocery_orders["problem_kind"].isin(["split_order", "off_purpose_item"]).to_numpy()
grocery_order_limit = ORDER_LIMIT_CHF[GROCERY_SCENARIO_ID]
grocery_window = np.timedelta64(GROCERY_PERIOD_DAYS, "D")



# Decide the ten grocery orders in sequence for one combination of customer answers.
def simulate_grocery_path(customer_answers):
    order_count = len(grocery_orders)
    is_approved = np.zeros(order_count, dtype=bool)
    total_before = np.zeros(order_count)
    outcome = np.full(order_count, "", dtype=object)
    answer_at_position = dict(zip(np.flatnonzero(grocery_asks_customer), customer_answers))

    for position in range(order_count):
        # Add up the approved orders inside the seven days before this order.
        is_in_window = is_approved & (grocery_times > grocery_times[position] - grocery_window) & (grocery_times < grocery_times[position])
        total_before[position] = round(grocery_amounts[is_in_window].sum(), 2)

        total_with_this_order = total_before[position] + grocery_amounts[position]

        if grocery_amounts[position] > grocery_order_limit * (1 + OVERSHOOT_TOLERANCE_SHARE):
            outcome[position] = "decline, over order limit"
        elif grocery_amounts[position] > grocery_order_limit:
            outcome[position] = "asked, small overshoot of order limit, assumed decline"
        elif total_with_this_order > GROCERY_PERIOD_LIMIT_CHF * (1 + OVERSHOOT_TOLERANCE_SHARE):
            outcome[position] = "decline, over 7-day limit"
        elif total_with_this_order > GROCERY_PERIOD_LIMIT_CHF:
            outcome[position] = "asked, small overshoot of 7-day limit, assumed decline"
        elif grocery_asks_customer[position]:
            outcome[position] = "asked, customer says " + answer_at_position[position]
            is_approved[position] = answer_at_position[position] == "approve"
        else:
            outcome[position] = "approve"
            is_approved[position] = True

    return grocery_orders[["replay_order", "authorization_id", "billing_amount_chf"]].assign(
        path="order 5 " + customer_answers[0] + ", order 6 " + customer_answers[1],
        seven_day_total_before=total_before,
        outcome=outcome,
    )



# Run all four combinations of answers to the two grocery questions and show the outcomes side by side.
possible_answers = list(product(["decline", "approve"], repeat=int(grocery_asks_customer.sum())))
all_grocery_paths = pd.concat([simulate_grocery_path(answers) for answers in possible_answers], ignore_index=True)

print("--- Grocery orders under every combination of customer answers, outcome ---")
print(all_grocery_paths.pivot(index=["replay_order", "billing_amount_chf"], columns="path", values="outcome").to_string())
print()

print("--- The same, seven-day total of approved orders just before each order ---")
print(all_grocery_paths.pivot(index=["replay_order", "billing_amount_chf"], columns="path", values="seven_day_total_before").to_string())
print()









#### Step 5: What the verdicts add up to ####

# Count the purchases per verdict and scenario.
print("--- Purchases per verdict and scenario ---")
print(pd.crosstab(purchase_walk["scenario_id"], purchase_walk["verdict"], margins=True).to_string())
print()

# Count the decisions under both ways of judging.
print("--- Decisions when every purchase is judged on its own facts ---")
print(purchase_walk["decision_on_own_facts"].value_counts().to_string())
print()
print("--- Decisions when one requested item means one item ---")
print(purchase_walk["decision_in_sequence"].value_counts().to_string())
print()

# List the purchases where the two ways of judging disagree.
print("--- Purchases where the two ways of judging disagree ---")
print(
    purchase_walk
    .query("decision_on_own_facts != decision_in_sequence")
    [["scenario_id", "replay_order", "authorization_id", "billing_amount_chf", "merchant_name", "decision_on_own_facts", "decision_in_sequence"]]
    .to_string(index=False)
)
print()

# Show how many of the purchases that need an intervention a plain order limit would catch.
needs_intervention = purchase_walk.query("verdict != 'ordinary'")
print("--- What a plain order limit catches ---")
print(f"purchases that need a decline or a question: {len(needs_intervention)} of {len(purchase_walk)}")
print(f"of those, over the order limit: {int(needs_intervention['is_over_order_limit'].sum())}")
print(needs_intervention["problem_kind"].value_counts().to_string())
print()
