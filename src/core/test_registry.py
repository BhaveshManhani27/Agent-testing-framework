import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List


class TestCase(BaseModel):
    id: str
    category: str                              
    severity: str                              
    input: str
    expected_behavior: str
    pass_criteria: str                         
    expected_keywords: Optional[List[str]] = []
    forbidden_keywords: Optional[List[str]] = []


class TestRegistry:

    def __init__(self, path: str = "data/test_cases.yaml"):
        self.path = Path(path)
        self.test_cases: List[TestCase] = []
        self._load()

    def _load(self):
        """Read YAML file and validate each test case using Pydantic."""
        with open(self.path, "r") as f:
            raw = yaml.safe_load(f)

        for item in raw:
            try:
                self.test_cases.append(TestCase(**item))
            except Exception as e:
                print(f"Skipping invalid test case: {item.get('id', '?')} — {e}")

        print(f"Loaded {len(self.test_cases)} test cases from {self.path}")

    def get_all(self) -> List[TestCase]:
        return self.test_cases

    def get_by_category(self, category: str) -> List[TestCase]:
        return [tc for tc in self.test_cases if tc.category == category]

    def get_by_severity(self, severity: str) -> List[TestCase]:
        return [tc for tc in self.test_cases if tc.severity == severity]

    def summary(self):
        """Print a quick breakdown of the test suite."""
        from collections import Counter
        cats = Counter(tc.category for tc in self.test_cases)
        print("\nTest Suite Summary:")
        for cat, count in cats.items():
            print(f"   {cat:<15} {count} tests")
        print(f"   {'TOTAL':<15} {len(self.test_cases)} tests\n")