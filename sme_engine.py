import json

class SMEEngine:
    def __init__(self, domain_path):
        self.output_mode = "DEFAULT"
        self.load_domain(domain_path)

    def load_domain(self, domain_path):
        with open(domain_path, "r") as f:
            self.domain = json.load(f)

    def switch_domain(self, domain_path):
        self.load_domain(domain_path)

    def set_output_mode(self, mode):
        self.output_mode = mode

    def build_system_prompt(self):
        prompt = f"""
You are acting as a Subject Matter Expert.

Domain: {self.domain['domain_name']}

Persona:
{self.domain['persona']}

Scope:
{', '.join(self.domain['scope'])}
"""

        if "decision_tree" in self.domain and self.domain["decision_tree"]:
            prompt += "\nDecision Process:\n"
            for step in self.domain["decision_tree"]:
                prompt += f"- {step}\n"

        prompt += """
            Grounding & Citation Rules:
            - If internal knowledge is insufficient, use the WebSearch tool.
            - You MUST extract source URLs from tool results.
            - Every factual claim must include citation in format: [SOURCE: <URL>]
            - After your answer, include a separate section:

            Sources:
            - <URL 1>
            - <URL 2>

            - If sufficient evidence is not available, clearly state that.
            """
        return prompt
    