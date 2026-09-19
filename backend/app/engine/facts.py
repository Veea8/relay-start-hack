# Script: facts.py
# Purpose: Turn the amounts of one purchase message into exact decimals that every guard can compare safely
# Author: Andrés Gallardo
# Date: September 2026

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal









#### Step 1: Turn one number into money ####

# State the smallest unit of money, which is one hundredth
ONE_HUNDREDTH = Decimal("0.01")



# Build the decimal from the text of the number, so a float such as 0.1 + 0.2 never carries its binary noise along.
# Round to two places with half-even rounding, where a value exactly between two hundredths goes to the even one.
def to_money(value):
    return Decimal(str(value)).quantize(ONE_HUNDREDTH, rounding = ROUND_HALF_EVEN)









#### Step 2: Define the fact sheet ####

# Hold the amounts of one purchase as exact decimals, together with the currency of the purchase.
# billing_amount_chf is the amount in Swiss francs, while amount, items_subtotal and delivery_fee are in the purchase currency.
@dataclass(frozen = True)
class FactSheet:
    billing_amount_chf: Decimal
    amount: Decimal
    items_subtotal: Decimal
    delivery_fee: Decimal
    currency: str









#### Step 3: Build the fact sheet of one purchase ####

# Read the amounts of the purchase and nothing else, so the fact sheet depends on no clock and on no identifier
def build_fact_sheet(event):
    return FactSheet(
        billing_amount_chf = to_money(event.authorization.billing_amount_chf),
        amount = to_money(event.authorization.amount),
        items_subtotal = to_money(event.authorization.items_subtotal),
        delivery_fee = to_money(event.authorization.delivery_fee),
        currency = event.authorization.currency,
    )
