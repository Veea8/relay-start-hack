# Script: 03_what_normal_looks_like.py
# Purpose: Measure the normal hours, amounts, countries, merchant novelty and purchase speed of each customer, and place every scenario purchase against that normal
# Author: Andrés Gallardo
# Date: September 2026

from pathlib import Path

import pandas as pd

from console_output import save_printed_output

# Save everything this script prints into a text file next to it, so the results can be read without running it.
save_printed_output(__file__)

# Locate the case data relative to this file so the script runs from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FOLDER = PROJECT_ROOT / "data" / "raw" / "2026-09-18_viseca-2026" / "data"

# Widen the console output so wide tables print without being cut off.
pd.set_option("display.width", 300)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_rows", 200)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {
    "scenario_id": str, "authority_id": str, "authorization_id": str, "customer_id": str,
    "account_id": str, "card_id": str, "merchant_id": str, "customer_device_id": str,
}

# Count a purchase as made at night when the local Swiss hour is before this hour.
NIGHT_ENDS_AT_LOCAL_HOUR = 5
LOCAL_TIME_ZONE = "Europe/Zurich"



# Return the 95th percentile of a column of amounts.
def percentile_95(values):
    return values.quantile(0.95)









#### Step 1: Load the history and the scenario purchases ####

# Read both tables and add the local Swiss hour, since the timestamps are stored in UTC.
authorization_history = (
    pd.read_csv(DATA_FOLDER / "authorization_history.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(
        timestamp_utc=lambda table: pd.to_datetime(table["timestamp"], utc=True),
        local_hour=lambda table: table["timestamp_utc"].dt.tz_convert(LOCAL_TIME_ZONE).dt.hour,
        is_night=lambda table: table["local_hour"] < NIGHT_ENDS_AT_LOCAL_HOUR,
        is_foreign=lambda table: table["merchant_country"] != "CH",
        is_first_time_merchant=lambda table: table["approved_merchant_transaction_count_before"] == 0,
        is_agent=lambda table: table["initiator_type"] == "agent",
    )
)

purchase_attempts = (
    pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(
        timestamp_utc=lambda table: pd.to_datetime(table["timestamp"], utc=True),
        local_hour=lambda table: table["timestamp_utc"].dt.tz_convert(LOCAL_TIME_ZONE).dt.hour,
    )
)

merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
customers = pd.read_csv(DATA_FOLDER / "customers.csv", dtype=IDENTIFIER_COLUMNS)

assert len(authorization_history) == 4701, len(authorization_history)
assert authorization_history["timestamp_utc"].notna().all()
print("--- History window ---")
print(authorization_history["timestamp_utc"].min(), "to", authorization_history["timestamp_utc"].max())
print()



# Keep the approved purchases a person or an agent actively made, leaving out scheduled recurring payments, cash and refunds.
active_purchases = authorization_history.query(
    "status == 'approved' and transaction_type == 'purchase' and channel != 'recurring'"
)
print("--- Approved, actively made purchases ---")
print(f"{len(active_purchases)} of {len(authorization_history)} history rows")
print()









#### Step 2: How different the twenty customers are from each other ####

# Summarize each customer's normal behavior in one row, next to the budget style from the profile.
last_90_days_start = authorization_history["timestamp_utc"].max() - pd.Timedelta(days=90)

customer_normal = (
    active_purchases
    .assign(
        is_recent_first_time_merchant=lambda table: table["is_first_time_merchant"] & (table["timestamp_utc"] >= last_90_days_start),
        is_recent=lambda table: table["timestamp_utc"] >= last_90_days_start,
    )
    .groupby("customer_id")
    .agg(
        purchases=("authorization_id", "count"),
        night_share=("is_night", "mean"),
        foreign_share=("is_foreign", "mean"),
        agent_share=("is_agent", "mean"),
        distinct_merchants=("merchant_id", "nunique"),
        recent_purchases=("is_recent", "sum"),
        recent_first_time_merchants=("is_recent_first_time_merchant", "sum"),
        median_chf=("billing_amount_chf", "median"),
        p95_chf=("billing_amount_chf", percentile_95),
        max_chf=("billing_amount_chf", "max"),
    )
    .reset_index()
    .merge(customers[["customer_id", "persona_name", "budget_style"]], on="customer_id", how="left")
    .round({"night_share": 3, "foreign_share": 3, "agent_share": 3, "median_chf": 0, "p95_chf": 0, "max_chf": 0})
)
print("--- Normal behavior per customer, all cards together ---")
print(
    customer_normal
    [[
        "customer_id", "persona_name", "budget_style", "purchases", "night_share", "foreign_share", "agent_share",
        "distinct_merchants", "recent_purchases", "recent_first_time_merchants", "median_chf", "p95_chf", "max_chf",
    ]]
    .to_string(index=False)
)
print()









#### Step 3: Hours of the day on the four scenario cards ####

# Count active purchases per local hour on each scenario card, one row per card and one column per hour.
scenario_card_ids = purchase_attempts["card_id"].unique()

hour_counts_per_card = (
    active_purchases
    .query("card_id in @scenario_card_ids")
    .groupby(["card_id", "local_hour"])
    .size()
    .unstack("local_hour", fill_value=0)
    .reindex(columns=range(24), fill_value=0)
)
print("--- Active approved purchases per local Swiss hour, scenario cards ---")
print(hour_counts_per_card.to_string())
print()



# Repeat the count for online purchases only, since every scenario purchase is an online purchase.
online_hour_counts_per_card = (
    active_purchases
    .query("card_id in @scenario_card_ids and channel == 'ecommerce'")
    .groupby(["card_id", "local_hour"])
    .size()
    .unstack("local_hour", fill_value=0)
    .reindex(columns=range(24), fill_value=0)
)
print("--- Online approved purchases per local Swiss hour, scenario cards ---")
print(online_hour_counts_per_card.to_string())
print()









#### Step 4: How fast purchases follow each other in the history ####

# Count, for every history row, how many earlier rows on the same card fall within the ten minutes before it.
rows_in_ten_minutes = (
    authorization_history
    .assign(one_row=1)
    .sort_values("timestamp_utc")
    .set_index("timestamp_utc")
    .groupby("card_id")["one_row"]
    .rolling("10min")
    .sum()
    .reset_index(name="rows_within_ten_minutes")
    .assign(earlier_rows_within_ten_minutes=lambda table: table["rows_within_ten_minutes"].astype(int) - 1)
)

print("--- Earlier rows within ten minutes on the same card, all 4,701 history rows ---")
print(rows_in_ten_minutes["earlier_rows_within_ten_minutes"].value_counts().sort_index().to_string())
print()



# Show the same distribution for the four scenario cards only.
print("--- The same, scenario cards only ---")
print(
    rows_in_ten_minutes
    .query("card_id in @scenario_card_ids")
    .groupby(["card_id", "earlier_rows_within_ten_minutes"])
    .size()
    .unstack("earlier_rows_within_ten_minutes", fill_value=0)
    .to_string()
)
print()









#### Step 5: Every scenario purchase placed against the normal of its own card ####

# Pair each scenario purchase with every active purchase in the history of the same card.
attempts_against_card_history = (
    purchase_attempts
    [["authorization_id", "scenario_id", "replay_order", "card_id", "merchant_id", "local_hour", "billing_amount_chf", "currency", "recent_attempt_count_10m"]]
    .merge(merchants[["merchant_id", "merchant_category", "merchant_country"]], on="merchant_id", how="left")
    .merge(
        active_purchases[["card_id", "local_hour", "billing_amount_chf", "merchant_category", "merchant_country", "channel"]],
        on="card_id",
        how="left",
        suffixes=("", "_history"),
    )
    .assign(
        hour_distance=lambda table: (table["local_hour"] - table["local_hour_history"]).abs(),
        is_within_one_hour=lambda table: (table["hour_distance"] <= 1) | (table["hour_distance"] >= 23),
        is_same_category=lambda table: table["merchant_category"] == table["merchant_category_history"],
        is_same_country=lambda table: table["merchant_country"] == table["merchant_country_history"],
        is_cheaper_or_equal=lambda table: table["billing_amount_chf_history"] <= table["billing_amount_chf"],
        is_cheaper_or_equal_same_category=lambda table: table["is_same_category"] & table["is_cheaper_or_equal"],
    )
)



# Reduce the pairs to one row per scenario purchase with the share of the card's history that resembles it.
attempt_signals = (
    attempts_against_card_history
    .groupby(["scenario_id", "replay_order", "authorization_id", "local_hour", "billing_amount_chf", "currency", "merchant_country", "recent_attempt_count_10m"])
    .agg(
        history_purchases=("is_within_one_hour", "count"),
        share_of_history_within_one_hour=("is_within_one_hour", "mean"),
        purchases_in_same_country=("is_same_country", "sum"),
        purchases_in_same_category=("is_same_category", "sum"),
        cheaper_or_equal_same_category=("is_cheaper_or_equal_same_category", "sum"),
        share_of_all_history_cheaper_or_equal=("is_cheaper_or_equal", "mean"),
    )
    .reset_index()
    .assign(
        amount_rank_within_category=lambda table: (table["cheaper_or_equal_same_category"] / table["purchases_in_same_category"]).round(2),
    )
    .round({"share_of_history_within_one_hour": 3, "share_of_all_history_cheaper_or_equal": 2})
    .sort_values(["scenario_id", "replay_order"])
)
print("--- Every scenario purchase against the normal of its own card ---")
print(
    attempt_signals
    [[
        "scenario_id", "replay_order", "authorization_id", "local_hour", "share_of_history_within_one_hour",
        "billing_amount_chf", "currency", "amount_rank_within_category", "share_of_all_history_cheaper_or_equal",
        "merchant_country", "purchases_in_same_country", "purchases_in_same_category", "recent_attempt_count_10m",
    ]]
    .to_string(index=False)
)
print()
