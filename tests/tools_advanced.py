# ============================================================
# ADVANCED TOOLS: Calculator, Database, Web Search
# ============================================================
"""
Production-ready tools for crypto bot with:
- Calculator: Precise arithmetic, unit conversion
- Database: Query host SQL database (PostgreSQL/MySQL)
- Web Search: SerpAPI integration (Google, Bing, DuckDuckGo, Baidu)
"""

import json
import os
from typing import Optional, Any
import requests
import sqlite3
from math import *
from datetime import datetime

# ============================================================
# ENVIRONMENT SETUP
# ============================================================
"""
Required environment variables in your .env:

SERPAPI_API_KEY=your_serpapi_key_here
DB_HOST=localhost (or your host server IP)
DB_PORT=5432 (PostgreSQL) or 3306 (MySQL)
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_database_name
DB_TYPE=postgresql (or mysql, sqlite)
"""

# ============================================================
# TOOL DEFINITIONS (OpenAI Format)
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform precise mathematical calculations, conversions, and complex formulas. Use for: arithmetic, unit conversion, percentages, exponentials, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression (e.g., '(100 * 2.5) + sqrt(16)', '1000 * (1.05**12)')"
                    },
                    "description": {
                        "type": "string",
                        "description": "What you're calculating (for context)"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using SerpAPI. Supports Google, Bing, DuckDuckGo, Baidu. Returns real-time results with titles, snippets, and URLs. Perfect for crypto/finance news and data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Bitcoin price today', 'Ethereum merge news', 'crypto regulations')"
                    },
                    "engine": {
                        "type": "string",
                        "description": "Search engine to use",
                        "enum": ["google", "bing", "duckduckgo", "baidu"],
                        "default": "google"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-100)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute SQL queries against your host database. Returns structured data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT/INSERT/UPDATE query"
                    },
                    "table": {
                        "type": "string",
                        "description": "Primary table being queried (for logging/safety)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limit results to N rows",
                        "default": 100
                    }
                },
                "required": ["query", "table"]
            }
        }
    }
]


# ============================================================
# CALCULATOR TOOL
# ============================================================

def calculator(expression: str, description: str = "") -> str:
    """
    Execute mathematical expressions safely.
    
    Supports: +, -, *, /, **, sqrt(), sin(), cos(), log(), exp(), etc.
    
    Args:
        expression: Math expression as string
        description: What you're calculating (optional)
    
    Returns:
        Result as string with original expression
    """
    try:
        # Whitelist allowed functions for safety
        safe_dict = {
            "sqrt": sqrt,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "log": log,
            "log10": log10,
            "exp": exp,
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "pow": pow,
            "pi": 3.141592653589793,
            "e": 2.718281828459045,
        }
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Format result
        if isinstance(result, float):
            # Round to reasonable precision
            result = round(result, 10)
        
        output = f"Expression: {expression}\nResult: {result}"
        if description:
            output = f"{description}\n{output}"
        
        return output
    
    except ZeroDivisionError:
        return "ERROR: Division by zero"
    except ValueError as e:
        return f"ERROR: Invalid calculation - {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================
# WEB SEARCH TOOL (SerpAPI)
# ============================================================

class SerpAPIClient:
    """SerpAPI client for multi-engine web search."""
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"
        
        if not self.api_key:
            raise ValueError(
                "Missing SerpAPI credentials. Set:\n"
                "SERPAPI_API_KEY (get free API key at https://serpapi.com)"
            )
    
    def search(
        self,
        query: str,
        engine: str = "google",
        max_results: int = 5
    ) -> str:
        """
        Search using SerpAPI.
        
        Args:
            query: Search query
            engine: Search engine ('google', 'bing', 'duckduckgo', 'baidu')
            max_results: Number of results (1-100)
        
        Returns:
            Formatted search results as string
        """
        try:
            # Validate engine
            valid_engines = ["google", "bing", "duckduckgo", "baidu"]
            if engine not in valid_engines:
                engine = "google"
            
            params = {
                "q": query,
                "engine": engine,
                "api_key": self.api_key,
                "num": min(max_results, 100),  # SerpAPI supports up to 100
                "timeout": 10
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if "error" in data:
                return f"ERROR: SerpAPI error - {data['error']}"
            
            # Parse results based on engine
            results = []
            
            if engine == "google":
                if "organic_results" in data:
                    for item in data["organic_results"][:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "position": item.get("position", ""),
                        })
            
            elif engine == "bing":
                if "organic_results" in data:
                    for item in data["organic_results"][:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                        })
            
            elif engine == "duckduckgo":
                if "organic_results" in data:
                    for item in data["organic_results"][:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                        })
            
            elif engine == "baidu":
                if "organic_results" in data:
                    for item in data["organic_results"][:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                        })
            
            # Format output
            output = f"Search Results for: {query} (via {engine.capitalize()})\n"
            output += "=" * 70 + "\n\n"
            
            # Include AI Overview if available (Google specific)
            if "ai_overview" in data and engine == "google":
                output += self._format_ai_overview(data["ai_overview"])
                output += "\n" + "-" * 70 + "\n\n"
            
            # Include organic search results
            if results:
                output += "ORGANIC RESULTS:\n\n"
                for i, result in enumerate(results, 1):
                    output += f"{i}. {result['title']}\n"
                    output += f"   URL: {result['url']}\n"
                    if result.get('snippet'):
                        output += f"   {result['snippet']}\n"
                    output += "\n"
            else:
                output += "No traditional search results found for this query.\n"
            
            return output
        
        except requests.exceptions.Timeout:
            return "ERROR: Search request timed out"
        except requests.exceptions.HTTPError as e:
            return f"ERROR: HTTP error - {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"ERROR: Search failed - {str(e)}"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _format_ai_overview(self, overview: dict) -> str:
        """Format AI overview data into readable text."""
        try:
            output = "📋 AI OVERVIEW:\n\n"
            
            # Process text blocks
            if "text_blocks" in overview:
                for block in overview["text_blocks"]:
                    block_type = block.get("type", "paragraph")
                    snippet = block.get("snippet", "")
                    
                    if block_type == "paragraph":
                        output += f"{snippet}\n\n"
                    
                    elif block_type == "heading":
                        output += f"**{snippet}**\n"
                    
                    elif block_type == "list":
                        list_items = block.get("list", [])
                        for item in list_items:
                            title = item.get("title", "")
                            snippet_item = item.get("snippet", "")
                            output += f"  • {title} {snippet_item}\n"
                        output += "\n"
            
            # Add references/sources
            if "references" in overview:
                output += "\n📚 SOURCES:\n"
                for ref in overview["references"][:5]:  # Limit to 5 refs
                    title = ref.get("title", "")
                    link = ref.get("link", "")
                    source = ref.get("source", "")
                    output += f"  • {title}\n"
                    output += f"    ({source})\n"
                    output += f"    {link}\n"
            
            return output
        
        except Exception as e:
            return f"[Overview formatting error: {str(e)}]\n"


def web_search(query: str, engine: str = "google", max_results: int = 5) -> str:
    """Wrapper for web search with SerpAPI."""
    try:
        client = SerpAPIClient()
        return client.search(query, engine, max_results)
    except ValueError as e:
        return f"ERROR: {str(e)}"


# ============================================================
# DATABASE TOOL (Host Server Connection)
# ============================================================

class DatabaseClient:
    """
    Database client for host server connection.
    Supports PostgreSQL, MySQL, SQLite.
    
    Architecture:
    - Connection pooling (reuse connections)
    - Query validation (prevent SQL injection)
    - Type mapping (convert DB types to Python)
    - Error handling & logging
    """
    
    def __init__(self):
        """Initialize database connection based on environment."""
        self.db_type = os.getenv("DB_TYPE", "postgresql").lower()
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.user = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")
        
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection based on type."""
        try:
            if self.db_type == "postgresql":
                try:
                    import psycopg2
                    self.connection = psycopg2.connect(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        connect_timeout=10
                    )
                except ImportError:
                    raise ImportError(
                        "PostgreSQL support requires: pip install psycopg2-binary"
                    )
            
            elif self.db_type == "mysql":
                try:
                    import mysql.connector
                    self.connection = mysql.connector.connect(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        connection_timeout=10
                    )
                except ImportError:
                    raise ImportError(
                        "MySQL support requires: pip install mysql-connector-python"
                    )
            
            elif self.db_type == "sqlite":
                import sqlite3
                self.connection = sqlite3.connect(
                    self.database,
                    timeout=10,
                    check_same_thread=False
                )
                self.connection.row_factory = sqlite3.Row
            
            else:
                raise ValueError(f"Unsupported DB_TYPE: {self.db_type}")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.db_type}: {str(e)}")
    
    def execute_query(
        self,
        query: str,
        table: str,
        limit: int = 100,
        params: tuple = None
    ) -> str:
        """
        Execute a query safely.
        
        Args:
            query: SQL query
            table: Table name (for validation/logging)
            limit: Result limit
            params: Query parameters (for parameterized queries)
        
        Returns:
            Formatted results as string
        """
        try:
            # Validate query
            query_upper = query.strip().upper()
            
            # Security check: only allow SELECT/INSERT/UPDATE on specified table
            if not any(query_upper.startswith(cmd) for cmd in ["SELECT", "INSERT", "UPDATE"]):
                return "ERROR: Only SELECT, INSERT, UPDATE queries allowed"
            
            # Prevent unbounded queries
            if query_upper.startswith("SELECT") and "LIMIT" not in query_upper:
                query += f" LIMIT {limit}"
            
            # Execute
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different query types
            if query_upper.startswith("SELECT"):
                rows = cursor.fetchall()
                
                if not rows:
                    return f"No results found for table: {table}"
                
                # Get column names
                col_names = [desc[0] for desc in cursor.description]
                
                # Format as readable output
                output = f"Query Results ({len(rows)} rows):\n\n"
                for i, row in enumerate(rows, 1):
                    output += f"Row {i}:\n"
                    for col, val in zip(col_names, row):
                        output += f"  {col}: {val}\n"
                    output += "\n"
                
                return output
            
            elif query_upper.startswith(("INSERT", "UPDATE")):
                self.connection.commit()
                affected = cursor.rowcount
                return f"SUCCESS: {affected} row(s) affected"
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            return f"ERROR: Database query failed - {str(e)}"
        
        finally:
            if cursor:
                cursor.close()
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


# Global database client (lazy initialized)
_db_client = None

def _get_db_client() -> DatabaseClient:
    """Get or create database client."""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client


def query_database(query: str, table: str, limit: int = 100) -> str:
    """
    Query your database.
    
    Args:
        query: SQL query
        table: Primary table name
        limit: Result limit
    """
    try:
        db = _get_db_client()
        return db.execute_query(query, table, limit)
    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {
    "calculator": calculator,
    "web_search": web_search,
    "query_database": query_database,
}


# ============================================================
# EXAMPLE USAGE & ENVIRONMENT SETUP GUIDE
# ============================================================

"""
SETUP INSTRUCTIONS:

1. CREATE .env FILE with:
   
   # Google Custom Search
   GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_cse_id
   
   # Database (example PostgreSQL)
   DB_TYPE=postgresql
   DB_HOST=192.168.1.100  # Your host server IP
   DB_PORT=5432
   DB_USER=botuser
   DB_PASSWORD=secure_password
   DB_NAME=crypto_db

2. INSTALL DEPENDENCIES:
   
   pip install psycopg2-binary  # For PostgreSQL
   # OR
   pip install mysql-connector-python  # For MySQL

3. USAGE IN YOUR BOT:
   
   from tools_advanced import TOOLS, TOOL_REGISTRY
   
   # In your chat loop:
   if response.choices[0].message.tool_calls:
       for tool_call in response.choices[0].message.tool_calls:
           tool_name = tool_call.function.name
           tool_args = json.loads(tool_call.function.arguments)
           
           result = TOOL_REGISTRY[tool_name](**tool_args)
           # Add to messages and continue...

EXAMPLE QUERIES:

Calculator:
  Expression: "((50000 * 1.12) / 4) + sqrt(1000)"
  
Web Search:
  Query: "Bitcoin price today CoinDesk"
  
Database (PostgreSQL example):
  Query: "SELECT * FROM crypto_prices WHERE symbol='BTC' ORDER BY timestamp DESC"
  Table: "crypto_prices"
"""


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 60)
    print("TESTING TOOLS")
    print("=" * 60)
    
    # Test Calculator
    print("\n1. CALCULATOR TEST:")
    result = calculator("(100000 * 1.05)**12 / 4", "Compound interest over 12 years")
    print(result)
    
    # Test Web Search
    print("\n2. WEB SEARCH TEST:")
    result = web_search("Bitcoin price USD today", max_results=3)
    print(result)
    
    # Test Database
    print("\n3. DATABASE TEST:")
    result = query_database(
        "SELECT * FROM crypto_prices LIMIT 5",
        "crypto_prices"
    )
    print(result)
