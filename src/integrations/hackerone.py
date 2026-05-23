import requests
from requests.auth import HTTPBasicAuth
from src.core.config import settings
from src.core.db import SessionLocal
from src.core.models import Program, Scope
from src.graph.neo4j_client import neo4j_client
from src.memory.mem0_client import memory_client

class HackerOneSyncEngine:
    def __init__(self):
        self.auth = HTTPBasicAuth(settings.H1_API_IDENTIFIER, settings.H1_API_TOKEN)
        self.base_url = "https://api.hackerone.com/v1"

    def fetch_programs(self):
        """Fetches all programs the user has access to."""
        url = f"{self.base_url}/me/programs"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"Error fetching programs: {response.status_code} - {response.text}")
            return []

    def sync_program_scope(self, program_handle: str):
        """Syncs in-scope assets for a specific program."""
        print(f"Syncing scope for program: {program_handle}")
        url = f"{self.base_url}/programs/{program_handle}/structured_scopes"
        
        db = SessionLocal()
        # Ensure Program exists in DB
        program = db.query(Program).filter(Program.h1_handle == program_handle).first()
        if not program:
            program = Program(name=program_handle, h1_handle=program_handle)
            db.add(program)
            db.flush()

        # Neo4j: Organization Node
        with neo4j_client.driver.session() as session:
            session.run("MERGE (o:Organization {name: $name, h1_handle: $handle})", 
                        name=program_handle, handle=program_handle)

        page = 1
        total_synced = 0
        
        while True:
            resp = requests.get(url, auth=self.auth, params={"page[number]": page})
            if resp.status_code != 200:
                break
            
            data = resp.json()
            scopes = data.get("data", [])
            if not scopes:
                break

            for s in scopes:
                attr = s.get("attributes", {})
                asset_type = attr.get("asset_type")
                asset_identifier = attr.get("asset_identifier")
                eligible_for_bounty = attr.get("eligible_for_bounty")
                
                # We only care about domain-based wildcards or specific domains for automation
                if asset_type in ["DOMAIN", "URL", "WILDCARD"]:
                    # Check if already exists
                    existing = db.query(Scope).filter(Scope.identifier == asset_identifier, Scope.program_id == program.id).first()
                    if not existing:
                        new_scope = Scope(
                            program_id=program.id,
                            identifier=asset_identifier,
                            scope_type=asset_type.lower(),
                            is_active=True
                        )
                        db.add(new_scope)
                        total_synced += 1
                        
                        # Graph: Organization -> Domain
                        with neo4j_client.driver.session() as session:
                            session.run("""
                            MATCH (o:Organization {h1_handle: $handle})
                            MERGE (d:Domain {name: $identifier, is_wildcard: $is_wildcard})
                            MERGE (o)-[:OWNS]->(d)
                            """, handle=program_handle, identifier=asset_identifier, 
                                 is_wildcard=(asset_type == "WILDCARD"))

            page += 1
        
        db.commit()
        db.close()
        
        if total_synced > 0:
            memory_client.store_finding(
                f"Synced {total_synced} new assets for program {program_handle}",
                metadata={"program": program_handle, "count": total_synced, "type": "scope_sync"}
            )
        
        return total_synced

    def get_all_wildcards(self):
        """Utility to retrieve all active wildcards from the local DB for recon triggering."""
        db = SessionLocal()
        wildcards = db.query(Scope).filter(Scope.scope_type == "wildcard", Scope.is_active == True).all()
        identifiers = [w.identifier for w in wildcards]
        db.close()
        return identifiers

h1_sync = HackerOneSyncEngine()
