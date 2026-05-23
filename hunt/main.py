# pyrefly: ignore [missing-import]
from hunt.cli.app import app
# pyrefly: ignore [missing-import]
from hunt.core.plugin_loader import plugin_loader
import asyncio

def main():
    """Main entry point for the Hunt framework."""
    # Load configuration
    
    
    # Initialize plugins
    plugin_loader.load_plugins()
    
    # Start CLI
    app()

if __name__ == "__main__":
    main()
