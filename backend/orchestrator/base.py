from __future__ import annotations

from abc import ABC, abstractmethod


class TaskHandler(ABC):
    task_type = "other"

    @abstractmethod
    def detect(self, text: str) -> float:
        """Return confidence in [0, 1]."""

    @abstractmethod
    def clarify_schema(self, text: str) -> dict:
        """Return ClarifyFormSchema dict."""

    @abstractmethod
    def build_spec(self, text: str, answers: dict) -> dict:
        """Build TaskSpec dict from text + clarify answers."""

    @abstractmethod
    def prompts(self, spec: dict, route: dict) -> list[dict]:
        """Return generated prompts for candidate executors."""

    @abstractmethod
    def validate(self, spec: dict, output: str) -> dict:
        """Return ValidationReport dict."""

    def postprocess(self, output: str) -> str:
        return output
