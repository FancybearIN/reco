#!/bin/bash
# RESET_SYSTEM.sh - Clean DBs and queues for a fresh target

echo "[!] WARNING: This will wipe all graph data and redis queues!"
read -p "Are you sure? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[*] Flushing Redis..."
    redis-cli -h localhost flushall
    
    echo "[*] Wiping Neo4j Data..."
    # Using cypher-shell via docker if available, or direct API
    docker exec -it recon-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) DETACH DELETE n"
    
    echo "[+] System Reset Complete."
fi
