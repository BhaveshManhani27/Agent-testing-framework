"""Tests for adversarial generator — template mutation, catalog loading."""

import pytest
from src.core.test_registry import TestCase
from src.adversarial.generator import (
    AdversarialGenerator, _apply_template, _build_mutation_prompt,
    MUTATION_TYPES, TEMPLATES
)
from src.adversarial.catalog import get_catalog


class TestTemplateMutation:
    def test_prompt_injection_template(self):
        result = _apply_template("What is 2+2?", "prompt_injection")
        assert "2+2" in result
        assert len(result) > len("What is 2+2?")  # template adds content

    def test_role_confusion_template(self):
        result = _apply_template("Hello", "role_confusion")
        assert "Hello" in result

    def test_all_mutation_types_have_templates(self):
        for mt in MUTATION_TYPES:
            assert mt in TEMPLATES, f"Missing template for {mt}"
            result = _apply_template("test input", mt)
            assert "test input" in result


class TestMutationPrompt:
    def test_prompt_contains_original(self):
        prompt = _build_mutation_prompt("Hello", "prompt_injection")
        assert "Hello" in prompt

    def test_prompt_contains_instructions(self):
        prompt = _build_mutation_prompt("Hello", "prompt_injection")
        assert "injection" in prompt.lower() or "hijack" in prompt.lower()

    def test_all_types_build_prompts(self):
        for mt in MUTATION_TYPES:
            prompt = _build_mutation_prompt("test", mt)
            assert len(prompt) > 50  # meaningful prompt


class TestAdversarialGenerator:
    def test_template_mode_generates_variants(self):
        gen = AdversarialGenerator(llm_mode=False)
        tc = TestCase(
            id="TC001",
            category="normal",
            severity="low",
            input="What is the capital of France?",
            expected_behavior="Should answer Paris",
            pass_criteria="contains_answer",
        )
        variants = gen.mutate(tc, mutation_types=["prompt_injection"])
        assert len(variants) == 1
        assert variants[0].mutation_type == "prompt_injection"
        assert variants[0].test_case.category == "adversarial"
        assert variants[0].test_case.pass_criteria == "should_refuse"

    def test_generates_all_types(self):
        gen = AdversarialGenerator(llm_mode=False)
        tc = TestCase(
            id="TC001",
            category="normal",
            severity="low",
            input="Hello",
            expected_behavior="test",
            pass_criteria="no_crash",
        )
        variants = gen.mutate(tc)
        assert len(variants) == 5  # all 5 mutation types
        types = {v.mutation_type for v in variants}
        assert types == set(MUTATION_TYPES)

    def test_batch_mutation(self):
        gen = AdversarialGenerator(llm_mode=False)
        cases = [
            TestCase(
                id=f"TC{i:03d}", category="normal", severity="low",
                input=f"Question {i}", expected_behavior="test",
                pass_criteria="no_crash",
            )
            for i in range(3)
        ]
        all_variants = gen.mutate_batch(cases, mutation_types=["prompt_injection"])
        assert len(all_variants) == 3  # one per input

    def test_generated_count(self):
        gen = AdversarialGenerator(llm_mode=False)
        tc = TestCase(
            id="TC001", category="normal", severity="low",
            input="test", expected_behavior="test", pass_criteria="no_crash",
        )
        gen.mutate(tc, mutation_types=["prompt_injection", "role_confusion"])
        assert gen.generated_count == 2


class TestCatalog:
    def test_catalog_returns_test_cases(self):
        catalog = get_catalog()
        assert len(catalog) > 0
        for tc in catalog:
            assert isinstance(tc, TestCase)
            assert tc.category == "adversarial"
