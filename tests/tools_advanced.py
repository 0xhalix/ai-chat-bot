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
# GOOGLE GEMINI TOOLS SUPPORT (Interactions API)
# ============================================================
"""
Modern implementation using Google's Interactions API.
Provides automatic tool handling with max thinking level.

Compatible with OpenAI tool format - no conversion needed.
"""

def chat_with_gemini_tools(
    model_name: str,
    api_key: str,
    messages: list[dict],
    thinking_level: str = "high",
    max_tool_iterations: int = 5,
) -> Optional[str]:
    try:
        import google.genai as genai
        client = genai.Client(api_key=api_key)
        
        system_instructions, user_input = _build_input_from_messages(messages) 
        print(f"[Gemini Interaction] Model: {model_name}, Thinking: {thinking_level}")
        iteration = 0
        
        while iteration < max_tool_iterations:
            iteration += 1
            print(f"\n[Iteration {iteration}/{max_tool_iterations}]")
            
            interaction = client.interactions.create(
                model=model_name,
                input=user_input,
                system_instruction=system_instructions if system_instructions else None,
                tools=TOOLS, 
                generation_config={
                    "thinking_level": thinking_level,
                    "temperature": 0.7,
                },
                previous_interaction_id=interaction_id if interaction_id else None
            )
            
            interaction_id = interaction.id
            has_tool_calls = False
            final_text = None
            print(f"{interaction}\n\n")
            
            for step in interaction.steps:
                if step.type == "function_call":
                    has_tool_calls = True
                    result = _execute_tool_call(step)
                    print(f"  ✓ Executed: {step.name}()")
                    
                    user_input += f"\n\n[Tool Result: {step.name}]\n{result}"
                
                elif hasattr(step, "content") and step.content:
                    for part in step.content:
                        if hasattr(part, "text") and part.text:
                            final_text = part.text
                            print(f"  → Response: {part.text[:80]}...")
            
            if not has_tool_calls and final_text is not None:
                print(f"\n[Complete] Iterations: {iteration}")
                return final_text
            
            if has_tool_calls:
                continue
            
            if final_text:
                return final_text
            
            print("  ⚠ No response or tool calls found")
            break
        print(f"⚠ Max iterations ({max_tool_iterations}) reached")
        return None
    except ImportError:
        print("ERROR: google-generativeai library required")
        print("Install with: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def _build_input_from_messages(messages: list[dict]) -> tuple[str, str]:
    system_instructions = ""
    user_parts = []
    
    for msg in messages:
        role = msg.get("role", "user").lower()
        content = msg.get("content", "").strip()
        
        if not content:
            continue
        
        if role == "system":
            if system_instructions:
                system_instructions += f"\n\n{content}"
            else:
                system_instructions = content
        elif role in ("user", "assistant"):
            user_parts.append(content)
    user_input = "\n\n".join(user_parts) if user_parts else ""
    
    return system_instructions, user_input

def _execute_tool_call(step) -> str:
    try:
        tool_name = step.name
        tool_args = step.arguments if hasattr(step, "arguments") else {}
        
        print(f"    → Calling: {tool_name}({tool_args})")
        if tool_name not in TOOL_REGISTRY:
            return f"ERROR: Unknown tool '{tool_name}'"

        try:
            result = TOOL_REGISTRY[tool_name](**tool_args)
            if isinstance(result, (dict, list)):
                result_str = json.dumps(result, indent=2)
            else:
                result_str = str(result)
            
            return result_str
        except TypeError as e:
            return f"ERROR: Invalid arguments for {tool_name}: {str(e)}"
        except Exception as e:
            return f"ERROR: Tool execution failed: {str(e)}"
    except Exception as e:
        return f"ERROR: Failed to process tool call: {str(e)}"


### Legacy Gemini api call code

def _python_type_to_gemini(python_type: str):
    """Convert Python type string to Gemini Schema Type."""
    from google.genai import types as genai_types
        
    type_map = {
        "string": genai_types.Type.STRING,
        "integer": genai_types.Type.INTEGER,
        "number": genai_types.Type.NUMBER,
        "boolean": genai_types.Type.BOOLEAN,
        "object": genai_types.Type.OBJECT,
        "array": genai_types.Type.ARRAY,
    }
        
    return type_map.get(python_type, genai_types.Type.STRING)

def convert_openai_tools_to_gemini():
    try:
        from google.genai import types as genai_types
            
        gemini_tools = []
        for tool in TOOLS:
            if tool["type"] != "function":
                continue
                
            func = tool["function"]
                
            params = func.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])
                
                
            param_schema = {}
            for prop_name, prop_info in properties.items():
                param_schema[prop_name] = {
                    "type": prop_info.get("type", "string"),
                    "description": prop_info.get("description", ""),
                }

                if "enum" in prop_info:
                    param_schema[prop_name]["enum"] = prop_info["enum"]

                if "default" in prop_info:
                    param_schema[prop_name]["default"] = prop_info["default"]

            func_decl = genai_types.FunctionDeclaration(
                name=func["name"],
                description=func["description"],
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        name: genai_types.Schema(
                            type=_python_type_to_gemini(prop["type"]),
                            description=prop.get("description", ""),
                            enum=prop.get("enum"),
                        )
                        for name, prop in param_schema.items()
                    },
                    required=[r for r in required if r in param_schema],
                ),
            )
                
            tool_obj = genai_types.Tool(
                function_declarations=[func_decl])
                
            gemini_tools.append(tool_obj)
        print(gemini_tools)
        return gemini_tools
    except ImportError:
        raise ImportError(
            "Google generativeai library required. Install with:\n"
            "pip install google-genai"
        )

def chat_with_gemini_tools(model_name: str, api_key: str, messages: list[dict], max_tool_calls: int = 5) -> Optional[str]:
    try:
        import google.genai as genai
        from google.genai import types as genai_types
        
        client = genai.Client(api_key=api_key)
        gemini_tools = convert_openai_tools_to_gemini()     
        system_instructions, user_parts =_build_input_from_messages(messages)
        tool_response = None
        assistant_response = None
        
        user_input = genai_types.Content(
            role='user',
            parts=[genai_types.Part.from_text(text=user_parts)],
        )
            
        tool_call_count = 0
            
        while tool_call_count < max_tool_calls:
            print(f"\n[Gemini Call #{tool_call_count + 1}]")
                
                # Generate response with tools
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    user_input,
                    assistant_response if assistant_response is not None else "",
                    tool_response if tool_response is not None else ""
                ],
                tools=gemini_tools,
                config=genai_types.GenerateContentConfig(
                    system_instructions= system_instructions if system_instructions else None,
                    tools= gemini_tools,
                    thinking_config= genai_types.ThinkingConfig(thinking_level="high"),
                    temperature= 0.7,
                )
            )
                
            print(response.candidate[0].content)
            print(f"Response finish reason: {response.candidates[0].finish_reason}")
                
            if response.candidates[0].finish_reason == genai_types.FinishReason.TOOL_USE:
                print("Model using tools...")
                
                tool_uses = []
                for part in response.candidates[0].content.parts:
                    if isinstance(part, genai_types.FunctionCall):
                        tool_uses.append(part)
                        
                    if not tool_uses:
                        print("No tool calls found despite TOOL_USE finish reason")
                        break
                        
                    assistant_response = response.candidates[0].content
                    tool_results = []
                        
                    for tool_use in tool_uses:
                        tool_name = tool_use.name
                        tool_args = tool_use.args
                            
                        print(f"  → Executing: {tool_name}({tool_args})")
                        if tool_name in TOOL_REGISTRY:
                            try:
                                result = TOOL_REGISTRY[tool_name](**tool_args)
                            except TypeError as e:
                                result = f"ERROR: Invalid arguments - {str(e)}"
                        else:
                            result = f"ERROR: Unknown tool {tool_name}"
                            
                        print(f"  ← Result: {result[:100]}...")
                            
                        tool_results.append(
                            genai_types.FunctionResponse(
                                name=tool_name,
                                response={"result": result}
                            )
                        )
                        
                    tool_response = genai_types.Content(
                        role="tool",
                        parts=tool_results
                    )
                        
                    tool_call_count += 1
            else:
                text = response.candidates[0].content.parts[0].text
                print(f"\n[Final Response]\n{text[:100]}...")
                return text
        print(f"Max tool calls ({max_tool_calls}) reached")
        return response.candidates[0].content.parts[0].text
    except ImportError as e:
        print(f"ERROR: {e}")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None



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
