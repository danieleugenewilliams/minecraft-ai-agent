#!/usr/bin/env python3
"""
Setup script for Minecraft AI Agent
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Main setup function"""
    print("🎮 Setting up Minecraft AI Agent...")
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not in a virtual environment!")
        print("   Consider running: python3 -m venv venv && source venv/bin/activate")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Setup failed during dependency installation")
        return False
    
    # Create config directory and default config
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    if not (config_dir / "default.yaml").exists():
        print("📝 Creating default configuration...")
        # The config will be auto-generated when the app runs
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Ensure Minecraft is running and iPhone mirroring is active")
    print("2. Run the agent: python main.py")
    print("3. Use --dry-run flag for testing: python main.py --dry-run")
    print("4. Use --debug flag for verbose logging: python main.py --debug")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)