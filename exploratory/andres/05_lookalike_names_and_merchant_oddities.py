# Script: 05_lookalike_names_and_merchant_oddities.py
# Purpose: Compare every merchant name with every other, and find merchants that have no history or look inconsistent
# Author: Andrés Gallardo
# Date: September 2026

from difflib import SequenceMatcher
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
IDENTIFIER_COLUMNS = {"merchant_id": str, "card_id": str, "customer_id": str, "authorization_id": str, "scenario_id": str}

# Words that carry no identity and are dropped before two names are compared word by word.
FILLER_WORDS = {"and", "the", "of"}



# Join the distinct values of a column into one sorted, readable string.
def join_distinct_values(values):
    distinct_values = sorted(set(values))
    return ", ".join(distinct_values)



# Reduce a merchant name to lowercase letters and digits, so spacing and capitals do not matter.
def normalize_name(merchant_name):
    kept_characters = [character.lower() for character in merchant_name if character.isalnum()]
    return "".join(kept_characters)



# Score how alike two normalized names are, from 0 for nothing in common to 1 for identical.
def name_similarity(pair_row):
    return round(SequenceMatcher(None, pair_row["normalized_name_a"], pair_row["normalized_name_b"]).ratio(), 3)



# List the meaningful words two merchant names share.
def shared_words(pair_row):
    words_a = {word.lower() for word in pair_row["merchant_name_a"].split()} - FILLER_WORDS
    words_b = {word.lower() for word in pair_row["merchant_name_b"].split()} - FILLER_WORDS
    return ", ".join(sorted(words_a & words_b))









#### Step 1: Load the merchants, the history and the scenario purchases ####

# Read the three tables and add a normalized version of every merchant name.
merchants = (
    pd.read_csv(DATA_FOLDER / "merchants.csv", dtype=IDENTIFIER_COLUMNS)
    .assign(normalized_name=lambda table: table["merchant_name"].map(normalize_name))
)
authorization_history = pd.read_csv(DATA_FOLDER / "authorization_history.csv", dtype=IDENTIFIER_COLUMNS)
purchase_attempts = pd.read_csv(DATA_FOLDER / "purchase_attempts.csv", dtype=IDENTIFIER_COLUMNS)

assert len(merchants) == 58, len(merchants)
assert merchants["merchant_id"].is_unique
print("--- Merchants loaded ---")
print(f"{len(merchants)} merchants, {merchants['normalized_name'].nunique()} distinct normalized names")
print()









#### Step 2: Every merchant name compared with every other ####

# Pair every merchant with every other merchant once and score how alike the two names are.
name_pairs = (
    merchants
    .merge(merchants, how="cross", suffixes=("_a", "_b"))
    .query("merchant_id_a < merchant_id_b")
    .assign(
        similarity=lambda table: table.apply(name_similarity, axis=1),
        shared_words=lambda table: table.apply(shared_words, axis=1),
        same_category=lambda table: table["merchant_category_a"] == table["merchant_category_b"],
        same_country=lambda table: table["merchant_country_a"] == table["merchant_country_b"],
    )
    .sort_values("similarity", ascending=False)
)
assert len(name_pairs) == 58 * 57 // 2, len(name_pairs)

print("--- The twenty most alike merchant names ---")
print(
    name_pairs
    .head(20)
    [[
        "merchant_id_a", "merchant_name_a", "merchant_id_b", "merchant_name_b", "similarity",
        "shared_words", "same_category", "merchant_country_a", "merchant_country_b",
    ]]
    .to_string(index=False)
)
print()



# Show how the similarity scores are spread, to see how far the closest pair stands from the rest.
print("--- How many name pairs fall into each similarity band ---")
print(
    pd.cut(name_pairs["similarity"], bins=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], include_lowest=True)
    .value_counts()
    .sort_index()
    .to_string()
)
print()



# List the pairs that share a whole word, since legitimate merchants also share words.
print("--- Merchant pairs that share a meaningful word ---")
print(
    name_pairs
    .query("shared_words != ''")
    [["merchant_name_a", "merchant_name_b", "shared_words", "similarity", "same_category"]]
    .sort_values("shared_words")
    .to_string(index=False)
)
print()









#### Step 3: How much history every merchant has ####

# Count history rows, approved rows, distinct cards and the first and last date per merchant.
history_per_merchant = (
    authorization_history
    .assign(is_approved=lambda table: table["status"] == "approved")
    .groupby("merchant_id")
    .agg(
        history_rows=("authorization_id", "count"),
        approved_rows=("is_approved", "sum"),
        distinct_cards=("card_id", "nunique"),
        first_seen=("timestamp", "min"),
        last_seen=("timestamp", "max"),
    )
    .reset_index()
)

scenario_use_per_merchant = (
    purchase_attempts
    .groupby("merchant_id")
    .agg(scenario_purchases=("authorization_id", "count"), scenarios=("scenario_id", join_distinct_values))
    .reset_index()
)

merchant_overview = (
    merchants
    .merge(history_per_merchant, on="merchant_id", how="left")
    .merge(scenario_use_per_merchant, on="merchant_id", how="left")
    .fillna({"history_rows": 0, "approved_rows": 0, "distinct_cards": 0, "scenario_purchases": 0, "scenarios": ""})
    .astype({"history_rows": int, "approved_rows": int, "distinct_cards": int, "scenario_purchases": int})
    .assign(decline_share=lambda table: (1 - table["approved_rows"] / table["history_rows"]).round(3))
)



# List the merchants that nobody has ever bought from.
print("--- Merchants with no history at all, on any card ---")
print(
    merchant_overview
    .query("history_rows == 0")
    [["merchant_id", "merchant_name", "merchant_category", "merchant_country", "merchant_city", "availability", "scenario_purchases", "scenarios"]]
    .to_string(index=False)
)
print()

# List the merchants with the fewest customers, since a rarely used merchant is close to unknown.
print("--- The ten merchants with history on the fewest cards ---")
print(
    merchant_overview
    .query("history_rows > 0")
    .sort_values(["distinct_cards", "history_rows"])
    .head(10)
    [["merchant_id", "merchant_name", "merchant_category", "merchant_country", "history_rows", "distinct_cards", "first_seen", "scenario_purchases"]]
    .to_string(index=False)
)
print()

# List the merchants with the highest share of declined rows in the history.
print("--- The ten merchants with the highest share of declines ---")
print(
    merchant_overview
    .query("history_rows >= 20")
    .sort_values("decline_share", ascending=False)
    .head(10)
    [["merchant_id", "merchant_name", "merchant_category", "merchant_country", "history_rows", "approved_rows", "decline_share"]]
    .to_string(index=False)
)
print()









#### Step 4: The lookalike pair and the scenario-only merchants side by side ####

# Print the full catalogue rows of the merchants that matter for the lookalike question.
print("--- PixelHarbor, PixelHarbour and the other merchants used only in scenarios ---")
print(
    merchant_overview
    .query("merchant_id in ['ME0022', 'ME0059', 'ME0024', 'ME0023', 'ME0026', 'ME0027', 'ME0029', 'ME0058', 'ME0060', 'ME0053']")
    [[
        "merchant_id", "merchant_name", "merchant_category", "merchant_mcc", "merchant_country", "merchant_city",
        "availability", "history_rows", "distinct_cards", "scenario_purchases",
    ]]
    .to_string(index=False)
)
print()

# Show the gaps in the merchant numbering, since identifiers are not contiguous.
all_numbers = set(range(1, int(merchants["merchant_id"].str[2:].astype(int).max()) + 1))
used_numbers = set(merchants["merchant_id"].str[2:].astype(int))
print("--- Merchant numbers that do not exist ---")
print(sorted(all_numbers - used_numbers))
print()









#### Step 5: Currencies and countries per merchant ####

# List the merchants billed in more than one currency, since currency does not follow the merchant's country.
currency_per_merchant = (
    authorization_history
    .groupby(["merchant_id", "merchant_name", "merchant_country", "currency"])
    .size()
    .unstack("currency", fill_value=0)
    .reset_index()
)
print("--- Foreign merchants and the currencies they billed in ---")
print(currency_per_merchant.query("merchant_country != 'CH'").to_string(index=False))
print()
