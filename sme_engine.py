import json

class SMEEngine:
    def __init__(self, domain_path):
        self.load_domain(domain_path)

    def load_domain(self, domain_path):
        with open(domain_path, "r") as f:
            self.domain = json.load(f)

    def switch_domain(self, domain_path):
        self.load_domain(domain_path)

    def build_system_prompt(self):
        prompt = f"""
You are acting as a Subject Matter Expert.

Domain: {self.domain['domain_name']}

Persona:
{self.domain['persona']}

Scope:
{', '.join(self.domain['scope'])}
"""

        # Add decision tree if present
        if "decision_tree" in self.domain and self.domain["decision_tree"]:
            prompt += "\nDecision Process:\n"
            for step in self.domain["decision_tree"]:
                prompt += f"- {step}\n"

        # Add citation rules
        if "citation_rules" in self.domain:
            if self.domain["citation_rules"].get("required", False):
                prompt += f"""
All factual claims must include citation in format:
{self.domain['citation_rules'].get('format', '')}
"""

        # Add output structure if defined
        if "output_format" in self.domain:
            prompt += "\nRequired Output Structure:\n"
            for item in self.domain["output_format"].get("structure", []):
                prompt += f"- {item}\n"

        # Add out-of-scope behavior
        if "out_of_scope_response" in self.domain:
            prompt += f"""
If query is outside domain scope, respond with:
{self.domain['out_of_scope_response']}
"""

        return prompt