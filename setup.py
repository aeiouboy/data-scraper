#!/usr/bin/env python3
"""
Setup script for HomePro Scraper project
"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str):
    """Run a shell command with error handling"""
    print(f"\n📦 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {description}")
        print(f"Output: {result.stderr}")
        return False
    
    print(f"✅ {description} completed")
    return True


def main():
    """Main setup function"""
    print("🚀 HomePro Scraper Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Error: Python 3.9+ required")
        sys.exit(1)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ Error: .env file not found")
        print("Please copy .env.example to .env and add your credentials")
        sys.exit(1)
    
    # Create virtual environment
    if not Path("venv").exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    
    # Determine pip path
    pip_path = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
    
    # Upgrade pip
    run_command(f"{pip_path} install --upgrade pip", "Upgrading pip")
    
    # Install dependencies
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    print("\n📋 Next steps:")
    print("1. Run the SQL schema in Supabase dashboard:")
    print("   - Go to SQL Editor in your Supabase project")
    print("   - Copy contents of scripts/create_schema.sql")
    print("   - Execute the SQL")
    print("\n2. Activate virtual environment:")
    if os.name != "nt":
        print("   source venv/bin/activate")
    else:
        print("   venv\\Scripts\\activate")
    print("\n3. Test the setup:")
    print("   python -m app.test_connection")
    print("\n✨ Setup complete!")


if __name__ == "__main__":
    main()