# Script: facts.py
# Purpose: Turn the amounts, the cart lines and the shop of one purchase message into exact decimals and typed facts that every guard can compare safely
# Author: Andrés Gallardo
# Date: September 2026

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Tuple

from app.engine.shop_text import LineTextFacts, read_line_text_facts
from app.policyc.instruction_text import read_words









#### Step 1: Turn one number into money ####

# State the smallest unit of money, which is one hundredth
ONE_HUNDREDTH = Decimal("0.01")



# Build the decimal from the text of the number, so a float such as 0.1 + 0.2 never carries its binary noise along.
# Round to two places with half-even rounding, where a value exactly between two hundredths goes to the even one.
def to_money(value):
    return Decimal(str(value)).quantize(ONE_HUNDREDTH, rounding = ROUND_HALF_EVEN)









#### Step 2: Define the fact sheet ####

# Hold one line of the cart, where unit_price and line_total are in the currency of the line and line_total is unit_price times quantity.
# The name is written by the shop. name_words holds its words in lower case and in singular form, which is the only form a guard compares.
# text_facts holds what the sentence of the shop about this line says, as typed facts, and the sentence itself is not kept.
# No identifier is kept, so no guard can decide on one.
@dataclass(frozen = True)
class LineFact:
    line_no: int
    item_name: str
    item_category: str
    quantity: int
    unit_price: Decimal
    currency: str
    line_total: Decimal
    text_facts: LineTextFacts
    name_words: Tuple[str, ...]



# Hold what the platform states about the shop. The name is written by the shop and is kept for display only.
# recurring_capable is a real boolean and says whether the shop can bill on a recurring basis.
# No identifier of the shop is kept, so no guard can decide on one.
@dataclass(frozen = True)
class MerchantFact:
    merchant_name: str
    merchant_category: str
    merchant_country: str
    recurring_capable: bool



# Hold the amounts of one purchase as exact decimals, together with the currency of the purchase, the lines of the cart and the shop.
# billing_amount_chf is the amount in Swiss francs, while amount, items_subtotal and delivery_fee are in the purchase currency.
@dataclass(frozen = True)
class FactSheet:
    billing_amount_chf: Decimal
    amount: Decimal
    items_subtotal: Decimal
    delivery_fee: Decimal
    currency: str
    lines: Tuple[LineFact, ...]
    merchant: MerchantFact









#### Step 3: Build the fact sheet of one purchase ####

# Read one line of the cart, multiply the exact unit price by the quantity, and read the sentence of the shop into typed facts
def build_line_fact(cart_item):
    unit_price = to_money(cart_item.unit_price)
    return LineFact(
        line_no = cart_item.line_no,
        item_name = cart_item.item_name,
        item_category = cart_item.item_category,
        quantity = cart_item.quantity,
        unit_price = unit_price,
        currency = cart_item.currency,
        line_total = to_money(unit_price * cart_item.quantity),
        text_facts = read_line_text_facts(cart_item.item_details),
        name_words = read_words(cart_item.item_name),
    )



# Map the two texts the message may carry for a yes or no fact to a real boolean
BOOLEAN_BY_TEXT = {"true": True, "false": False}



# Read a yes or no fact from its text. Only the exact texts "true" and "false" count, and anything else stops the decision,
# because Python would read every text that is not empty as true, the text "false" included.
def read_true_or_false(text):
    if not isinstance(text, str) or text not in BOOLEAN_BY_TEXT:
        raise ValueError("Expected the text true or false, found " + repr(text))
    return BOOLEAN_BY_TEXT[text]



# Read what the platform states about the shop, without any identifier
def build_merchant_fact(merchant):
    return MerchantFact(
        merchant_name = merchant.merchant_name,
        merchant_category = merchant.merchant_category,
        merchant_country = merchant.merchant_country,
        recurring_capable = read_true_or_false(merchant.recurring_capable),
    )



# Read the amounts, the cart lines and the shop of the purchase and nothing else, so the fact sheet depends on no clock and on no identifier
def build_fact_sheet(event):
    return FactSheet(
        billing_amount_chf = to_money(event.authorization.billing_amount_chf),
        amount = to_money(event.authorization.amount),
        items_subtotal = to_money(event.authorization.items_subtotal),
        delivery_fee = to_money(event.authorization.delivery_fee),
        currency = event.authorization.currency,
        lines = tuple(build_line_fact(cart_item) for cart_item in event.authorization.items),
        merchant = build_merchant_fact(event.authorization.merchant),
    )
