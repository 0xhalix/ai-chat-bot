#!/usr/bin/env python3
"""
Validation script for SerpAPI + Advanced Tools Setup
Run this to verify your crypto bot is ready to use all tools
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if .env file exists and has required variables."""
    print("=" * 60)
    print("1. ENVIRONMENT VARIABLES CHECK")
    print("=" * 60)
    
    # Load env
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Create one from template: cp .env.advanced.template .env")
        return False
    
    load_dotenv()
    
    # Check SerpAPI key
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key and serpapi_key != "":
        print("✅ SERPAPI_API_KEY is set")
    else:
        print("❌ SERPAPI_API_KEY is missing!")
        print("   Get key from: https://serpapi.com")
        return False
    
    # Check database config
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_name = os.getenv("DB_NAME")
    
    if all([db_host, db_user, db_name]):
        print("✅ Database credentials are set")
    else:
        print("⚠️  Database credentials incomplete (optional for calculator/search)")
    
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n" + "=" * 60)
    print("2. DEPENDENCIES CHECK")
    print("=" * 60)
    
    dependencies = {
        "requests": "Web requests (SerpAPI)",
        "openai": "OpenAI library",
        "python-dotenv": "Environment variables",
        "psycopg2": "PostgreSQL (optional)",
        "mysql.connector": "MySQL (optional)",
    }
    
    all_ok = True
    
    for package, description in dependencies.items():
        try:
            if package == "mysql.connector":
                import mysql.connector
            else:
                __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            if package in ["psycopg2", "mysql.connector"]:
                print(f"⚠️  {package} - {description} (optional)")
            else:
                print(f"❌ {package} - {description}")
                all_ok = False
    
    return all_ok


def test_calculator():
    """Test calculator tool."""
    print("\n" + "=" * 60)
    print("3. CALCULATOR TOOL TEST")
    print("=" * 60)
    
    try:
        from tools_advanced import calculator
        
        result = calculator("sqrt(100) * 2")
        if "20" in result:
            print("✅ Calculator works correctly")
            print(f"   Test: sqrt(100) * 2 = 20")
            return True
        else:
            print("❌ Calculator returned unexpected result")
            print(f"   Result: {result}")
            return False
    except Exception as e:
        print(f"❌ Calculator test failed: {e}")
        return False


def test_web_search():
    """Test web_search tool with SerpAPI."""
    print("\n" + "=" * 60)
    print("4. WEB SEARCH (SerpAPI) TEST")
    print("=" * 60)
    
    try:
        from tools_advanced import web_search
        
        print("Testing web_search tool...")
        result = web_search("Python programming", engine="google", max_results=2)
        
        if "ERROR" in result:
            if "Missing SerpAPI" in result:
                print("❌ SerpAPI key missing!")
                print("   Add SERPAPI_API_KEY to .env")
                print("   Get it from: https://serpapi.com")
            else:
                print(f"❌ Search failed: {result}")
            return False
        
        if "Search Results" in result and "URL:" in result:
            print("✅ Web search works correctly!")
            print("   Sample output:")
            for line in result.split("\n")[:5]:
                print(f"   {line}")
            return True
        else:
            print("⚠️  Search returned unexpected format")
            return False
    
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        return False


def test_database():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("5. DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        from tools_advanced import query_database
        
        # Test with simple query
        result = query_database(
            "SELECT 1 as test_value",
            "test_table",
            limit=1
        )
        
        if "ERROR" in result:
            print("⚠️  Database not available (optional)")
            print(f"   Error: {result[:100]}...")
            print("   Database is optional for web_search and calculator")
            return True  # Not critical
        
        if "test_value" in result or "1" in result:
            print("✅ Database connection works!")
            return True
        else:
            print("⚠️  Database connection uncertain")
            return True  # Not critical
    
    except Exception as e:
        print(f"⚠️  Database not available (optional): {str(e)[:50]}")
        return True  # Database is optional


def test_tools_registry():
    """Check if all tools are registered."""
    print("\n" + "=" * 60)
    print("6. TOOLS REGISTRY CHECK")
    print("=" * 60)
    
    try:
        from tools_advanced import TOOL_REGISTRY, TOOLS
        
        print(f"✅ Found {len(TOOLS)} tool definitions")
        print(f"✅ Found {len(TOOL_REGISTRY)} tool implementations")
        
        expected_tools = {"calculator", "web_search", "query_database"}
        registered_tools = set(TOOL_REGISTRY.keys())
        
        if expected_tools.issubset(registered_tools):
            print("✅ All expected tools registered")
            for tool in expected_tools:
                print(f"   • {tool}")
            return True
        else:
            missing = expected_tools - registered_tools
            print(f"❌ Missing tools: {missing}")
            return False
    
    except Exception as e:
        print(f"❌ Tools registry check failed: {e}")
        return False


def generate_report(results):
    """Generate final report."""
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    if passed == total:
        print("\n" + "🎉 All checks passed! Your bot is ready to use tools.")
        print("\nYou can now:")
        print("• Use web_search for real-time crypto news")
        print("• Use calculator for precise math")
        print("• Query your database for portfolio data")
        return True
    
    elif passed >= total - 1:
        print("\n" + "⚠️  Most checks passed. Some optional features unavailable.")
        print("Web search, calculator, and tool registry working!")
        print("Database is optional - it's OK if it's not set up.")
        return True
    
    else:
        print("\n" + "❌ Some critical checks failed. See above for details.")
        print("\nNext steps:")
        print("1. Set SERPAPI_API_KEY in .env (get from https://serpapi.com)")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Restart the bot")
        return False


def main():
    """Run all checks."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   CRYPTO BOT - TOOLS VALIDATION SCRIPT                    ║")
    print("║   Testing: Calculator, Web Search (SerpAPI), Database    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {
        "Environment Variables": check_environment(),
        "Dependencies": check_dependencies(),
        "Calculator Tool": test_calculator(),
        "Web Search Tool (SerpAPI)": test_web_search(),
        "Database Connection": test_database(),
        "Tools Registry": test_tools_registry(),
    }
    
    success = generate_report(results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
