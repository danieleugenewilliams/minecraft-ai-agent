#!/usr/bin/env python3
"""
Minecraft AI Agent - Main Entry Point
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minecraft_ai.core.config import Config
from minecraft_ai.core.logger import setup_logger
from minecraft_ai.ai.agent import MinecraftAgent


def main():
    """Main entry point for the Minecraft AI agent"""
    parser = argparse.ArgumentParser(description="Minecraft AI Agent")
    parser.add_argument("--config", "-c", 
                       help="Configuration file path", 
                       default="config/default.yaml")
    parser.add_argument("--debug", "-d", 
                       action="store_true", 
                       help="Enable debug logging")
    parser.add_argument("--dry-run", 
                       action="store_true", 
                       help="Run without actual input actions")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(debug=args.debug)
    
    try:
        # Load configuration
        config = Config(args.config)
        logger.info("Starting Minecraft AI Agent...")
        
        # Initialize and run agent
        agent = MinecraftAgent(config, dry_run=args.dry_run)
        agent.run()
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()