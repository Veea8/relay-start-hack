# Script: 06_past_declines_and_agent_purchases.py
# Purpose: Show which signals go together with past declines, what the rapid series in the history are, and how agent purchases differ from human ones
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
pd.set_option("display.max_rows", 300)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {
    "authorization_id": str, "customer_id": str, "account_id": str, "card_id": str,
    "merchant_id": str, "customer_device_id": str, "related_transaction_id": str,
}

LOCAL_TIME_ZONE = "Europe/Zurich"
NIGHT_ENDS_AT_LOCAL_HOUR = 5
HIGH_AMOUNT_RATIO = 3
SCENARIO_CARD_IDS = ["CA0001", "CA0011", "CA0023", "CA0039"]









#### Step 1: Load the history and add one flag per signal ####

# Read the history in time order per card, so a rolling count lines up with the rows.
authorization_history = (
    pd.read_csv(DATA_FOLDER / "authorization_history.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(timestamp_utc=lambda table: pd.to_datetime(table["timestamp"], utc=True))
    .sort_values(["card_id", "timestamp_utc", "authorization_id"])
    .reset_index(drop=True)
)
assert len(authorization_history) == 4701, len(authorization_history)



# Count, for every row, the earlier rows on the same card within the ten minutes before it.
rows_within_ten_minutes = (
    authorization_history
    .assign(one_row=1)
    .set_index("timestamp_utc")
    .groupby("card_id")["one_row"]
    .rolling("10min")
    .sum()
)
assert len(rows_within_ten_minutes) == len(authorization_history)

# Take the median approved purchase amount per card as that card's normal amount.
median_amount_per_card = (
    authorization_history
    .query("status == 'approved' and transaction_type == 'purchase'")
    .groupby("card_id")
    .agg(card_median_chf=("billing_amount_chf", "median"))
    .reset_index()
)



# Add one true or false flag per signal to every history row.
history_with_signals = (
    authorization_history
    .assign(earlier_rows_within_ten_minutes=rows_within_ten_minutes.to_numpy().astype(int) - 1)
    .merge(median_amount_per_card, on="card_id", how="left")
    .assign(
        local_hour=lambda table: table["timestamp_utc"].dt.tz_convert(LOCAL_TIME_ZONE).dt.hour,
        is_declined=lambda table: table["status"] == "declined",
        is_night=lambda table: table["local_hour"] < NIGHT_ENDS_AT_LOCAL_HOUR,
        is_foreign_merchant=lambda table: table["merchant_country"] != "CH",
        is_first_time_merchant=lambda table: table["approved_merchant_transaction_count_before"] == 0,
        is_first_time_device=lambda table: table["customer_device_id"].notna() & (table["approved_device_transaction_count_before"] == 0),
        is_rapid_series=lambda table: table["earlier_rows_within_ten_minutes"] >= 1,
        amount_to_card_median=lambda table: (table["billing_amount_chf"] / table["card_median_chf"]).round(2),
        is_high_amount=lambda table: table["amount_to_card_median"] >= HIGH_AMOUNT_RATIO,
        is_card_not_active=lambda table: table["card_status"] != "active",
    )
)

purchases_with_signals = history_with_signals.query("transaction_type == 'purchase'")
print("--- Purchases in the history ---")
print(f"{len(purchases_with_signals)} purchases, {int(purchases_with_signals['is_declined'].sum())} declined, share {purchases_with_signals['is_declined'].mean():.3f}")
print()









#### Step 2: How often a purchase was declined when each signal was present ####

# Turn the flags into one long table and compute the decline share with and without each signal.
SIGNAL_COLUMNS = [
    "is_night", "is_foreign_merchant", "is_first_time_merchant", "is_first_time_device",
    "is_rapid_series", "is_high_amount", "is_card_not_active",
]

decline_share_per_signal = (
    purchases_with_signals
    .melt(id_vars=["authorization_id", "is_declined"], value_vars=SIGNAL_COLUMNS, var_name="signal", value_name="signal_present")
    .groupby(["signal", "signal_present"])
    .agg(purchases=("authorization_id", "count"), declined=("is_declined", "sum"), decline_share=("is_declined", "mean"))
    .round({"decline_share": 3})
    .reset_index()
)
print("--- Decline share with and without each signal ---")
print(decline_share_per_signal.to_string(index=False))
print()



# Count how many signals each purchase carries and show the decline share per count.
decline_share_per_signal_count = (
    purchases_with_signals
    .assign(signal_count=lambda table: table[SIGNAL_COLUMNS].sum(axis=1))
    .groupby("signal_count")
    .agg(purchases=("authorization_id", "count"), declined=("is_declined", "sum"), decline_share=("is_declined", "mean"))
    .round({"decline_share": 3})
    .reset_index()
)
print("--- Decline share by the number of signals a purchase carries ---")
print(decline_share_per_signal_count.to_string(index=False))
print()



# Show the decline share by who started the purchase and on which channel.
print("--- Decline share by initiator and channel ---")
print(
    purchases_with_signals
    .groupby(["initiator_type", "channel"])
    .agg(purchases=("authorization_id", "count"), declined=("is_declined", "sum"), decline_share=("is_declined", "mean"))
    .round({"decline_share": 3})
    .reset_index()
    .to_string(index=False)
)
print()

# Show the decline share by the amount relative to the card's own median.
print("--- Decline share by amount relative to the card median ---")
print(
    purchases_with_signals
    .assign(amount_band=lambda table: pd.cut(table["amount_to_card_median"], bins=[0, 1, 2, 3, 5, 10, 1000], include_lowest=True))
    .groupby("amount_band", observed=True)
    .agg(purchases=("authorization_id", "count"), declined=("is_declined", "sum"), decline_share=("is_declined", "mean"))
    .round({"decline_share": 3})
    .reset_index()
    .to_string(index=False)
)
print()









#### Step 3: What the rapid series in the history are ####

# Describe the rows that follow another row on the same card within ten minutes.
rapid_series_rows = history_with_signals.query("is_rapid_series")
print("--- Rows that follow another row on the same card within ten minutes ---")
print(f"{len(rapid_series_rows)} rows, declined share {rapid_series_rows['is_declined'].mean():.3f}")
print(
    rapid_series_rows
    .groupby(["channel", "initiator_type", "merchant_category"])
    .agg(rows=("authorization_id", "count"), declined=("is_declined", "sum"))
    .reset_index()
    .sort_values("rows", ascending=False)
    .head(15)
    .to_string(index=False)
)
print()



# Print every row of the rapid series on the two scenario cards that have them, together with the row just before.
print("--- Rapid series on the clothing and monitor scenario cards, row by row ---")
print(
    history_with_signals
    .query("card_id in ['CA0023', 'CA0039']")
    .assign(starts_or_continues_series=lambda table: table["is_rapid_series"] | table.groupby("card_id")["is_rapid_series"].shift(-1, fill_value=False))
    .query("starts_or_continues_series")
    [[
        "card_id", "timestamp", "local_hour", "channel", "initiator_type", "status", "billing_amount_chf",
        "merchant_name", "merchant_category", "merchant_country", "earlier_rows_within_ten_minutes",
        "is_first_time_merchant", "is_first_time_device",
    ]]
    .to_string(index=False)
)
print()









#### Step 4: Every declined row on the four scenario cards ####

# List the declined rows on the scenario cards with the signals each one carried.
print("--- Declined rows on the scenario cards ---")
print(
    history_with_signals
    .query("card_id in @SCENARIO_CARD_IDS and is_declined")
    [[
        "card_id", "timestamp", "local_hour", "channel", "initiator_type", "billing_amount_chf", "amount_to_card_median",
        "merchant_name", "merchant_country", "is_first_time_merchant", "is_first_time_device", "earlier_rows_within_ten_minutes",
    ]]
    .to_string(index=False)
)
print()









#### Step 5: How agent purchases differ from human purchases ####

# Compare agent and human purchases on the channels agents use.
print("--- Agent and human purchases on the ecommerce and recurring channels ---")
print(
    purchases_with_signals
    .query("channel in ['ecommerce', 'recurring'] and initiator_type in ['agent', 'human']")
    .groupby(["channel", "initiator_type"])
    .agg(
        purchases=("authorization_id", "count"),
        decline_share=("is_declined", "mean"),
        median_chf=("billing_amount_chf", "median"),
        first_time_merchant_share=("is_first_time_merchant", "mean"),
        foreign_share=("is_foreign_merchant", "mean"),
        night_share=("is_night", "mean"),
    )
    .round(3)
    .reset_index()
    .to_string(index=False)
)
print()



# Show which kinds of shop the agents bought from.
print("--- Agent purchases by merchant category ---")
print(
    purchases_with_signals
    .query("initiator_type == 'agent'")
    .groupby("merchant_category")
    .agg(purchases=("authorization_id", "count"), declined=("is_declined", "sum"), median_chf=("billing_amount_chf", "median"))
    .reset_index()
    .sort_values("purchases", ascending=False)
    .to_string(index=False)
)
print()

# List the agent purchases on the four scenario cards.
print("--- Agent purchases on the scenario cards ---")
print(
    purchases_with_signals
    .query("initiator_type == 'agent' and card_id in @SCENARIO_CARD_IDS")
    [["card_id", "timestamp", "channel", "status", "billing_amount_chf", "merchant_name", "merchant_category", "is_first_time_merchant", "description"]]
    .to_string(index=False)
)
print()









#### Step 6: Refunds ####

# Count the refunds and check that each one points back to a purchase in the history.
refunds = history_with_signals.query("transaction_type == 'refund'")
refunds_with_origin = refunds.merge(
    authorization_history[["authorization_id", "billing_amount_chf", "merchant_id"]],
    left_on="related_transaction_id",
    right_on="authorization_id",
    how="left",
    suffixes=("", "_original"),
)
print("--- Refunds ---")
print(f"{len(refunds)} refunds, {int(refunds_with_origin['authorization_id_original'].notna().sum())} point back to a purchase in the history")
print(f"refunds on the scenario cards: {int(refunds['card_id'].isin(SCENARIO_CARD_IDS).sum())}")
print()
