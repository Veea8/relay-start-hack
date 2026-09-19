# Script: facts.py
# Purpose: Turn the amounts and the cart lines of one purchase message into exact decimals that every guard can compare safely
# Author: Andrés Gallardo
# Date: September 2026

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Tuple









#### Step 1: Turn one number into money ####

# State the smallest unit of money, which is one hundredth
ONE_HUNDREDTH = Decimal("0.01")



# Build the decimal from the text of the number, so a float such as 0.1 + 0.2 never carries its binary noise along.
# Round to two places with half-even rounding, where a value exactly between two hundredths goes to the even one.
def to_money(value):
    return Decimal(str(value)).quantize(ONE_HUNDREDTH, rounding = ROUND_HALF_EVEN)









#### Step 2: Define the fact sheet ####

# Hold one line of the cart, where unit_price and line_total are in the currency of the line and line_total is unit_price times quantity.
# The name is written by the shop and is kept for display only. No identifier is kept, so no guard can decide on one.
@dataclass(frozen = True)
class LineFact:
    line_no: int
    item_name: str
    item_category: str
    quantity: int
    unit_price: Decimal
    currency: str
    line_total: Decimal



# Hold the amounts of one purchase as exact decimals, together with the currency of the purchase and the lines of the cart.
# billing_amount_chf is the amount in Swiss francs, while amount, items_subtotal and delivery_fee are in the purchase currency.
@dataclass(frozen = True)
class FactSheet:
    billing_amount_chf: Decimal
    amount: Decimal
    items_subtotal: Decimal
    delivery_fee: Decimal
    currency: str
    lines: Tuple[LineFact, ...]









#### Step 3: Build the fact sheet of one purchase ####

# Read one line of the cart, and multiply the exact unit price by the quantity
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
    )



# Read the amounts and the cart lines of the purchase and nothing else, so the fact sheet depends on no clock and on no identifier
def build_fact_sheet(event):
    return FactSheet(
        billing_amount_chf = to_money(event.authorization.billing_amount_chf),
        amount = to_money(event.authorization.amount),
        items_subtotal = to_money(event.authorization.items_subtotal),
        delivery_fee = to_money(event.authorization.delivery_fee),
        currency = event.authorization.currency,
        lines = tuple(build_line_fact(cart_item) for cart_item in event.authorization.items),
    )
