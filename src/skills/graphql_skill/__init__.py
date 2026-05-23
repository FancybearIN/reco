from typing import Dict, Any

from .schema_detection import schema_detector
from .introspection_engine import introspection_engine
from .batching_engine import batching_engine
from .alias_overloading import alias_engine
from .field_suggestions import suggestions_engine
from .auth_mapping import auth_mapping_engine
from .object_reference_analysis import object_ref_engine
from .admin_field_detector import admin_detector
from .persisted_query_analyzer import apq_engine
from .graphql_ws_detector import ws_detector
from .bola_heuristics import bola_engine

from src.memory.mem0_client import memory_client
from src.intelligence.chain_verifier import chain_verifier
from src.graph.neo4j_client import neo4j_client

class GraphQLSkillEngine:
    """
    Orchestrates the deep offensive GraphQL skill execution.
    Focuses on chaining findings and evaluating authorization, rather than blindly fuzzing.
    """
    def __init__(self):
        pass

    def evaluate_target(self, target_domain: str, js_data: dict = None):
        """
        Executes the full GraphQL offensive methodology against a target.
        """
        print(f"Executing Elite GraphQL Skill against {target_domain}")
        base_url = f"https://{target_domain}"
        
        # 1. Detection
        detection_res = schema_detector.detect_endpoint(base_url)
        if not detection_res["found"]:
            print(f"No standard GraphQL endpoints found on {target_domain}")
            return
            
        endpoints = detection_res["endpoints"]
        memory_client.store_finding(
            f"GraphQL endpoints discovered: {endpoints}",
            metadata={"domain": target_domain, "type": "graphql_endpoint_detected"}
        )
        
        for endpoint in endpoints:
            self._analyze_endpoint(target_domain, endpoint, js_data)

    def _analyze_endpoint(self, domain: str, endpoint: str, js_data: dict):
        findings = []
        
        # 2. Introspection
        intro_res = introspection_engine.extract_schema(endpoint)
        schema = intro_res.get("schema")
        
        if intro_res["introspection_enabled"]:
            findings.append({"type": "Introspection Enabled", "confidence": 1.0})
            
            # Deep Schema Analysis
            admin_res = admin_detector.analyze_schema(schema)
            if admin_res["count"] > 0:
                findings.append({"type": "Sensitive/Admin Fields Exposed", "confidence": 0.9, "details": admin_res})
                
            bola_res = bola_engine.analyze_references(schema)
            if bola_res["high_priority_count"] > 0:
                findings.append({"type": "BOLA Candidates Identified", "confidence": 0.8, "details": bola_res})
                
            auth_map = auth_mapping_engine.map_boundaries(schema)
            obj_refs = object_ref_engine.analyze_references(schema)
            
            # Store extracted schema intel in Mem0
            memory_client.store_finding(
                f"GraphQL Schema extracted via {intro_res['method']}. Found {admin_res['count']} sensitive fields.",
                metadata={"domain": domain, "endpoint": endpoint, "type": "graphql_schema_extracted"}
            )
        else:
            findings.append({"type": "Introspection Disabled", "confidence": 1.0})
            # 3. If no introspection, check Field Suggestions
            sugg_res = suggestions_engine.test_suggestions(endpoint)
            if sugg_res["vulnerable"]:
                findings.append({"type": "Field Suggestions Leaking Schema", "confidence": sugg_res["confidence"]})
        
        # 4. Infrastructure & Gateway Weaknesses
        batch_res = batching_engine.test_array_batching(endpoint)
        if batch_res["vulnerable"]:
             findings.append({"type": "Array Batching Enabled (DoS/Bruteforce)", "confidence": batch_res["confidence"]})
             
        alias_res = alias_engine.test_alias_overloading(endpoint)
        if alias_res["vulnerable"]:
            findings.append({"type": "Alias Overloading (DoS)", "confidence": alias_res["confidence"]})
            
        apq_res = apq_engine.detect_apq(endpoint)
        if apq_res["apq_enabled"]:
            findings.append({"type": "Automatic Persisted Queries Enabled", "confidence": apq_res["confidence"]})
            
        if js_data and ws_detector.detect_ws(js_data.get("content", ""))["ws_supported"]:
            findings.append({"type": "GraphQL Subscriptions over WS", "confidence": 0.8})

        # 5. Chain Reasoning & Prioritization
        self._evaluate_graphql_chains(domain, endpoint, findings)

    def _evaluate_graphql_chains(self, domain: str, endpoint: str, findings: list):
        """
        Builds probability-weighted attack chains based on GraphQL heuristics.
        """
        chain_steps = []
        
        has_intro = any(f["type"] == "Introspection Enabled" for f in findings)
        has_admin = any(f["type"] == "Sensitive/Admin Fields Exposed" for f in findings)
        has_bola = any(f["type"] == "BOLA Candidates Identified" for f in findings)
        
        if has_intro:
            chain_steps.append({"type": "GraphQL Introspection", "confidence": 1.0})
            if has_admin:
                chain_steps.append({"type": "Admin Field Extraction", "confidence": 0.9})
                chain_steps.append({"type": "Authorization Bypass", "confidence": 0.4, "required_evidence": "Successful unauthorized mutation execution"})
            elif has_bola:
                chain_steps.append({"type": "BOLA Enumeration", "confidence": 0.8})
                chain_steps.append({"type": "IDOR Exploitation", "confidence": 0.5, "required_evidence": "Cross-tenant data extraction via ID manipulation"})

        if chain_steps:
            res = chain_verifier.verify_chain(domain, chain_steps)
            if res["is_viable"]:
                memory_client.store_finding(
                    f"Viable GraphQL Attack Chain identified on {endpoint}. Probability: {res['chain_probability']:.2f}",
                    metadata={"domain": domain, "type": "graphql_attack_chain"}
                )

graphql_skill_engine = GraphQLSkillEngine()
