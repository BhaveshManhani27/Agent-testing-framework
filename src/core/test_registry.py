import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List
from src.observability.log_config import get_logger

logger = get_logger(__name__)


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
                logger.warning("Skipping invalid test case: %s — %s", item.get('id', '?'), e)

        logger.info("Loaded %d test cases from %s", len(self.test_cases), self.path)

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
        logger.info("Test Suite Summary:")
        for cat, count in cats.items():
            logger.info("   %s %d tests", f"{cat:<15}", count)
        logger.info("   %s %d tests", f"{'TOTAL':<15}", len(self.test_cases))