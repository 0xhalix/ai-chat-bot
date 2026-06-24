# SerpAPI Integration Guide

## Why SerpAPI?

| Feature | SerpAPI | Google Custom Search |
|---------|---------|---------------------|
| **Multiple Engines** | Google, Bing, DuckDuckGo, Baidu | Only Google |
| **Free Tier** | 100 searches/month | 100 searches/month |
| **Pricing** | $5 per 1000 searches | $5 per 1000 searches |
| **Setup Complexity** | 1 API key only | API key + Custom Search Engine setup |
| **Crypto Data** | Excellent (real-time) | Good |
| **News Results** | Built-in structured data | Raw results |
| **Result Quality** | Very structured | Standard |

---

## Setup (3 Steps)

### 1. Get SerpAPI Key

Go to **https://serpapi.com** and:
1. Sign up (free account)
2. Copy your API key from dashboard
3. Add to .env:

```bash
SERPAPI_API_KEY=your_key_here
```

### 2. Update .env File

```env
# Web Search (SerpAPI)
SERPAPI_API_KEY=abc123def456ghi789jkl

# Database (keep existing)
DB_TYPE=postgresql
DB_HOST=192.168.1.100
DB_PORT=5432
DB_USER=botuser
DB_PASSWORD=secure_password
DB_NAME=crypto_database
```

### 3. Restart Your Bot

```bash
python main.py
```

---

## Usage in Your Bot

The web_search tool now supports 4 search engines:

### Example 1: Bitcoin Price (Google)
```python
# Model automatically calls:
web_search(
    query="Bitcoin price USD today",
    engine="google",  # Default
    max_results=5
)
```

### Example 2: Crypto News (DuckDuckGo - Privacy)
```python
web_search(
    query="Ethereum merge news latest",
    engine="duckduckgo",
    max_results=5
)
```

### Example 3: China Crypto (Baidu)
```python
web_search(
    query="中国比特币监管",
    engine="baidu",
    max_results=3
)
```

### Example 4: Regulations (Bing - Different perspective)
```python
web_search(
    query="SEC crypto regulation 2024",
    engine="bing",
    max_results=5
)
```

---

## Response Format

```python
# web_search returns formatted string:

"""
Search Results for: Bitcoin price today (via Google)

1. Bitcoin Price Today - CoinGecko
   URL: https://coingecko.com/bitcoin-price
   Bitcoin is trading at $65,234 USD, up 5.2% in 24h...

2. BTC Price & Chart - Investing.com
   URL: https://investing.com/crypto/bitcoin
   Bitcoin trading volume is $25B, market cap is $1.2T...

3. Bitcoin Market Data - CoinMarketCap
   URL: https://coinmarketcap.com/currencies/bitcoin
   Real-time Bitcoin prices across exchanges...
"""
```

---

## Integration in main.py

Already integrated! Just make sure you:

1. Have `SERPAPI_API_KEY` in your `.env`
2. Import tools:

```python
from tools_advanced import TOOLS, TOOL_REGISTRY

# In your response() function:
response = client.chat.completions.create(
    model=AI_MODEL,
    messages=messages,
    tools=TOOLS,  # ← Includes web_search with SerpAPI
    tool_choice="auto"
)
```

---

## Example Queries for Crypto Bot

### Market Analysis
- "What's the current BTC/ETH ratio?"
- "Bitcoin vs Ethereum performance this month"
- "Current L2 solutions market share"

### News & Updates
- "Latest Ethereum development updates"
- "SEC Bitcoin ETF news 2024"
- "DeFi hack news this week"

### Regulations
- "Crypto regulation latest news"
- "SEC guidance on staking"
- "EU crypto regulation updates"

### Technical Analysis
- "Bitcoin resistance levels today"
- "Ethereum whale transactions"
- "NFT floor price trends"

---

## Free Tier Limits & Pricing

**Free Plan:**
- 100 searches/month
- Multiple engines supported
- Real-time data
- Structured results

**Usage Tracking:**
```python
# Check your usage at https://serpapi.com/dashboard
# Each search counts as 1 request
```

**Upgrade to Paid:**
- $5 per 1000 searches (overages)
- Unlimited searches on paid tier
- Priority support

---

## Tool Parameters

```python
web_search(
    query="Bitcoin price today",  # Required - your search query
    engine="google",              # Optional - 'google' (default), 'bing', 'duckduckgo', 'baidu'
    max_results=5                 # Optional - 1-100 results
)
```

### Engines & Best For:

| Engine | Best For | Language Support |
|--------|----------|-----------------|
| **google** | General, crypto news, price data | 100+ languages |
| **bing** | Alternative perspective, US-focused | Major languages |
| **duckduckgo** | Privacy-focused, general search | Multiple languages |
| **baidu** | Chinese crypto news & data | Simplified/Traditional Chinese |

---

## Error Handling

```python
# The tool handles errors automatically:

# No results found
"No results found for 'xyz' on google"

# API key missing
"ERROR: Missing SerpAPI credentials. Set: SERPAPI_API_KEY"

# Timeout
"ERROR: Search request timed out"

# Invalid engine
# Automatically defaults to "google"
```

---

## Tips for Your Crypto Bot

### 1. Combine Tools
```python
# User: "What's Bitcoin worth if it goes to $100k?"

# Model uses tools in sequence:
# 1. web_search("Bitcoin current price") → Gets current price
# 2. calculator("100000 / current_price * investment") → Calculates gains
# 3. Returns analysis
```

### 2. Multi-Engine Search
```python
# For comprehensive results:
web_search("Ethereum staking APY", engine="google")    # 5 results
web_search("Ethereum staking APY", engine="duckduckgo") # Different perspective
# Model combines insights
```

### 3. Database + Search
```python
# Get user's portfolio from DB
query_database("SELECT * FROM user_portfolio WHERE user_id=123", "user_portfolio")

# Search latest prices
web_search("BTC ETH SOL price today", engine="google")

# Model creates personalized analysis
```

### 4. Crypto-Specific Queries
```python
# Best searches for crypto bot:
"bitcoin price coinmarketcap"
"ethereum gas fees gwei"
"crypto market cap dominance"
"defi tvl rankings"
"nft floor price"
"crypto news today"
"blockchain transaction fees"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ERROR: Missing SerpAPI" | Add `SERPAPI_API_KEY=` to .env from https://serpapi.com |
| "No results found" | Try different engine or query term |
| "API key invalid" | Regenerate key at https://serpapi.com/dashboard |
| "Timeout error" | Check internet connection, try simpler query |
| "Used all free searches" | Upgrade plan at https://serpapi.com/pricing |

---

## Monitoring

Check your usage:
1. Go to https://serpapi.com/dashboard
2. View current month's searches
3. Monitor remaining free/paid quota

```python
# In your bot logs:
logger.info(f"Tool: web_search, Query: {query}, Engine: {engine}")
logger.info(f"Result: {result[:200]}...")  # First 200 chars
```

---

## Next Steps

1. ✅ Update `.env` with `SERPAPI_API_KEY`
2. ✅ Restart bot
3. ✅ Test with user queries
4. ✅ Monitor usage at https://serpapi.com/dashboard
5. Consider upgrading for production use (100+ queries/month)
