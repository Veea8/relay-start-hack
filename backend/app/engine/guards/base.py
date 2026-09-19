# Script: base.py
# Purpose: Define what every guard receives, what every guard must offer and the placeholder for a guard without logic
# Author: Andrés Gallardo
# Date: September 2026

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from app.models.decision import GuardFamily, GuardResult, GuardVerdict, ReasonCode
from app.models.events import AuthorizationEvent
from app.models.policy import InternalPolicy









#### Step 1: Define the input of a decision ####

# Hold everything a guard may look at, where state is an opaque value that nothing reads yet
@dataclass(frozen = True)
class DecisionInput:
    event: AuthorizationEvent
    policy: InternalPolicy
    state: Any = None









#### Step 2: Define what every guard must offer ####

# Describe a guard, which carries its number, its id and its family and answers one purchase with one result.
# earlier_results maps the id of every guard that already ran to its result and cannot be changed.
# A guard fills in its own number, id and family, and the pipeline fills in the running time.
class Guard(Protocol):

    guard_number: int
    guard_id: str
    family: GuardFamily

    def check(self, decision_input: DecisionInput, earlier_results: Mapping[str, GuardResult]) -> GuardResult:
        ...









#### Step 3: Define the placeholder for a guard without logic ####

# Stand in for a guard that is not built yet, which answers SKIP and therefore never changes a decision
@dataclass(frozen = True)
class PlaceholderGuard:
    guard_number: int
    guard_id: str
    family: GuardFamily

    # Answer SKIP with the reason that the guard is not built, without evidence and without a message
    def check(self, decision_input, earlier_results):
        return GuardResult(
            guard_number = self.guard_number,
            guard_id = self.guard_id,
            family = self.family,
            verdict = GuardVerdict.SKIP,
            reason_code = ReasonCode.GUARD_NOT_BUILT,
        )
