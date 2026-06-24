# Quick Implementation: Gemini Tools for main.py

## Current Gemini Implementation (in main.py)

```python
def _call_gemini_sync(prompt: str, api_key: str) -> Optional[str]:
    """Sync Gemini call. Runs inside executor. Returns text or None."""
    try:
        import google.genai as genai 
        client = genai.Client(api_key=api_key)
        gen_config = None
        
        try:
            from google.genai import types as genai_types
            gen_config = genai_types.GenerateContentConfig(
                thinking_config=genai_types.ThinkingConfig(thinking_level="high")
            )
        except Exception as e:
            print(e)

        kwargs: dict = {
            "model": GEMINI_MODEL,
            "contents": prompt,
        }
        if gen_config is not None:
            kwargs["config"] = gen_config

        response = client.models.generate_content(**kwargs)
        print(f"response = {response.text[:50]}")
        
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
        logger.warning("Gemini returned empty text")
        return None
    except Exception as exc:
        logger.warning(f"Gemini sync call failed: {exc}")
        return None
```

---

## New Implementation with Tools (Option 1: Simple)

Replace entire `_call_gemini_sync()` function with:

```python
def _call_gemini_sync(prompt: list[dict], api_key: str) -> Optional[str]:
    """Sync Gemini call with tool support."""
    try:
        from tools_advanced import chat_with_gemini_tools
        
        response = chat_with_gemini_tools(
            model_name=GEMINI_MODEL,
            api_key=api_key,
            messages=prompt,
            max_tool_calls=5
        )
        
        if response and response.strip():
            return response.strip()
        
        logger.warning("Gemini returned empty text")
        return None
    
    except Exception as exc:
        logger.warning(f"Gemini sync call failed: {exc}")
        return None
```

---

## New Implementation with Tools (Option 2: Full Control)

If you want more control and error handling:

```python
def _call_gemini_sync(prompt: list[dict], api_key: str) -> Optional[str]:
    """Sync Gemini call with tool support and error handling."""
    try:
        from tools_advanced import chat_with_gemini_tools, TOOL_REGISTRY
        import google.genai as genai
        from google.genai import types as genai_types
        
        # Log tool availability
        logger.info(f"Available tools: {list(TOOL_REGISTRY.keys())}")
        
        # Call Gemini with tools
        response = chat_with_gemini_tools(
            model_name=GEMINI_MODEL,
            api_key=api_key,
            messages=prompt,
            max_tool_calls=5  # Allow up to 5 sequential tool calls
        )
        
        # Handle response
        if response:
            logger.info(f"Gemini response length: {len(response)}")
            return response.strip()
        
        logger.warning("Gemini returned empty response")
        return None
    
    except ImportError as e:
        logger.error(f"Import error (check dependencies): {e}")
        return None
    
    except Exception as exc:
        logger.error(f"Gemini call failed: {exc}")
        return None
```

---

## Changes Needed in response() Function

### Before (Current Code)

```python
async def response(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    # ...existing code...
    
    gemini_key: Optional[str] = os.getenv("GEMINI_KEY")
    
    prompt = [
        {"role": "system", "content": "...system message..."},
        {"role": "user", "content": user_message}
    ]
    
    # Call model
    text = await _call_gemini(prompt, gemini_key)
```

### After (With Tools)

**No changes needed!** The prompt format is already correct.

```python
async def response(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    # ...existing code - NO CHANGES...
    
    gemini_key: Optional[str] = os.getenv("GEMINI_KEY")
    
    prompt = [
        {"role": "system", "content": "...system message..."},
        {"role": "user", "content": user_message}
    ]
    
    # Same call - now with tools!
    text = await _call_gemini(prompt, gemini_key)
    
    # Rest of code unchanged
```

---

## Step-by-Step Integration

### 1. Update tools_advanced.py
✅ Already done! (Gemini functions added)

### 2. Install google-generativeai
```bash
pip install google-generativeai
```

### 3. Update _call_gemini_sync() in main.py

**Find this section:**
```python
def _call_gemini_sync(prompt: str, api_key: str) -> Optional[str]:
    """Sync Gemini call. Runs inside executor. Returns text or None."""
```

**Replace with:**
```python
def _call_gemini_sync(prompt: list[dict], api_key: str) -> Optional[str]:
    """Sync Gemini call with tool support."""
    try:
        from tools_advanced import chat_with_gemini_tools
        
        response = chat_with_gemini_tools(
            model_name=GEMINI_MODEL,
            api_key=api_key,
            messages=prompt,
            max_tool_calls=5
        )
        
        if response and response.strip():
            return response.strip()
        
        logger.warning("Gemini returned empty text")
        return None
    
    except Exception as exc:
        logger.warning(f"Gemini sync call failed: {exc}")
        return None
```

### 4. Restart Bot
```bash
python main.py
```

---

## Verification

Test that tools work with Gemini:

```python
# In main.py or separate test file
import asyncio
from tools_advanced import chat_with_gemini_tools
import os
from dotenv import load_dotenv

load_dotenv()

messages = [
    {
        "role": "system",
        "content": "You are a helpful crypto analyst. Use tools when needed."
    },
    {
        "role": "user",
        "content": "What's the current Bitcoin price and what would $1000 be worth if BTC reaches $100k?"
    }
]

response = chat_with_gemini_tools(
    model_name="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_KEY"),
    messages=messages
)

print(response)

# Expected: Uses web_search tool to get price, calculator to compute gains
```

---

## What You Get

### Before (No Tools)
```
User: "What's Bitcoin price and my returns if it hits $100k?"
Gemini: "I don't have real-time price data. You would need to check..."
```

### After (With Tools)
```
User: "What's Bitcoin price and my returns if it hits $100k?"
Gemini:
  1. Calls web_search("Bitcoin price today")
  2. Calls calculator("100000 / current_price * 1000")
  3. Returns: "Bitcoin is trading at $65,234. 
     If you invested $1,000 at that price and it reaches $100k,
     your $1,000 would grow to approximately $1,533 (53% gain)."
```

---

## Troubleshooting

### Issue: "Module google.genai not found"
```bash
pip install google-generativeai
```

### Issue: "Gemini API key invalid"
- Check GEMINI_KEY in .env
- Make sure API key has generativeai access

### Issue: Tools not being used
- Check logs: `logger.info(f"Available tools: {list(TOOL_REGISTRY.keys())}")`
- Try simpler query that clearly needs tools
- Check `max_tool_calls` parameter

### Issue: Timeout
- Increase GEMINI_TIMEOUT_SEC in main.py
- Simplify queries (fewer tool calls needed)

---

## Summary

**3 Simple Steps:**

1. ✅ `pip install google-generativeai`
2. ✅ Copy new `_call_gemini_sync()` code into main.py
3. ✅ Restart bot

**Result:** Gemini now uses same tools as HuggingFace model!

---

## Comparison Table

| Feature | Before | After |
|---------|--------|-------|
| Tools | None | Calculator, Web Search, Database |
| Real-time data | No | Yes (via SerpAPI) |
| Math | Hallucination-prone | Accurate (via calculator) |
| Database access | No | Yes (query_database) |
| User portfolio analysis | Limited | Full capability |
| Multi-step reasoning | Basic | Advanced (tool chaining) |

---

## Advanced: Switching Between Models

Your bot now supports tools on both models:

```python
# HuggingFace with tools (via OpenAI lib)
text = await _call_model(prompt, hf_key)

# Gemini with tools (via google.genai lib)
text = await _call_gemini(prompt, gemini_key)

# Both use SAME tool implementations!
```

Add model selection logic:

```python
# Route to best model for query
if "price" in user_message.lower() or "search" in user_message.lower():
    # Use Gemini - better at web search
    text = await _call_gemini(prompt, gemini_key)
else:
    # Use HuggingFace - faster for simple queries
    text = await _call_model(prompt, hf_key)
```

---

Done! Your crypto bot now has multi-model tool support. 🚀
