"""
Example: Using Gemini with Interactions API and Tools

This demonstrates the modern way to use Google Gemini with tool support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Example 1: Simple Tool Use
# ====================================================================
def example_simple():
    """Simple example: Calculate and search for current data"""
    from tools_advanced import chat_with_gemini_tools
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful crypto analyst. Use tools to provide accurate information."
        },
        {
            "role": "user",
            "content": "Calculate 25% of $1000 and tell me the current Bitcoin price"
        }
    ]
    
    response = chat_with_gemini_tools(
        model_name="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
        messages=messages,
        thinking_level="high"
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Tool Use")
    print("="*60)
    print(f"\nResponse:\n{response}\n")


# Example 2: Complex Multi-Tool Chain
# ====================================================================
def example_multi_tool():
    """Complex example: Multiple tool calls in sequence"""
    from tools_advanced import chat_with_gemini_tools
    
    messages = [
        {
            "role": "system",
            "content": "You are a financial advisor. Use tools to provide data-driven recommendations."
        },
        {
            "role": "user",
            "content": (
                "If Bitcoin is above $60,000, calculate 15% gain on $5,000 investment. "
                "Otherwise, calculate 10% gain on $5,000. Also search for latest Bitcoin price trends."
            )
        }
    ]
    
    response = chat_with_gemini_tools(
        model_name="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
        messages=messages,
        thinking_level="high",
        max_tool_iterations=5
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Complex Multi-Tool Chain")
    print("="*60)
    print(f"\nResponse:\n{response}\n")


# Example 3: Deep Thinking Mode
# ====================================================================
def example_deep_thinking():
    """Example with maximum thinking level for complex reasoning"""
    from tools_advanced import chat_with_gemini_tools
    
    messages = [
        {
            "role": "system",
            "content": "You are an expert in cryptocurrency market analysis with deep reasoning."
        },
        {
            "role": "user",
            "content": (
                "Analyze the current crypto market: "
                "1. Get current Bitcoin and Ethereum prices "
                "2. Calculate ROI scenarios for different investment amounts "
                "3. Provide market insights based on the data"
            )
        }
    ]
    
    response = chat_with_gemini_tools(
        model_name="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
        messages=messages,
        thinking_level="high",  # Max thinking
        max_tool_iterations=5
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Deep Thinking Mode")
    print("="*60)
    print(f"\nResponse:\n{response}\n")


# Example 4: Database Query with Web Search
# ====================================================================
def example_database_with_search():
    """Example combining database queries with web search"""
    from tools_advanced import chat_with_gemini_tools
    
    messages = [
        {
            "role": "system",
            "content": "You are a crypto portfolio manager. Use database queries and web search for analysis."
        },
        {
            "role": "user",
            "content": (
                "Please provide a portfolio summary: "
                "1. Query the database for user portfolio details "
                "2. Search for current market prices "
                "3. Calculate current portfolio value based on latest prices"
            )
        }
    ]
    
    response = chat_with_gemini_tools(
        model_name="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
        messages=messages,
        thinking_level="medium",
        max_tool_iterations=5
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Database Query with Web Search")
    print("="*60)
    print(f"\nResponse:\n{response}\n")


# Example 5: Error Handling
# ====================================================================
def example_error_handling():
    """Example showing error handling"""
    from tools_advanced import chat_with_gemini_tools
    
    # This will fail gracefully if GEMINI_KEY is not set
    if not os.getenv("GEMINI_KEY"):
        print("\n" + "="*60)
        print("EXAMPLE 5: Error Handling")
        print("="*60)
        print("ERROR: GEMINI_KEY not set in .env")
        print("Please set GEMINI_KEY=your_api_key in .env file")
        return
    
    messages = [
        {"role": "user", "content": "What's 2+2?"}
    ]
    
    response = chat_with_gemini_tools(
        model_name="gemini-3.5-flash",
        api_key=os.getenv("GEMINI_KEY"),
        messages=messages,
        thinking_level="low"
    )
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling")
    print("="*60)
    print(f"\nResponse:\n{response}\n")


# Example 6: Thinking Level Comparison
# ====================================================================
def example_thinking_levels():
    """Compare different thinking levels"""
    from tools_advanced import chat_with_gemini_tools
    
    query = "Should I invest $10,000 in Bitcoin? Provide detailed reasoning."
    
    for level in ["low", "medium", "high"]:
        print(f"\n--- Thinking Level: {level.upper()} ---")
        
        messages = [
            {"role": "user", "content": query}
        ]
        
        response = chat_with_gemini_tools(
            model_name="gemini-3.5-flash",
            api_key=os.getenv("GEMINI_KEY"),
            messages=messages,
            thinking_level=level,
            max_tool_iterations=3
        )
        
        if response:
            print(f"Response preview: {response[:150]}...")


# Main
# ====================================================================
if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║   Gemini Interactions API - Tool Use Examples                  ║
║   Modern implementation with automatic tool support            ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Check environment
    if not os.getenv("GEMINI_KEY"):
        print("⚠️  GEMINI_KEY not set in .env file")
        print("Please add: GEMINI_KEY=your_api_key_here")
        exit(1)
    
    print("✓ GEMINI_KEY found")
    print("✓ Ready to run examples\n")
    
    # Run examples (uncomment to use)
    
    # example_simple()                    # Basic tool use
    # example_multi_tool()                # Multiple tool calls
    # example_deep_thinking()             # Deep reasoning
    # example_database_with_search()      # Combined tools
    # example_error_handling()            # Error handling
    # example_thinking_levels()           # Compare thinking levels
    
    # For demo, run the simple example:
    print("Running Example 1: Simple Tool Use")
    example_simple()
    
    print("\nTo run other examples, uncomment them in __main__:")
    print("  - example_multi_tool()")
    print("  - example_deep_thinking()")
    print("  - example_database_with_search()")
    print("  - example_error_handling()")
    print("  - example_thinking_levels()")
