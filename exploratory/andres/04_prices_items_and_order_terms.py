# Script: 04_prices_items_and_order_terms.py
# Purpose: Compare every scenario cart line with the item catalogue, check the order arithmetic, and line up the return flag with the shop text
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
pd.set_option("display.max_colwidth", 120)
pd.set_option("display.max_rows", 200)

# Keep every identifier as text so none is read as a number.
IDENTIFIER_COLUMNS = {
    "scenario_id": str, "authorization_id": str, "card_id": str, "merchant_id": str, "item_id": str,
    "order_returnable": str, "order_cancellable": str,
}

# Text patterns for the two facts that exist only in the shop sentence.
RETURN_DAYS_PATTERN = r"returns? accepted within (\d+) days"
SHOE_OR_CLOTHING_SIZE_PATTERN = r"size (\d+|[A-Z]{1,3})\b"









#### Step 1: Load the cart lines with their purchase, merchant, catalogue item and exchange rate ####

# Read the tables needed to price every cart line in francs.
purchase_attempts = pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)
purchase_attempt_items = pd.read_csv(DATA_FOLDER / "purchase_attempt_items.csv", dtype=IDENTIFIER_COLUMNS)
items = pd.read_csv(DATA_FOLDER / "items.csv", dtype=IDENTIFIER_COLUMNS)
merchants = pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
fx_rates = pd.read_csv(DATA_FOLDER / "fx_rates.csv")

assert len(purchase_attempt_items) == 56, len(purchase_attempt_items)



# Attach the purchase, the merchant, the catalogue entry and the rate to every cart line.
cart_lines = (
    purchase_attempt_items
    .merge(
        purchase_attempts[["authorization_id", "scenario_id", "replay_order", "merchant_id", "order_returnable"]],
        on="authorization_id",
        how="left",
    )
    .merge(merchants[["merchant_id", "merchant_name", "merchant_category", "recurring_capable"]], on="merchant_id", how="left")
    .merge(
        items.rename(columns={"item_name": "catalogue_item_name", "item_category": "catalogue_item_category"}),
        on="item_id",
        how="left",
    )
    .merge(fx_rates[["from_currency", "rate"]], left_on="currency", right_on="from_currency", how="left")
    .assign(
        unit_price_chf=lambda table: (table["unit_price"] * table["rate"]).round(2),
        price_to_typical_ratio=lambda table: (table["unit_price_chf"] / table["unit_price_typical_chf"]).round(2),
        is_below_catalogue_min=lambda table: table["unit_price_chf"] < table["unit_price_min_chf"],
        is_above_catalogue_max=lambda table: table["unit_price_chf"] > table["unit_price_max_chf"],
    )
    .sort_values(["scenario_id", "replay_order", "line_no"])
)

# Confirm that every cart line found its catalogue item and that names and categories agree with the catalogue.
assert cart_lines["catalogue_item_name"].notna().all()
assert (cart_lines["item_name"] == cart_lines["catalogue_item_name"]).all()
assert (cart_lines["item_category"] == cart_lines["catalogue_item_category"]).all()
print("--- Cart lines joined to the catalogue ---")
print(f"{len(cart_lines)} lines, all names and categories agree with the catalogue")
print()









#### Step 2: Where each price sits inside the catalogue range of its item ####

# Show every cart line with its price in francs next to the lowest, typical and highest catalogue price.
print("--- Price of every cart line against the catalogue range ---")
print(
    cart_lines
    [[
        "scenario_id", "replay_order", "authorization_id", "item_name", "quantity", "unit_price", "currency",
        "unit_price_chf", "unit_price_min_chf", "unit_price_typical_chf", "unit_price_max_chf",
        "price_to_typical_ratio", "is_below_catalogue_min", "is_above_catalogue_max",
    ]]
    .to_string(index=False)
)
print()



# List only the lines whose price falls outside the catalogue range.
print("--- Cart lines priced outside the catalogue range ---")
print(
    cart_lines
    .query("is_below_catalogue_min or is_above_catalogue_max")
    [["scenario_id", "replay_order", "authorization_id", "item_name", "unit_price_chf", "unit_price_min_chf", "unit_price_max_chf"]]
    .to_string(index=False)
)
print()









#### Step 3: Whether the order arithmetic adds up ####

# Add up the cart lines of each purchase and compare with the subtotal, the delivery fee, the amount and the franc amount.
cart_totals = (
    cart_lines
    .assign(line_total=lambda table: table["quantity"] * table["unit_price"])
    .groupby("authorization_id")
    .agg(sum_of_lines=("line_total", "sum"), line_count=("line_no", "count"), highest_quantity=("quantity", "max"))
    .reset_index()
)

order_arithmetic = (
    purchase_attempts
    .merge(cart_totals, on="authorization_id", how="left")
    .merge(fx_rates[["from_currency", "rate"]], left_on="currency", right_on="from_currency", how="left")
    .assign(
        lines_minus_subtotal=lambda table: (table["sum_of_lines"] - table["items_subtotal"]).round(2),
        subtotal_plus_fee_minus_amount=lambda table: (table["items_subtotal"] + table["delivery_fee"] - table["amount"]).round(2),
        converted_minus_billing=lambda table: (table["amount"] * table["rate"] - table["billing_amount_chf"]).round(2),
    )
)
print("--- Purchases whose arithmetic does not add up ---")
print(
    order_arithmetic
    .query("lines_minus_subtotal != 0 or subtotal_plus_fee_minus_amount != 0 or converted_minus_billing != 0")
    [["scenario_id", "replay_order", "authorization_id", "sum_of_lines", "items_subtotal", "delivery_fee", "amount", "currency", "billing_amount_chf"]]
    .to_string(index=False)
)
print()

# Show how many lines and what quantities the purchases carry, and how often a delivery fee is charged.
print("--- Lines per purchase, highest quantity and delivery fees ---")
print("lines per purchase:", order_arithmetic["line_count"].value_counts().sort_index().to_dict())
print("highest quantity on any line:", int(order_arithmetic["highest_quantity"].max()))
print(
    order_arithmetic
    .query("delivery_fee > 0")
    [["scenario_id", "replay_order", "authorization_id", "items_subtotal", "delivery_fee", "amount"]]
    .to_string(index=False)
)
print()









#### Step 4: Items that do not fit the shop that sells them ####

# List the lines whose item category differs from the category of the merchant.
print("--- Cart lines whose item category differs from the merchant category ---")
print(
    cart_lines
    .query("item_category != merchant_category")
    [["scenario_id", "replay_order", "authorization_id", "merchant_name", "merchant_category", "recurring_capable", "item_name", "item_category", "item_details"]]
    .to_string(index=False)
)
print()



# List the distinct catalogue items that appear in each scenario, since near-twin items are separate catalogue entries.
print("--- Distinct catalogue items per scenario ---")
print(
    cart_lines
    .groupby(["scenario_id", "item_id", "item_name", "item_category"])
    .agg(lines=("line_no", "count"), purchases=("authorization_id", ", ".join))
    .reset_index()
    .to_string(index=False)
)
print()









#### Step 5: The return flag against the shop sentence ####

# Pull the number of return days and the size out of the shop sentence with two plain text patterns.
order_terms = cart_lines.assign(
    return_days_in_text=lambda table: table["item_details"].str.extract(RETURN_DAYS_PATTERN, expand=False),
    size_in_text=lambda table: table["item_details"].str.extract(SHOE_OR_CLOTHING_SIZE_PATTERN, expand=False),
    mentions_final_sale=lambda table: table["item_details"].str.contains("final sale", case=False),
    mentions_not_stated=lambda table: table["item_details"].str.contains("not stated", case=False),
)

print("--- Structured return flag against what the shop sentence says ---")
print(
    order_terms
    .fillna({"return_days_in_text": "none"})
    .groupby(["order_returnable", "return_days_in_text", "mentions_final_sale", "mentions_not_stated"])
    .agg(lines=("line_no", "count"), example=("item_details", "first"))
    .reset_index()
    .to_string(index=False)
)
print()



# Show the lines where the two text patterns found nothing, to see which phrasings a plain pattern would miss.
print("--- Shop sentences where no return days were found ---")
print(
    order_terms
    .query("return_days_in_text.isna()")
    [["scenario_id", "authorization_id", "item_category", "order_returnable", "item_details"]]
    .drop_duplicates(subset=["item_details"])
    .to_string(index=False)
)
print()









#### Step 6: How the catalogue itself describes items ####

# Print the catalogue descriptions of the item categories used in the scenarios, to see the wording a hidden scenario could use.
print("--- Catalogue entries for the categories the scenarios use ---")
print(
    items
    .query("item_category in ['sporting_goods', 'electronics', 'clothing', 'subscriptions', 'gift_card', 'membership', 'cosmetics']")
    [["item_id", "item_name", "item_category", "unit_price_min_chf", "unit_price_typical_chf", "unit_price_max_chf", "item_description"]]
    .sort_values(["item_category", "item_name"])
    .to_string(index=False)
)
print()
