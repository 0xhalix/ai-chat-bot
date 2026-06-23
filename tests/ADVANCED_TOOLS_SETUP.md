# Advanced Tools Integration Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Telegram Bot                         │
│                                                              │
│  main.py (response function)                               │
│  └─> OpenAI API Call with tools=TOOLS                      │
│      └─> Model decides: needs tool? yes/no                 │
│          └─> tool_calls returned                           │
│              └─> Execute: calculator/web_search/query_db  │
│                  └─> Add results to messages               │
│                      └─> Loop back to API                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      External Services                       │
│                                                              │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐│
│  │  Google Custom │  │   Your Host  │  │  Math Library    ││
│  │  Search API    │  │   Database   │  │  (Built-in)      ││
│  │                │  │  (PostgreSQL/│  │                  ││
│  │  • Web results │  │   MySQL)     │  │  • sqrt, sin,etc││
│  │  • Real-time   │  │              │  │  • Conversions   ││
│  │  • News feeds  │  │  • User data │  │  • Precision     ││
│  └────────────────┘  └──────────────┘  └──────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Setup Steps

### 1. Environment Variables (.env)

```bash
# Google Custom Search
GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_cse_id_here

# Database Connection (Host Server)
DB_TYPE=postgresql              # or mysql, sqlite
DB_HOST=192.168.1.100          # Your server IP
DB_PORT=5432                    # PostgreSQL: 5432, MySQL: 3306
DB_USER=botuser                 # Database user
DB_PASSWORD=YourSecurePassword  # Database password
DB_NAME=crypto_database         # Database name
```

### 2. Get Google Custom Search Credentials

**Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project
3. Enable "Custom Search API"
4. Create API key (Credentials → API Key)
5. Go to [Programmable Search Engine](https://cse.google.com)
6. Create custom search engine for your desired sites
7. Copy Search Engine ID (cx value)

**Cost:** Free tier = 100 searches/day, $5 per 1000 searches after

### 3. Database Setup (Host Server)

**PostgreSQL Example:**

```sql
-- Connect to your host server
psql -h 192.168.1.100 -U postgres

-- Create database
CREATE DATABASE crypto_database;

-- Connect to database
\c crypto_database

-- Create tables
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    price DECIMAL(20, 8),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50)
);

CREATE TABLE user_alerts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    asset VARCHAR(10),
    threshold DECIMAL(20, 8),
    condition VARCHAR(20),  -- 'above' or 'below'
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create bot user with limited permissions
CREATE USER botuser WITH PASSWORD 'YourSecurePassword';
GRANT CONNECT ON DATABASE crypto_database TO botuser;
GRANT USAGE ON SCHEMA public TO botuser;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO botuser;

-- For MySQL equivalent
CREATE USER 'botuser'@'192.168.1.100' IDENTIFIED BY 'YourSecurePassword';
GRANT SELECT, INSERT, UPDATE ON crypto_database.* TO 'botuser'@'192.168.1.100';
FLUSH PRIVILEGES;
```

### 4. Install Dependencies

```bash
# For PostgreSQL
pip install psycopg2-binary

# For MySQL
pip install mysql-connector-python

# For Google Search
pip install requests  # Already have via OpenAI lib

# All together
pip install psycopg2-binary mysql-connector-python requests python-dotenv
```

---

## Integration into main.py

Replace your `_call_model_sync()` function:

```python
from tools_advanced import TOOLS, TOOL_REGISTRY
import json

def _call_model_sync(prompt: list[dict], api_key: str) -> Optional[str]:
    """Call model with tool support."""
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key, base_url=api_url)
    messages = prompt.copy()
    
    tool_call_loop = 0
    max_tool_loops = 5
    
    while tool_call_loop < max_tool_loops:
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                tools=TOOLS,              # ← Your advanced tools
                tool_choice="auto",       # ← Auto-use when needed
                stream=False,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}}
            )
            
            # Check for tool calls
            if response.choices[0].message.tool_calls:
                logger.info(f"Model using tools: {len(response.choices[0].message.tool_calls)}")
                
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
                
                # Execute tools
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool: {tool_name}")
                    
                    # Execute from registry
                    if tool_name in TOOL_REGISTRY:
                        try:
                            tool_result = TOOL_REGISTRY[tool_name](**tool_args)
                        except TypeError as e:
                            tool_result = f"ERROR: Invalid arguments - {str(e)}"
                    else:
                        tool_result = f"ERROR: Unknown tool {tool_name}"
                    
                    # Add tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                    
                    logger.info(f"Tool result: {tool_result[:100]}...")
                
                tool_call_loop += 1
                # Continue loop to let model process results
                continue
            
            else:
                # No tool calls, return final response
                text = response.choices[0].message.content
                if text and text.strip():
                    logger.info(f"Model response (len={len(text)})")
                    return text.strip()
                else:
                    logger.warning("Model returned empty response")
                    return None
        
        except asyncio.TimeoutError:
            logger.error(f"Model timeout on attempt {tool_call_loop}")
            return None
        except Exception as exc:
            logger.error(f"Model error: {exc}")
            return None
    
    logger.warning(f"Max tool loops ({max_tool_loops}) reached")
    return None
```

---

## Usage Examples for Your Crypto Bot

### Example 1: Query User's Price Alerts

```python
# User asks: "Show me my Bitcoin alerts"

# Model uses tool:
query_database(
    query="SELECT asset, threshold, condition FROM user_alerts WHERE user_id=12345 AND active=TRUE",
    table="user_alerts"
)

# Returns:
# Row 1:
#   asset: BTC
#   threshold: 50000
#   condition: above
```

### Example 2: Calculate Portfolio Performance

```python
# User asks: "If I bought $10k at $40k, what's my current value at $65k?"

# Model uses tool:
calculator(
    expression="10000 * (65000 / 40000)",
    description="Portfolio value calculation"
)

# Returns:
# Portfolio value calculation
# Expression: 10000 * (65000 / 40000)
# Result: 16250
```

### Example 3: Get Latest Crypto News

```python
# User asks: "What's the latest news on Ethereum?"

# Model uses tool:
web_search(
    query="Ethereum latest news today",
    max_results=5
)

# Returns:
# Search Results for: Ethereum latest news today
#
# 1. Ethereum Price Hits New High
#    URL: https://example.com/article1
#    Ethereum surged past $3000 following network upgrade...
```

### Example 4: Multi-Tool Analysis

```python
# User asks: "Compare my portfolio performance vs market gains"

# Model execution flow:
# 1. Uses query_database to get user's portfolio data
# 2. Uses web_search to get current market data
# 3. Uses calculator to compute percentage gains
# 4. Returns combined analysis
```

---

## Database Query Patterns for Crypto Bot

### Insert Price Data

```python
query_database(
    query="INSERT INTO crypto_prices (symbol, price, source) VALUES (%s, %s, %s)",
    table="crypto_prices"
)
```

### Get User's Transaction History

```python
query_database(
    query="SELECT * FROM user_transactions WHERE user_id=12345 ORDER BY timestamp DESC",
    table="user_transactions",
    limit=50
)
```

### Check Price Alerts Triggered

```python
query_database(
    query="SELECT * FROM user_alerts WHERE active=TRUE AND symbol IN ('BTC', 'ETH')",
    table="user_alerts"
)
```

---

## Debugging & Monitoring

### Check Tool Execution Logs

```python
logger.info(f"Tool: {tool_name}, Args: {tool_args}")
logger.info(f"Result: {tool_result[:200]}...")  # First 200 chars
```

### Test Each Tool Independently

```bash
# Test calculator
python -c "from tools_advanced import calculator; print(calculator('sqrt(16) * 100'))"

# Test web search
python -c "from tools_advanced import web_search; print(web_search('BTC price'))"

# Test database
python -c "from tools_advanced import query_database; print(query_database('SELECT COUNT(*) FROM crypto_prices', 'crypto_prices'))"
```

### Monitor Tool Performance

```python
import time

start = time.time()
result = TOOL_REGISTRY[tool_name](**tool_args)
elapsed = time.time() - start

logger.info(f"{tool_name} took {elapsed:.2f}s, result length: {len(result)}")
```

---

## Security Considerations

### Database

- ✅ Use parameterized queries (防止 SQL injection)
- ✅ Create limited user (botuser) with SELECT/INSERT only
- ✅ Use strong passwords
- ✅ Query validation (check table names)
- ✅ Result limits (prevent huge dumps)

### Web Search

- ✅ Store API key in .env (never hardcode)
- ✅ Rate limit: 100 free searches/day
- ✅ Validate query (prevent injection)

### Calculator

- ✅ Whitelist allowed functions
- ✅ No import statements (prevent code execution)
- ✅ Timeout protection

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No module named psycopg2" | `pip install psycopg2-binary` |
| Database connection refused | Check DB_HOST, DB_PORT, firewall rules |
| 403 Google Search API | Verify API key in .env, enable API in Cloud Console |
| Model not using tools | Check `tool_choice="auto"`, model may not support tools |
| Query timeout | Increase DB timeout, optimize SQL query, add LIMIT |
| Tool result too large | Use LIMIT in queries, truncate web search results |

---

## Next Steps

1. Add more tables: `user_portfolios`, `market_data`, `trading_signals`
2. Implement caching: Redis for frequently accessed data
3. Add data validation: Input sanitization before DB queries
4. Set up monitoring: Track tool execution times, error rates
5. Rate limiting: Prevent abuse of free Google Search tier
