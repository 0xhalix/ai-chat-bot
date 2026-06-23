# OpenAI vs HuggingFace Tools Format

## Quick Comparison

### ❌ HuggingFace Transformers Format (Local)
```python
TOOLS = [
    {"type": "function", "function": {
        "name": "python_executor",
        "description": "...",
        "parameters": {...}
    }},
]

# Then parse <tool_call><function=...>...</function></tool_call> blocks manually
text = tok.apply_chat_template(messages, tools=TOOLS, tokenize=False, add_generation_prompt=True)
# You have to parse the output strings yourself
```

---

## ✅ OpenAI Library Format (What you need)

### 1️⃣ DEFINE TOOLS (Same structure as HuggingFace)
```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_website_html_at_url",
            "description": "Fetch HTML from a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    }
]
```

### 2️⃣ PASS TOOLS TO API
```python
from openai import OpenAI

client = OpenAI(api_key=api_key, base_url=api_url)

response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=TOOLS,              # ← Add this
    tool_choice="auto",       # ← Auto-use tools when needed
    stream=False
)
```

### 3️⃣ CHECK FOR TOOL CALLS IN RESPONSE
```python
if response.choices[0].message.tool_calls:
    # Model wants to use a tool
    for tool_call in response.choices[0].message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        # Execute your tool
        result = execute_tool(tool_name, tool_args)
```

### 4️⃣ ADD TOOL RESULT & CONTINUE CONVERSATION
```python
# Add assistant's response with tool calls
messages.append({
    "role": "assistant",
    "content": response.choices[0].message.content or "",
    "tool_calls": [
        {
            "id": tc.id,
            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            "type": tc.type
        }
        for tc in response.choices[0].message.tool_calls
    ]
})

# Add tool result
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": result  # The output from your tool
})

# Call API again - model will process results and potentially use more tools
response = client.chat.completions.create(...messages...)
```

---

## Response Object Structure

When the model uses tools, the response looks like:

```python
response.choices[0].message = {
    "role": "assistant",
    "content": "I'll check the website for you...",  # Optional text before tool use
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "read_website_html_at_url",
                "arguments": '{"url": "https://coindesk.com/price-bitcoin"}'
            }
        }
    ]
}
```

Parse it like:
```python
tool_call = response.choices[0].message.tool_calls[0]
tool_name = tool_call.function.name  # "read_website_html_at_url"
tool_args = json.loads(tool_call.function.arguments)  # {"url": "..."}
tool_id = tool_call.id  # "call_abc123"
```

---

## Integration into Your Telegram Bot

In your `response()` function, modify `_call_model_sync()`:

```python
def _call_model_sync(prompt: list[dict], api_key: str) -> Optional[str]:
    from openai import OpenAI
    import json
    
    client = OpenAI(api_key=api_key, base_url=api_url)
    messages = prompt
    
    for attempt in range(3):  # Up to 3 tool use loops
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=False,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}}
        )
        
        # Check if model used tools
        if response.choices[0].message.tool_calls:
            # Add assistant response with tool calls
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
            
            # Execute tools and add results
            for tc in response.choices[0].message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                
                result = execute_tool(tool_name, tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
            
            # Continue loop to let model process results
            continue
        
        else:
            # No tool calls, return response
            text = response.choices[0].message.content
            if text and text.strip():
                return text.strip()
    
    return None

def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool and return result as string."""
    if tool_name == "read_website_html_at_url":
        url = tool_args.get("url")
        try:
            import requests
            resp = requests.get(url, timeout=10)
            return resp.text[:3000]  # Limit response size
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"
    
    elif tool_name == "python_executor":
        code = tool_args.get("code")
        # Use sandbox or restrict what code can do
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {str(e)}"
    
    else:
        return f"Unknown tool: {tool_name}"
```

---

## Key Takeaways

| Aspect | HuggingFace Local | OpenAI Library |
|--------|------------------|----------------|
| Tool format | Same as OpenAI | `tools=[...]` parameter |
| Tool call parsing | Manual string parsing `<tool_call>...</tool_call>` | Automatic in `response.tool_calls` |
| Response handling | Parse text blocks | Use structured `tool_calls` list |
| Agentic loop | Manual parsing | Just check `tool_calls` list |
| When to use | Local model (transformers) | API-based inference |

---

## Example: Reading CoinDesk Website

```python
# What the model does automatically:
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "What's Bitcoin price on CoinDesk?"}],
    tools=TOOLS,
    tool_choice="auto"
)

# If model decides to use your tool:
# response.choices[0].message.tool_calls[0] = {
#     "id": "call_123",
#     "function": {
#         "name": "read_website_html_at_url",
#         "arguments": '{"url": "https://coindesk.com/price-bitcoin"}'
#     }
# }

# You execute it:
result = requests.get("https://coindesk.com/price-bitcoin").text

# Add result back:
messages.append({"role": "tool", "tool_call_id": "call_123", "content": result})

# Call API again - model reads the HTML and provides final answer
response = client.chat.completions.create(...messages...)
# This time no tool_calls, just the final answer
```
