# Script: 01_reference_tables_and_vocabulary.py
# Purpose: Profile the small reference tables and list the category vocabulary a wallet policy can refer to
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



# Join the distinct values of a column into one sorted, readable string.
def join_distinct_values(values):
    distinct_values = sorted(set(values))
    return ", ".join(distinct_values)



# Join the first three values of a column as examples.
def join_first_three_values(values):
    first_three_values = list(values)[:3]
    return ", ".join(first_three_values)









#### Step 1: Load the reference tables ####

# Read every small reference table as text first so no identifier or code loses leading zeros.
merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=str)
items = pd.read_csv(DATA_FOLDER / "items.csv", dtype=str)
customers = pd.read_csv(DATA_FOLDER / "customers.csv", dtype=str)
accounts = pd.read_csv(DATA_FOLDER / "accounts.csv", dtype=str)
cards = pd.read_csv(DATA_FOLDER / "cards.csv", dtype=str)
fx_rates = pd.read_csv(DATA_FOLDER / "fx_rates.csv", dtype=str)



# Check the row counts against the figures stated in the data guide.
expected_row_counts = {"merchants": 58, "items": 66, "customers": 20, "accounts": 31, "cards": 41, "fx_rates": 4}
actual_row_counts = {
    "merchants": len(merchants), "items": len(items), "customers": len(customers),
    "accounts": len(accounts), "cards": len(cards), "fx_rates": len(fx_rates),
}
assert actual_row_counts == expected_row_counts, actual_row_counts
print("--- Row counts match the data guide ---")
print(pd.Series(actual_row_counts).to_string())
print()









#### Step 2: Merchant vocabulary ####

# Count merchants per category and show which card network codes and countries each category covers.
merchant_category_summary = (
    merchants
    .groupby("merchant_category")
    .agg(
        merchant_count=("merchant_id", "count"),
        mcc_codes=("merchant_mcc", join_distinct_values),
        countries=("merchant_country", join_distinct_values),
        example_names=("merchant_name", join_first_three_values),
    )
    .reset_index()
    .sort_values("merchant_count", ascending=False)
)
print("--- Merchant categories ---")
print(merchant_category_summary.to_string(index=False))
print()



# Show the two remaining merchant attributes and their values.
print("--- Merchant availability values ---")
print(merchants["availability"].value_counts().to_string())
print()

# List the merchants that can bill on a recurring basis, since a recurring item from any other shop is inconsistent.
print("--- Merchants able to bill on a recurring basis, by category ---")
print(
    merchants
    .query("recurring_capable == 'true'")
    .groupby("merchant_category")
    .agg(merchant_count=("merchant_id", "count"), names=("merchant_name", join_distinct_values))
    .reset_index()
    .to_string(index=False)
)
print()









#### Step 3: Item vocabulary ####

# Count catalogue items per category and show the price span each category covers.
items_with_prices = items.assign(
    unit_price_min_chf=lambda table: table["unit_price_min_chf"].astype(float),
    unit_price_typical_chf=lambda table: table["unit_price_typical_chf"].astype(float),
    unit_price_max_chf=lambda table: table["unit_price_max_chf"].astype(float),
)

# Count the items per category with the lowest and highest catalogue price.
item_category_summary = (
    items_with_prices
    .groupby("item_category")
    .agg(
        item_count=("item_id", "count"),
        lowest_min_chf=("unit_price_min_chf", "min"),
        highest_max_chf=("unit_price_max_chf", "max"),
        example_items=("item_name", join_first_three_values),
    )
    .reset_index()
    .sort_values("item_count", ascending=False)
)
print("--- Item categories ---")
print(item_category_summary.to_string(index=False))
print()



# Compare the two vocabularies, since a policy can refer to a kind of shop or to a kind of item.
merchant_category_names = set(merchants["merchant_category"])
item_category_names = set(items["item_category"])

# List the item categories that describe basket contents and have no matching kind of shop.
print("--- Item categories with no merchant category of the same name ---")
print(sorted(item_category_names - merchant_category_names))
print()

# List the kinds of shop for which the catalogue holds no item category of the same name.
print("--- Merchant categories with no item category of the same name ---")
print(sorted(merchant_category_names - item_category_names))
print()









#### Step 4: Customer profiles ####

# Print every customer profile in full, because the free text describes what each person wants and avoids.
print("--- Customer profiles ---")
for customer_row in customers.to_dict("records"):
    print(f"{customer_row['customer_id']}  {customer_row['persona_name']}  ({customer_row['home_region']})")
    print(f"  background            {customer_row['background']}")
    print(f"  shopping_preferences  {customer_row['shopping_preferences']}")
    print(f"  typical_spending      {customer_row['typical_spending']}")
    print(f"  budget_style          {customer_row['budget_style']}")
    print(f"  travel_pattern        {customer_row['travel_pattern']}")
    print()



# Count the values of the two short profile fields.
print("--- Budget style values ---")
print(customers["budget_style"].value_counts().to_string())
print()









#### Step 5: Accounts and cards ####

# Summarize the issuer limits carried by each account type.
accounts_with_limits = accounts.assign(
    per_transaction_limit_chf=lambda table: table["per_transaction_limit_chf"].astype(float),
    monthly_limit_chf=lambda table: table["monthly_limit_chf"].astype(float),
)

# Show the lowest and highest issuer limits per kind of account.
print("--- Account limits by account type and purpose ---")
print(
    accounts_with_limits
    .groupby(["account_type", "account_purpose"])
    .agg(
        account_count=("account_id", "count"),
        lowest_per_transaction_limit=("per_transaction_limit_chf", "min"),
        highest_per_transaction_limit=("per_transaction_limit_chf", "max"),
        lowest_monthly_limit=("monthly_limit_chf", "min"),
        highest_monthly_limit=("monthly_limit_chf", "max"),
    )
    .reset_index()
    .to_string(index=False)
)
print()

# Confirm whether any account is inactive or held in a currency other than francs.
print("--- Account status and base currency values ---")
print(accounts.groupby(["status", "base_currency"]).size().to_string())
print()



# Count the card switches, since a card that forbids online or international use limits what an agent may do.
print("--- Card attribute values ---")
for card_attribute in ["card_type", "card_purpose", "status", "online_enabled", "international_enabled", "virtual_card"]:
    print(f"{card_attribute}: {cards[card_attribute].value_counts().to_dict()}")
print()

# List the cards with a restriction, together with the customer who holds them.
print("--- Cards that are not active, or that forbid online or international use ---")
print(
    cards
    .query("status != 'active' or online_enabled != 'true' or international_enabled != 'true'")
    .merge(accounts[["account_id", "customer_id"]], on="account_id", how="left")
    .to_string(index=False)
)
print()









#### Step 6: Exchange rates ####

# Print the fixed rates used to convert every purchase amount to francs.
print("--- Fixed exchange rates ---")
print(fx_rates.to_string(index=False))
print()
