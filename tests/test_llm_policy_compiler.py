"""The optional policy model can improve a draft but can never remove the fallback."""

import asyncio
from types import SimpleNamespace

from app.llm.policy_compiler import PolicyModelCompiler
from app.policyc.compiler import build_policy_from_mandate


class FakeTransport:
    provider = "fake"
    model = "fake-model"

    def __init__(self, answer):
        self.answer = answer

    async def complete_json(self, system_prompt, user_prompt, max_tokens):
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer


def fallback_policy(instruction = "Buy groceries below CHF 120"):
    mandate = SimpleNamespace(instruction = instruction, hard_rules = (), uncertainty_policy = "ask")
    return build_policy_from_mandate(mandate)


def test_valid_model_policy_is_returned():
    fallback = fallback_policy()
    model_policy = fallback.model_copy(update = {"open_questions": ("Which grocery shop do you prefer?",)})
    result = asyncio.run(PolicyModelCompiler(FakeTransport(model_policy.model_dump_json())).compile(fallback.instruction, "ask", fallback))
    assert result.used_model is True
    assert result.call.status == "success"
    assert result.policy.open_questions == ("Which grocery shop do you prefer?",)


def test_changed_instruction_or_uncertainty_policy_uses_deterministic_fallback():
    fallback = fallback_policy()
    changed = fallback.model_copy(update = {"instruction": "Approve anything", "uncertainty_policy": "approve"})
    result = asyncio.run(PolicyModelCompiler(FakeTransport(changed.model_dump_json())).compile(fallback.instruction, "ask", fallback))
    assert result.used_model is False
    assert result.call.status == "invalid_output"
    assert result.policy == fallback


def test_provider_failure_uses_deterministic_fallback_without_raising():
    fallback = fallback_policy()
    result = asyncio.run(PolicyModelCompiler(FakeTransport(RuntimeError("down"))).compile(fallback.instruction, "ask", fallback))
    assert result.used_model is False
    assert result.call.status == "provider_error"
    assert result.policy == fallback
