# Script: 08_evidence_for_hidden_scenarios.py
# Purpose: Gather, for every customer no public scenario uses, the profile, the card settings, the normal behavior and the unused catalogue items that a hidden scenario could be built from
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
pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 160)
pd.set_option("display.max_rows", 300)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {
    "scenario_id": str, "authority_id": str, "authorization_id": str, "customer_id": str,
    "account_id": str, "card_id": str, "merchant_id": str, "item_id": str, "customer_device_id": str,
}

LOCAL_TIME_ZONE = "Europe/Zurich"
NIGHT_ENDS_AT_LOCAL_HOUR = 5



# Return the 95th percentile of a column of amounts.
def percentile_95(values):
    return values.quantile(0.95)



# Join the distinct values of a column into one sorted, readable string.
def join_distinct_values(values):
    distinct_values = sorted(set(values))
    return ", ".join(distinct_values)









#### Step 1: Load the tables and find the customers no public scenario uses ####

# Read the reference tables, the scenario tables and the history.
customers = pd.read_csv(DATA_FOLDER / "customers.csv", dtype=IDENTIFIER_COLUMNS)
accounts = pd.read_csv(DATA_FOLDER / "accounts.csv", dtype=IDENTIFIER_COLUMNS)
cards = pd.read_csv(DATA_FOLDER / "cards.csv", dtype=IDENTIFIER_COLUMNS)
merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
items = pd.read_csv(DATA_FOLDER / "items.csv", dtype=IDENTIFIER_COLUMNS)
scenario_authorities = pd.read_csv(DATA_FOLDER / "scenario_authorities.csv", dtype=IDENTIFIER_COLUMNS)
purchase_attempts = pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)
purchase_attempt_items = pd.read_csv(DATA_FOLDER / "purchase_attempt_items.csv", dtype=IDENTIFIER_COLUMNS)

authorization_history = (
    pd.read_csv(DATA_FOLDER / "authorization_history.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(
        timestamp_utc=lambda table: pd.to_datetime(table["timestamp"], utc=True),
        local_hour=lambda table: table["timestamp_utc"].dt.tz_convert(LOCAL_TIME_ZONE).dt.hour,
        is_night=lambda table: table["local_hour"] < NIGHT_ENDS_AT_LOCAL_HOUR,
        is_foreign=lambda table: table["merchant_country"] != "CH",
        is_agent=lambda table: table["initiator_type"] == "agent",
    )
)



# Separate the customers used by a public scenario from the ones that are not.
scenario_customer_ids = set(scenario_authorities["customer_id"])
unused_customers = customers.query("customer_id not in @scenario_customer_ids")
assert len(unused_customers) == 16, len(unused_customers)
print("--- Customers no public scenario uses ---")
print(f"{len(unused_customers)} of {len(customers)}")
print()









#### Step 2: Catalogue items and merchants no public scenario uses ####

# List the catalogue items that appear in no public cart, since a hidden scenario has to be built from them.
used_item_ids = set(purchase_attempt_items["item_id"])
unused_items = items.query("item_id not in @used_item_ids").sort_values(["item_category", "item_name"])
print("--- Catalogue items that appear in no public scenario ---")
print(f"{len(unused_items)} of {len(items)} items")
print(unused_items[["item_id", "item_name", "item_category", "unit_price_typical_chf", "unit_price_max_chf", "item_description"]].to_string(index=False))
print()



# Count, per merchant category, how many merchants the public scenarios use and how many they leave untouched.
used_merchant_ids = set(purchase_attempts["merchant_id"])
merchant_use = (
    merchants
    .assign(is_used_in_public_scenario=lambda table: table["merchant_id"].isin(used_merchant_ids))
    .groupby("merchant_category")
    .agg(merchants=("merchant_id", "count"), used_in_public_scenarios=("is_used_in_public_scenario", "sum"))
    .reset_index()
    .sort_values("used_in_public_scenarios", ascending=False)
)
print("--- Merchant categories and how many of their merchants the public scenarios use ---")
print(merchant_use.to_string(index=False))
print()









#### Step 3: Cards and limits of the unused customers ####

# Show every card of the unused customers with its switches and the limits of its account.
cards_of_unused_customers = (
    cards
    .merge(accounts[["account_id", "customer_id", "account_type", "account_purpose", "per_transaction_limit_chf", "monthly_limit_chf"]], on="account_id", how="left")
    .query("customer_id not in @scenario_customer_ids")
    .sort_values(["customer_id", "card_id"])
)
print("--- Cards of the unused customers ---")
print(
    cards_of_unused_customers
    [["customer_id", "card_id", "card_type", "card_purpose", "status", "international_enabled", "virtual_card", "account_purpose", "per_transaction_limit_chf", "monthly_limit_chf"]]
    .to_string(index=False)
)
print()









#### Step 4: Normal behavior of the unused customers ####

# Keep the approved purchases a person or an agent actively made, leaving out scheduled recurring payments.
active_purchases = authorization_history.query(
    "status == 'approved' and transaction_type == 'purchase' and channel != 'recurring' and customer_id not in @scenario_customer_ids"
)

# Summarize each customer's behavior in one row.
behavior_per_customer = (
    active_purchases
    .groupby("customer_id")
    .agg(
        purchases=("authorization_id", "count"),
        night_share=("is_night", "mean"),
        foreign_share=("is_foreign", "mean"),
        agent_share=("is_agent", "mean"),
        countries=("merchant_country", join_distinct_values),
        median_chf=("billing_amount_chf", "median"),
        p95_chf=("billing_amount_chf", percentile_95),
        max_chf=("billing_amount_chf", "max"),
    )
    .round({"night_share": 3, "foreign_share": 3, "agent_share": 3, "median_chf": 0, "p95_chf": 0, "max_chf": 0})
    .reset_index()
)
print("--- Normal behavior of the unused customers ---")
print(behavior_per_customer.to_string(index=False))
print()



# Rank the merchant categories of each customer by approved purchases and keep the top four.
top_categories_per_customer = (
    active_purchases
    .groupby(["customer_id", "merchant_category"])
    .agg(purchases=("authorization_id", "count"), total_chf=("billing_amount_chf", "sum"))
    .reset_index()
    .sort_values(["customer_id", "purchases"], ascending=[True, False])
    .groupby("customer_id")
    .head(4)
    .round({"total_chf": 0})
)
print("--- Four most used merchant categories per unused customer ---")
print(top_categories_per_customer.to_string(index=False))
print()



# Show where the agents of these customers have bought, including scheduled recurring payments.
agent_categories_per_customer = (
    authorization_history
    .query("is_agent and customer_id not in @scenario_customer_ids")
    .groupby(["customer_id", "merchant_category"])
    .agg(agent_rows=("authorization_id", "count"))
    .reset_index()
    .sort_values(["customer_id", "agent_rows"], ascending=[True, False])
    .groupby("customer_id")
    .head(3)
)
print("--- Three categories where each unused customer's agent has bought most ---")
print(agent_categories_per_customer.to_string(index=False))
print()









#### Step 5: The profile of each unused customer next to the merchants that fit it ####

# List, for each unused customer, the merchants of their most used category with how often they bought there.
merchants_in_top_category = (
    top_categories_per_customer
    .groupby("customer_id")
    .head(2)
    [["customer_id", "merchant_category"]]
    .merge(
        active_purchases.groupby(["customer_id", "merchant_category", "merchant_name", "merchant_country"]).size().reset_index(name="purchases"),
        on=["customer_id", "merchant_category"],
        how="left",
    )
    .sort_values(["customer_id", "merchant_category", "purchases"], ascending=[True, True, False])
)

print("--- Profile and best known merchants in the two most used categories ---")
for customer_row in unused_customers.to_dict("records"):
    print(f"{customer_row['customer_id']}  {customer_row['persona_name']}  ({customer_row['budget_style']})")
    print(f"  background            {customer_row['background']}")
    print(f"  shopping_preferences  {customer_row['shopping_preferences']}")
    print(f"  typical_spending      {customer_row['typical_spending']}")
    print(f"  travel_pattern        {customer_row['travel_pattern']}")
    print(
        merchants_in_top_category
        .query("customer_id == @customer_row['customer_id']")
        [["merchant_category", "merchant_name", "merchant_country", "purchases"]]
        .to_string(index=False)
    )
    print()
