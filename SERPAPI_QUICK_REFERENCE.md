# Quick Reference: Web Search Tool Integration

## What Changed

**Before (Google Custom Search):**
```python
GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_ENGINE_ID=your_cse_id

class GoogleSearchClient:
    def search(query, max_results):
        # Google API only
        # Limited to 10 results
        # Single engine
```

**After (SerpAPI):**
```python
SERPAPI_API_KEY=your_api_key

class SerpAPIClient:
    def search(query, engine="google", max_results):
        # Multiple engines: Google, Bing, DuckDuckGo, Baidu
        # Up to 100 results
        # Single API key
```

---

## Tool Definition (OpenAI Format)

```json
{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web using SerpAPI. Supports Google, Bing, DuckDuckGo, Baidu. Returns real-time results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "engine": {
                    "type": "string",
                    "enum": ["google", "bing", "duckduckgo", "baidu"],
                    "default": "google"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results (1-100)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}
```

---

## Tool Call Flow

```
┌─────────────────────────────────────────┐
│ User: "What's Bitcoin trading at?"      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Model sees: tools available             │
│ Decides: I need web_search              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Model generates tool_call:              │
│ {                                       │
│   "name": "web_search",                 │
│   "arguments": {                        │
│     "query": "Bitcoin price today",     │
│     "engine": "google",                 │
│     "max_results": 5                    │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Your Code Executes:                     │
│ result = web_search(                    │
│   query="Bitcoin price today",          │
│   engine="google",                      │
│   max_results=5                         │
│ )                                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ SerpAPI Returns:                        │
│ • 5 search results                      │
│ • Titles, URLs, snippets                │
│ • Real-time data                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Model Reads Results:                    │
│ "Bitcoin is trading at $65,234..."      │
│ "Volume is $25B..."                     │
│ "Market cap is $1.2T..."                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Model Responds to User:                 │
│ "Bitcoin is currently trading at        │
│  $65,234 USD with a 24h volume of       │
│  $25 billion and market cap of $1.2T"   │
└─────────────────────────────────────────┘
```

---

## Complete Integration in main.py

```python
# At top of file
from tools_advanced import TOOLS, TOOL_REGISTRY
import json

# In your response() function
async def response(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    def _call_model_sync(prompt: list[dict], api_key: str) -> Optional[str]:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key, base_url=api_url)
        messages = prompt.copy()
        
        tool_loop = 0
        max_loops = 5
        
        while tool_loop < max_loops:
            # Make API call with tools
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                tools=TOOLS,              # ← Includes web_search
                tool_choice="auto",
                stream=False,
                reasoning_effort="high"
            )
            
            # Check if model used tools
            if response.choices[0].message.tool_calls:
                logger.info(f"Tool use detected: {len(response.choices[0].message.tool_calls)} calls")
                
                # Add assistant response
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
                
                # Execute each tool
                for tc in response.choices[0].message.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)
                    
                    logger.info(f"Executing: {tool_name}({tool_args})")
                    
                    # Execute from registry
                    if tool_name in TOOL_REGISTRY:
                        try:
                            result = TOOL_REGISTRY[tool_name](**tool_args)
                        except Exception as e:
                            result = f"ERROR: {str(e)}"
                    else:
                        result = f"ERROR: Unknown tool {tool_name}"
                    
                    # Add result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
                
                tool_loop += 1
                continue  # Loop back for model to process results
            
            else:
                # No tool calls, return final response
                text = response.choices[0].message.content
                if text and text.strip():
                    logger.info(f"Final response: {len(text)} chars")
                    return text.strip()
                return None
        
        logger.warning(f"Max tool loops reached")
        return None
    
    # ... rest of function ...
```

---

## Testing the Tool

```bash
# Test calculator
python -c "from tools_advanced import calculator; print(calculator('sqrt(100) * 2'))"

# Test web_search (requires SERPAPI_API_KEY in .env)
python -c "from tools_advanced import web_search; print(web_search('Bitcoin price today', engine='google', max_results=3))"

# Test database
python -c "from tools_advanced import query_database; print(query_database('SELECT COUNT(*) FROM crypto_prices', 'crypto_prices'))"
```

---

## Environment Setup Checklist

- [ ] Add `SERPAPI_API_KEY` to `.env` (get from https://serpapi.com)
- [ ] Keep existing database credentials in `.env`
- [ ] Restart bot with `python main.py`
- [ ] Test with user query: "What's Bitcoin price?"
- [ ] Check logs for tool execution
- [ ] Monitor free tier usage at https://serpapi.com/dashboard

---

## Troubleshooting

**Error: "Missing SerpAPI credentials"**
- Add `SERPAPI_API_KEY=your_key` to `.env`
- Restart bot

**Error: "No results found"**
- Try different query term
- Try different engine: `engine="duckduckgo"`

**Model not using tools?**
- Check `tools=TOOLS` passed to API call
- Check `tool_choice="auto"` set
- Verify model supports tool use

**Using wrong file location?**
- Should be: `tests/tools_advanced.py`
- Make sure you import from correct location in main.py

---

## Cost Analysis

For crypto bot using web_search:

**Free Tier (100/month):**
- ~3 searches per day
- Good for light testing
- Enough for small user base

**Paid Tier ($5 per 1000):**
- For production
- Supports 100+ daily queries
- Real-time data

**Estimate for 1000 queries/month:**
- Cost: $5
- Per query: $0.005
- Negligible for most bots

---

## Next: Multi-Tool Example

User query: "Compare my portfolio to market performance"

**Model execution:**
1. **query_database** → Get user's holdings
2. **web_search** → Get latest prices
3. **calculator** → Compute portfolio %gain vs market %gain
4. **Response** → "Your portfolio is up 12% vs market up 8%"

All automated!
