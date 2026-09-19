# Script: 02_scenario_customers_up_close.py
# Purpose: Show who stands behind each public scenario and which merchants and devices that person really knows
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

# Widen the console output so long text columns print without being cut off.
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 200)
pd.set_option("display.max_rows", 200)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {
    "scenario_id": str, "authority_id": str, "authorization_id": str, "customer_id": str,
    "account_id": str, "card_id": str, "merchant_id": str, "customer_device_id": str,
}









#### Step 1: Load the tables ####

# Read the scenario tables, the reference tables and the purchase history.
scenario_catalogue = pd.read_csv(DATA_FOLDER / "scenario_catalogue.csv", dtype=IDENTIFIER_COLUMNS)
scenario_authorities = pd.read_csv(DATA_FOLDER / "scenario_authorities.csv", dtype=IDENTIFIER_COLUMNS)
purchase_attempts = pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)
customers = pd.read_csv(DATA_FOLDER / "customers.csv", dtype=IDENTIFIER_COLUMNS)
accounts = pd.read_csv(DATA_FOLDER / "accounts.csv", dtype=IDENTIFIER_COLUMNS)
cards = pd.read_csv(DATA_FOLDER / "cards.csv", dtype=IDENTIFIER_COLUMNS)
merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
authorization_history = pd.read_csv(DATA_FOLDER / "authorization_history.csv", dtype=IDENTIFIER_COLUMNS)



# Check the two sizes every later step relies on.
assert len(purchase_attempts) == 45, len(purchase_attempts)
assert len(authorization_history) == 4701, len(authorization_history)
print("--- Tables loaded ---")
print(f"purchase attempts {len(purchase_attempts)}, history rows {len(authorization_history)}")
print()









#### Step 2: Who stands behind each scenario ####

# Link each scenario to its customer, card and account through the purchase attempts, as the data guide prescribes.
scenario_identity = (
    purchase_attempts
    [["scenario_id", "authority_id", "card_id"]]
    .drop_duplicates()
    .merge(scenario_authorities[["authority_id", "customer_id"]], on="authority_id", how="left")
    .merge(cards, on="card_id", how="left")
    .merge(accounts.drop(columns=["customer_id", "status"]), on="account_id", how="left")
    .merge(customers, on="customer_id", how="left")
    .merge(scenario_catalogue[["scenario_id", "scenario_name", "cardholder_instruction"]], on="scenario_id", how="left")
    .sort_values("scenario_id")
)
assert len(scenario_identity) == 5, len(scenario_identity)



# Print the instruction next to the profile and the card settings, one scenario at a time.
print("--- Scenario, instruction, customer profile and card ---")
for scenario_row in scenario_identity.to_dict("records"):
    print(f"{scenario_row['scenario_id']}  {scenario_row['scenario_name']}")
    print(f"  instruction           {scenario_row['cardholder_instruction']}")
    print(f"  customer              {scenario_row['customer_id']}  {scenario_row['persona_name']}  ({scenario_row['home_region']})")
    print(f"  shopping_preferences  {scenario_row['shopping_preferences']}")
    print(f"  typical_spending      {scenario_row['typical_spending']}")
    print(f"  budget and travel     {scenario_row['budget_style']}. {scenario_row['travel_pattern']}")
    print(f"  card                  {scenario_row['card_id']}  {scenario_row['card_type']}, purpose {scenario_row['card_purpose']}, status {scenario_row['status']}, virtual {scenario_row['virtual_card']}")
    print(f"  card switches         online {scenario_row['online_enabled']}, international {scenario_row['international_enabled']}")
    print(f"  account               {scenario_row['account_id']}  {scenario_row['account_type']}, purpose {scenario_row['account_purpose']}")
    print(f"  issuer limits         per transaction CHF {scenario_row['per_transaction_limit_chf']}, monthly CHF {scenario_row['monthly_limit_chf']}")
    print()









#### Step 3: How much history each scenario customer has, card by card ####

# Keep only the four scenario customers and count their history rows per card.
scenario_customer_ids = scenario_identity["customer_id"].unique()
scenario_card_ids = scenario_identity["card_id"].unique()

history_of_scenario_customers = authorization_history.query("customer_id in @scenario_customer_ids")

history_per_card = (
    history_of_scenario_customers
    .assign(
        is_approved=lambda table: table["status"] == "approved",
        is_agent=lambda table: table["initiator_type"] == "agent",
        is_scenario_card=lambda table: table["card_id"].isin(scenario_card_ids),
    )
    .groupby(["customer_id", "card_id", "card_purpose", "is_scenario_card"])
    .agg(
        history_rows=("authorization_id", "count"),
        approved_rows=("is_approved", "sum"),
        agent_rows=("is_agent", "sum"),
        first_row=("timestamp", "min"),
        last_row=("timestamp", "max"),
    )
    .reset_index()
)
print("--- History per card of the four scenario customers ---")
print(history_per_card.to_string(index=False))
print()



# Show which payment channels each scenario card was used on.
print("--- Channels used on each scenario card ---")
print(
    authorization_history
    .query("card_id in @scenario_card_ids")
    .groupby(["card_id", "channel", "initiator_type"])
    .size()
    .unstack("initiator_type", fill_value=0)
    .to_string()
)
print()









#### Step 4: Merchant familiarity for every merchant that appears in a scenario ####

# Count approved purchases per card and merchant, and per customer and merchant across all of that customer's cards.
approved_purchases = authorization_history.query("status == 'approved' and transaction_type == 'purchase'")

approved_per_card_and_merchant = (
    approved_purchases
    .groupby(["card_id", "merchant_id"])
    .agg(
        approved_on_this_card=("authorization_id", "count"),
        first_approved=("timestamp", "min"),
        last_approved=("timestamp", "max"),
    )
    .reset_index()
)

approved_per_customer_and_merchant = (
    approved_purchases
    .groupby(["customer_id", "merchant_id"])
    .agg(approved_on_all_cards_of_customer=("authorization_id", "count"))
    .reset_index()
)

declined_per_card_and_merchant = (
    authorization_history
    .query("status == 'declined'")
    .groupby(["card_id", "merchant_id"])
    .agg(declined_on_this_card=("authorization_id", "count"))
    .reset_index()
)



# List each merchant used in a scenario with its familiarity on the scenario card and for the customer as a whole.
scenario_merchant_familiarity = (
    purchase_attempts
    .groupby(["scenario_id", "card_id", "merchant_id"])
    .agg(attempts_in_scenario=("authorization_id", "count"), attempt_ids=("authorization_id", ", ".join))
    .reset_index()
    .merge(scenario_identity[["scenario_id", "customer_id"]], on="scenario_id", how="left")
    .merge(merchants[["merchant_id", "merchant_name", "merchant_category", "merchant_country"]], on="merchant_id", how="left")
    .merge(approved_per_card_and_merchant, on=["card_id", "merchant_id"], how="left")
    .merge(approved_per_customer_and_merchant, on=["customer_id", "merchant_id"], how="left")
    .merge(declined_per_card_and_merchant, on=["card_id", "merchant_id"], how="left")
    .fillna({"approved_on_this_card": 0, "approved_on_all_cards_of_customer": 0, "declined_on_this_card": 0})
    .astype({"approved_on_this_card": int, "approved_on_all_cards_of_customer": int, "declined_on_this_card": int})
    .sort_values(["scenario_id", "approved_on_this_card"], ascending=[True, False])
)
print("--- Familiarity of every merchant that appears in a scenario ---")
print(
    scenario_merchant_familiarity
    [[
        "scenario_id", "merchant_id", "merchant_name", "merchant_category", "merchant_country",
        "attempts_in_scenario", "approved_on_this_card", "approved_on_all_cards_of_customer",
        "declined_on_this_card", "last_approved", "attempt_ids",
    ]]
    .to_string(index=False)
)
print()









#### Step 5: Device familiarity for every device that appears in a scenario ####

# Count approved purchases per card and device, then attach the count to each device used in a scenario.
approved_per_card_and_device = (
    approved_purchases
    .groupby(["card_id", "customer_device_id"])
    .agg(approved_on_this_device=("authorization_id", "count"), last_approved=("timestamp", "max"))
    .reset_index()
)

scenario_device_familiarity = (
    purchase_attempts
    .groupby(["scenario_id", "card_id", "customer_device_id"])
    .agg(attempts_in_scenario=("authorization_id", "count"), attempt_ids=("authorization_id", ", ".join))
    .reset_index()
    .merge(approved_per_card_and_device, on=["card_id", "customer_device_id"], how="left")
    .fillna({"approved_on_this_device": 0})
    .astype({"approved_on_this_device": int})
)
print("--- Familiarity of every device that appears in a scenario ---")
print(scenario_device_familiarity.to_string(index=False))
print()



# Count how many distinct devices each scenario card has ever been used with.
print("--- Distinct devices with approved purchases, per scenario card ---")
print(
    approved_per_card_and_device
    .query("card_id in @scenario_card_ids")
    .sort_values(["card_id", "approved_on_this_device"], ascending=[True, False])
    .to_string(index=False)
)
print()









#### Step 6: The merchants each scenario card knows best ####

# Rank the merchants on each scenario card by approved purchases, with the money spent there.
best_known_merchants = (
    approved_purchases
    .query("card_id in @scenario_card_ids")
    .groupby(["card_id", "merchant_id", "merchant_name", "merchant_category", "merchant_country"])
    .agg(approved_purchases=("authorization_id", "count"), total_chf=("billing_amount_chf", "sum"))
    .reset_index()
    .sort_values(["card_id", "approved_purchases"], ascending=[True, False])
    .groupby("card_id")
    .head(8)
)
print("--- Eight best known merchants per scenario card ---")
print(best_known_merchants.to_string(index=False))
print()
