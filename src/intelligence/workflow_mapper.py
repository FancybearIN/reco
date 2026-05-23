import os
from typing import List, Dict, Any

class WorkflowMapper:
    """
    Autonomous Methodology-Aware Workflow Selector.
    Maps findings to specific offensive methodologies and triggers native tool chains.
    """
    def __init__(self):
        # Triggers based on technology, keywords, or specific findings
        self.triggers = {
            "tech:graphql": {
                "methodology": "graphql_exploitation",
                "workflows": ["graphql_deep_dive", "auth_mapping"]
            },
            "tech:swagger": {
                "methodology": "api_enumeration",
                "workflows": ["swagger_extraction", "fuzz_hidden_routes"]
            },
            "tech:wordpress": {
                "methodology": "cms_exploitation",
                "workflows": ["wpscan_native", "plugin_enumeration"]
            },
            "finding:leaked_secret": {
                "methodology": "credential_abuse",
                "workflows": ["secret_validation", "pivoting_recon"]
            },
            "feature:upload": {
                "methodology": "file_upload_exploitation",
                "workflows": ["upload_polyglot_test", "mime_confusion"]
            },
            "feature:auth": {
                "methodology": "auth_bypass",
                "workflows": ["jwt_analysis", "oauth_misconfig_check"]
            }
        }

        # Workflows: Ordered lists of native tool executions and internal actions
        self.workflow_definitions = {
            "graphql_deep_dive": [
                {"action": "trigger_graphql_skill", "params": {}},
                {"tool": "inql", "args": ["-t", "{target}"]}
            ],
            "swagger_extraction": [
                {"action": "trigger_swagger_skill", "params": {}},
                {"tool": "katana", "args": ["-u", "{target}", "-silent", "-jc"]}
            ],
            "api_fuzzing": [
                {"tool": "ffuf", "args": ["-w", "wordlists/api_routes.txt", "-u", "{target}/FUZZ"]},
                {"tool": "arjun", "args": ["-u", "{target}"]}
            ],
            "passive_recon_wide": [
                {"tool": "subfinder", "args": ["-d", "{target}", "-silent", "-all"]},
                {"tool": "amass", "args": ["enum", "-passive", "-d", "{target}"]},
                {"tool": "assetfinder", "args": ["--subs-only", "{target}"]}
            ],
            "active_recon_discovery": [
                {"tool": "puredns", "args": ["resolve", "{target}_list.txt", "-r", "resolvers.txt"]},
                {"tool": "dnsx", "args": ["-d", "{target}", "-resp", "-a", "-cname"]}
            ],
            "endpoint_mining": [
                {"tool": "gau", "args": ["{target}"]},
                {"tool": "waymore", "args": ["-i", "{target}", "-mode", "U"]},
                {"tool": "katana", "args": ["-u", "{target}", "-d", "5"]}
            ]
        }

    def select_workflows(self, finding_type: str, data: dict) -> List[str]:
        """
        Autonomously infers the best next workflows based on the finding.
        """
        selected = []
        
        # Exact match
        if finding_type in self.triggers:
            selected.extend(self.triggers[finding_type]["workflows"])
            
        # Partial match for tech strings (e.g., 'tech:GraphQL' or 'tech:Apollo')
        if finding_type.startswith("tech:"):
            tech_name = finding_type.split(":")[1].lower()
            if "graphql" in tech_name:
                selected.extend(self.triggers["tech:graphql"]["workflows"])
            if "swagger" in tech_name or "openapi" in tech_name:
                selected.extend(self.triggers["tech:swagger"]["workflows"])

        # Contextual inference
        if data.get("has_parameters") and "api" in data.get("url", "").lower():
            selected.append("api_fuzzing")

        return list(set(selected)) # Deduplicate

    def get_tool_chain(self, workflow_name: str, target: str) -> List[Dict[str, Any]]:
        """
        Returns the concrete tool chain for a selected workflow.
        """
        base_chain = self.workflow_definitions.get(workflow_name, [])
        # Template injection for target
        formatted_chain = []
        for step in base_chain:
            step_copy = step.copy()
            if "args" in step_copy:
                step_copy["args"] = [arg.replace("{target}", target) for arg in step_copy["args"]]
            formatted_chain.append(step_copy)
        return formatted_chain

mapper = WorkflowMapper()
