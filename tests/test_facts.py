# Script: test_facts.py
# Purpose: Check that amounts become exact decimals with half-even rounding and that the fact sheet of a purchase cannot be changed
# Author: Andrés Gallardo
# Date: September 2026

import dataclasses
from decimal import Decimal

import pytest

from app.engine.facts import FactSheet, build_fact_sheet, to_money
from app.models.events import read_purchase_message









#### Step 1: Check the conversion of one number ####

# Check that a number becomes an exact decimal with two places, without the binary noise of a float
@pytest.mark.parametrize(
    "value, expected_money",
    [
        (44.5, Decimal("44.50")),
        (8925.73, Decimal("8925.73")),
        (0.1 + 0.2, Decimal("0.30")),
        (20, Decimal("20.00")),
        ("2.665", Decimal("2.66")),
        ("2.675", Decimal("2.68")),
    ],
)
def test_number_becomes_exact_money(value, expected_money):
    money = to_money(value)
    assert money == expected_money
    assert isinstance(money, Decimal)
    assert money.as_tuple().exponent == -2









#### Step 2: Check the fact sheet ####

# Check the amounts of the example message field by field
def test_fact_sheet_of_the_example_message(example_message):
    fact_sheet = build_fact_sheet(read_purchase_message(example_message))
    assert isinstance(fact_sheet, FactSheet)
    assert fact_sheet.billing_amount_chf == Decimal("20.00")
    assert fact_sheet.amount == Decimal("20.00")
    assert fact_sheet.items_subtotal == Decimal("18.00")
    assert fact_sheet.delivery_fee == Decimal("2.00")
    assert fact_sheet.currency == "CHF"



# Check that a fact sheet cannot be changed after it was built
def test_fact_sheet_is_frozen(example_message):
    fact_sheet = build_fact_sheet(read_purchase_message(example_message))
    with pytest.raises(dataclasses.FrozenInstanceError):
        fact_sheet.billing_amount_chf = Decimal("1.00")
