# ============================================================
# TOOLS IMPLEMENTATION WITH OPENAI LIBRARY
# ============================================================

"""
OpenAI library tool format differs from HuggingFace transformers.
With OpenAI, you:
1. Pass tools to chat.completions.create()
2. Check for tool_calls in response.choices[0].message.tool_calls
3. Execute tools and continue the conversation by adding tool results to messages
"""

from openai import OpenAI
from typing import Optional, Any, Callable
import json
import subprocess
import requests

# Define tools in OpenAI format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "python_executor",
            "description": "Execute Python code and return stdout + stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current facts and citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
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
            "name": "read_website_html_at_url",
            "description": "Fetch and return HTML content from a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

def python_executor(code: str) -> str:
    """Execute Python code and return output."""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout + result.stderr
        return output if output else "Code executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out"
    except Exception as e:
        return f"ERROR: {str(e)}"


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web. 
    NOTE: This is a placeholder - implement with actual search API
    (e.g., SerpAPI, Google Custom Search, Bing)
    """
    try:
        # Placeholder: You'd use a real search API here
        # Example with requests to a search engine:
        # results = requests.get(f"https://api.search.com/search?q={query}").json()
        return f"Search results for '{query}' (placeholder - integrate actual search API)"
    except Exception as e:
        return f"ERROR: {str(e)}"


def read_website_html_at_url(url: str) -> str:
    """Fetch HTML content from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text[:5000]  # Limit to first 5000 chars
    except Exception as e:
        return f"ERROR fetching {url}: {str(e)}"


# Tool registry - maps tool names to functions
TOOL_REGISTRY: dict[str, Callable] = {
    "python_executor": python_executor,
    "web_search": web_search,
    "read_website_html_at_url": read_website_html_at_url,
}


# ============================================================
# MAIN FUNCTION WITH TOOL USE
# ============================================================

def chat_with_tools(
    api_key: str,
    api_url: str,
    model: str,
    messages: list[dict],
    max_tool_calls: int = 5
) -> Optional[str]:
    """
    Chat with tool support. Handles the tool call loop automatically.
    
    Args:
        api_key: API key for the model
        api_url: Base URL for the API
        model: Model name/ID
        messages: List of message dicts with "role" and "content"
        max_tool_calls: Maximum number of tool calls per request
    
    Returns:
        Final text response from the model
    """
    client = OpenAI(api_key=api_key, base_url=api_url)
    
    # Add tools to the API call
    kwargs = {
        "model": model,
        "messages": messages,
        "tools": TOOLS,  # <-- Pass tools here
        "tool_choice": "auto",  # Let model decide when to use tools
        "stream": False,
    }
    
    tool_call_count = 0
    
    while tool_call_count < max_tool_calls:
        print(f"\n[API Call #{tool_call_count + 1}]")
        
        # Make the API call
        response = client.chat.completions.create(**kwargs)
        
        
        # Check if we got tool calls
        if response.choices[0].message.tool_calls:
            print(response.choices[0].message.tool_calls)
            print(f"Model wants to use {len(response.choices[0].message.tool_calls)} tool(s)")
            
            # Add assistant's response (with tool calls) to messages
            messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        },
                        "type": tc.type
                    }
                    for tc in response.choices[0].message.tool_calls
                ]
            })
            
            # Process each tool call
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                
                print(f"  → Executing: {tool_name}({tool_input})")
                
                # Execute the tool
                if tool_name in TOOL_REGISTRY:
                    tool_result = TOOL_REGISTRY[tool_name](**tool_input)
                else:
                    tool_result = f"ERROR: Unknown tool {tool_name}"
                
                print(f"  ← Result: {tool_result[:100]}...")
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            tool_call_count += 1
            # Continue loop to let model process tool results
            
        else:
            # No more tool calls, return the text response
            text = response.choices[0].message.content
            print(f"\n[Final Response]\n{text}")
            return text
    
    # Max tool calls reached
    print(f"Max tool calls ({max_tool_calls}) reached")
    return response.choices[0].message.content


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("HF_KEY")  # or your API key
    api_url = "https://router.huggingface.co/v1"
    model = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M:featherless-ai"
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use tools when needed to help answer questions."
        },
        {
            "role": "user",
            "content": "What's the current Bitcoin price? Check the CoinDesk website and use Python to calculate the change if needed."
        }
    ]
    
    result = chat_with_tools(api_key, api_url, model, messages)
    print(f"\nFinal answer: {result}")
