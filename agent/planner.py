from llm.ollama_client import OllamaClient
from llm.prompts import PLANNER_PROMPT, BASE_SYSTEM_PROMPT


class Planner:
    """
    Responsible for turning a user request into a step-by-step plan.
    """

    def __init__(self, llm: OllamaClient):
        self.llm = llm

    def create_plan(self, user_request: str) -> list[str]:
        """
        Generate a numbered plan from a user request.
        """

        prompt = f"""
User request:
{user_request}

Produce a numbered step-by-step plan.
"""

        response = self.llm.generate(
            prompt=prompt,
            system=f"{BASE_SYSTEM_PROMPT}\n\n{PLANNER_PROMPT}",
            temperature=0.1,
        )

        return self._parse_plan(response)

    def _parse_plan(self, text: str) -> list[str]:
        """
        Convert model output into a clean list of steps.
        """

        steps = []
        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            # Match "1. step" or "1) step"
            if line[0].isdigit():
                step = line.lstrip("0123456789.). ").strip()
                if step:
                    steps.append(step)

        return steps
