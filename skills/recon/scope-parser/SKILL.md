# Skill: Scope Parser

Automates the retrieval and parsing of bug bounty target scopes, primarily focusing on HackerOne's structured scope API.

## Capabilities
- **Fetch HackerOne Scope**: Retrieves the full structured scope for a given program handle.
- **Parse Assets**: Categorizes assets by type (URL, Domain, IP, etc.) and scope status.
- **Export to JSON**: Saves the parsed scope to a file for use by other tools.
- **Asset List Extraction**: Converts parsed JSON scope into a simple text list of in-scope assets.

## Usage

### Environment Variables
Set the following environment variables for API authentication:
- `H1_API_IDENTIFIER`: Your HackerOne API Identifier.
- `H1_API_TOKEN`: Your HackerOne API Token.
- `H1_PROGRAM_HANDLE`: (Optional) Default program handle (e.g., `att`).

### Command Line
1. **Fetch and Parse**:
   ```bash
   python3 scripts/fetch_h1_scope.py --handle <program_handle> --output scope.json
   ```
2. **Extract Asset List**:
   ```bash
   python3 scripts/json_to_assets.py scope.json --output in_scope_assets.txt
   ```

## Integration
This skill provides the foundation for Phase 1 (Recon) by ensuring the target surface is accurately defined and up-to-date.
