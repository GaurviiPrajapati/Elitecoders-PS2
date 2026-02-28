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

        # Add Output Personas
        if self.output_mode == "TECHNICAL MODE":
            prompt += "\nOutput Style: TECHNICAL MODE\nUse precise technical jargon, provide deep details, code/equations where applicable, and maintain a highly analytical tone.\n"
        elif self.output_mode == "EXECUTIVE MODE":
            prompt += "\nOutput Style: EXECUTIVE MODE\nFocus on high-level summaries, ROI, strategic impact, and concise bullet points. Avoid unnecessary technical weeds.\n"
        elif self.output_mode == "AUDIT MODE":
            prompt += "\nOutput Style: AUDIT MODE\nFocus strictly on compliance, risks, evidence, and verification steps. Be extremely meticulous and objective.\n"
        elif self.output_mode == "CLIENT SUMMARY MODE":
            prompt += "\nOutput Style: CLIENT SUMMARY MODE\nUse accessible language, focus on benefits and practical implications. Be empathetic and reassuring without jargon.\n"

        return prompt