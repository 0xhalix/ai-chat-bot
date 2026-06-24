import asyncio
import logging
import datetime
import os
from typing import Optional, Any, Callable
import json
import subprocess
import requests
import telegram as tg
from pathlib import Path
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder,
                          ContextTypes,
                          CommandHandler,
                          MessageHandler,
                          ConversationHandler, 
                          filters)
from dotenv import load_dotenv as load_env

IMAGE_PATH = Path(__file__).resolve().parents[0] / "images" / "conversations"
IMAGE_PATH.mkdir(parents=True, exist_ok=True)
load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_MODEL = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M:featherless-ai"
MODEL_MAX_TRIES = 3
MODEL_TIMEOUT_SEC = 120
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_TIMEOUT_SEC = 120
GEMINI_MAX_TRIES = 2
SAFE_MSG_LIMIT = 3800

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level= logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    
    user = update.effective_user
    if user and user.first_name:
        name = user.first_name
    elif user and user.username:
        name = f"@{user.username}"
    else:
        name = "there"
        
    msg = (
        f"Hey {name}, welcome to the AI Chat Bot! 👋\n\n"
        "Chat with our AI assistant in a simple, fast, and structured way. "
        "Use it to ask questions, explore ideas, and have full conversations powered by the backend model.\n\n"
        "To get started, complete the onboarding flow first, then begin chatting when access is enabled.\n\n"
        "Available commands:\n"
        "  /converse — Start the onboarding conversation\n"
        "  /cancel — Cancel the current onboarding flow\n"
        "  /ai_chat — Start an AI chat session\n"
        "  /end_chat — End the current AI chat session\n"
        "  /id — Show your Telegram user ID\n"
        "  /help — View all available commands\n\n"
        "Once you are set up, you can start chatting anytime."
    )
    
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= msg)

async def any_message(update:tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id= update.effective_chat.id, text= 'You sent me a message')

async def unknown(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\n Message: {update.effective_message.text}")
    await context.bot.send_message(chat_id=update.effective_user.id, text= f"Sorry, I do not understand the command {update.effective_message.text}")

async def user_id(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}, equested for ID\nUser ID: {update.effective_user.id}")
    await update.effective_message.reply_text(text= f"Your user ID is {update.effective_user.id}", do_quote= True)

async def help(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "AI Chat Bot — Command Reference\n\n"
        "Getting Started\n"
        "• /converse — Begin the onboarding process\n"
        "• /cancel — Cancel the current onboarding process\n\n"
        "AI Chat\n"
        "• /ai_chat — Start a new AI chat session\n"
        "• /end_chat — End your current AI chat session\n\n"
        "Utility\n"
        "• /id — Display your Telegram user ID\n"
        "• /help — Show this command reference\n"
        "• /start — Show the welcome message\n"
    )
    await update.effective_message.reply_text(text=msg, do_quote=True)

# CONVERSATION BOT
GENDER, PHOTO, LOCATION, BIO = range(4)
async def conversation(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Boy", "Girl"]]

    await update.effective_message.reply_text(
        text= f"""Hi there, I'm your Ai chat bot.\nSend /cancel to stop the conversation.\n\nAre you a boy or a girl?""", 
        reply_markup=tg.ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            input_field_placeholder="Boy or girl?"
        ),
        do_quote=True
    )
    return GENDER

async def gender(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Gender of {user.first_name}: {update.effective_message.text}")
    await update.effective_message.reply_text(
        text= f"""I see! Please send me a photo of yourself,\nso i know what you look like, or send /skip if you don't want to""",
        reply_markup=tg.ReplyKeyboardRemove(),
        do_quote=True
    )
    return PHOTO

async def photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.effective_message.photo[-1].get_file()
    photo_name = f"{user.username}.jpg"
    file_path = IMAGE_PATH / photo_name
    await photo_file.download_to_drive(file_path)
    logger.info(f"Photo of {user.first_name}: {photo_name}")
    await update.message.reply_text(
        text= f"Great! Now, send me your location please,\nor send /skip if you don't want to.",
        do_quote=True
    )

    return LOCATION

async def skip_photo(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a photo.")
    await update.effective_message.reply_text(
        text= f"I bet you look great! Now, send me your location please, or send /skip.",
        do_quote=True
    )

    return LOCATION

async def location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_location = update.effective_message.location
    print(update.effective_message.location)
    logger.info(f"Location of {user.first_name}: {user_location.latitude} / {user_location.longitude}")
    await update.message.reply_text(
        text= f"Super, lastly\n tell me something about yourself.",
        do_quote=True
    )
    return BIO

async def skip_location(update: tg.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.first_name} did not send a location.")
    await update.effective_message.reply_text(
        text= f"That's not a problem. But, can you tell me something about yourself?",
        do_quote=True
    )

    return BIO

async def bio(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"Bio of {user.first_name}: {update.effective_message.text}")
    await update.effective_message.reply_text(
        text= f"Thank You!\nI hope we can chat again some day.",
        do_quote=True
    )
    return ConversationHandler.END

async def cancel(update: tg.Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    logger.info(f"user {user.first_name} canceled the conversation")
    await update.effective_message.reply_text(
        text= f"Bye!\nI hope we can talk again.",
        do_quote=True,
        reply_markup=tg.ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Conversation Handler for AI chat bot
RESPONSE = range(1)
async def ai_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nInitiate Ai guided chat")

    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👨\u200d💻')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    
    try:
        await update.effective_message.reply_text(
            text= f"""Initializing Ai chat bot, Start your conversation below.\n\nSend /end_chat to end the chat session.""", 
            do_quote=True
        )
        print(f"AI chat initialization by User: @{update.effective_user.username} Started")
    except tg.error.TelegramError as error:
        print(f'Message Error: {error}')
        
    return RESPONSE
        
async def response(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    openrouter_key: Optional[str] = os.getenv("OPENROUTER_KEY")
    gemini_key: Optional[str] = os.getenv("GEMINI_KEY")
    deepseek_key: Optional[str] = os.getenv("DEEPSEEK_KEY")
    serp_key: Optional[str] = os.getenv("SERPAPI_KEY")
    hf_key: Optional[str] = os.getenv("HF_KEY")
    api_url = "https://router.huggingface.co/v1"
    print(f"User_prompt: {update.effective_message.text}")
    prompt = [
        {"role": "system", "content": 
            """\
            You are an autonomous crypto/DeFi market intelligence agent designed to ingest high-volume information (news, on-chain data, pricing, macro) and produce the highest-signal actionable insights through multi-layer analysis + simulation-style reasoning used by experienced crypto operators for years.
            You are not a hype narrator. You are a disciplined intelligence system that:
            - detects repeating behaviors and regime shifts,
            - explains why markets moved (not just that they moved),
            - turns raw info into clear decisions and testable playbooks.

            You can output trade/strategy concepts, but you must frame them as decision-support with explicit assumptions and invalidation criteria (not personal financial advice).

            ---

            1) Your Character (Years-deep Operator Brain)
            You behave like someone with:
            - years of exposure to crypto cycles (risk-on/risk-off, liquidity waves, narrative rotations, leverage flushes), pattern memory for recurring structures (funding squeezes, liquidations cascades, "buy rumor sell news," unlock dumps, TGE playbooks, governance/bribe rotations), an analyst's discipline (evidence ranking, falsifiable hypotheses, measured confidence), a systems mindset (macro → liquidity → positioning → on-chain flows → price → reflexive feedback loops).

            You must constantly build and refine an internal "arsenal" of:
            - known market patterns,
            - cause → effect mappings,
            - trigger conditions,
            - playbooks with entry/exit/invalidation,
            - risk controls and sizing logic,
            - post-mortems that update the model.

            ---

            2) Primary Mission
            Given streams of:
            - news (crypto + traditional finance + geopolitics),
            - pricing (spot, perps, options, funding, basis),
            - on-chain (flows, TVL, bridges, stablecoin supply, CEX netflows if available),
            - protocol-specific events (upgrades, hacks, listings, emissions changes, governance, unlocks),
            - macro (rates, CPI, jobs, DXY, liquidity, central bank decisions),

            produce:
            1. What matters right now (top 3–7 actionable insights)
            2. Why it matters (mechanistic explanation)
            3. What to watch next (triggers + invalidation)
            4. What actions are rational (playbooks as conditional statements)
            5. What could break the thesis (risk + alternate scenarios)

            Every insight must be:
            grounded in evidence, mapped to a mechanism, assigned a confidence score with reasons, accompanied by triggers/invalidation.

            ---
            3) Ingestion & Normalization Pipeline (Non-negotiable)
            Step A — Ingest
            Pull from as wide a surface area as available:
            - crypto news sites, official blogs, protocol docs, governance forums
            - on-chain dashboards, explorers, event feeds
            - price feeds (spot/perps), volatility, funding rates
            - macro calendars and major economic announcements
            - reputable research sources

            Step B — Normalize (convert messy inputs into structured events)
            For every item ingested, create a standardized "Event Card":
            - Event Card Schema
            - timestamp_utc
            - source_type (news / on-chain / price / macro / social / governance / exploit / listing)
            - asset_or_sector (BTC, ETH, L2s, memes, perps, LSDfi, stablecoins, etc.)
            - event_type (policy, hack, listing, unlock, upgrade, lawsuit, exploit, partnership, emission-change, liquidation-wave, etc.)
            - claim (what is being asserted)
            - evidence (what can verify it)
            - expected_mechanism (how it could move markets)
            - time_horizon (minutes/hours/days/weeks)
            - reliability_score (0–1)
            - novelty_score (is this new info or recycled narrative?)
            - market_relevance_score (0–1)
            - tags (liquidity, leverage, solvency, regulation, risk-on, etc.)

            Step C — De-duplicate & cluster
            - Deduplicate repeated stories.
            - Cluster multiple sources reporting the same event.
            - Detect narrative "echoes" (same claim repeated without new evidence).

            ---
            4) The "Simulation Strategy" (Core Reasoning Engine)
            You must use a layered simulation approach that experienced crypto operators implicitly use:
            - Layer 1 — Regime Detection (Market Weather)
            - Classify the market regime using available evidence:
            - Liquidity regime (expanding / contracting)
            - Volatility regime (low / rising / high / compressing)
            - Leverage regime (clean / crowded / fragile)
            - Risk appetite (risk-on / risk-off / rotation)
            - Narrative regime (single dominant narrative vs fragmented)

            Output: a short regime label like:
            - "Risk-on, liquidity expanding, leverage rebuilding"
            - "Risk-off, volatility rising, leverage fragile (flush-prone)"
            - "Range-bound, vol compression, catalyst-sensitive"

            Layer 2 — Catalyst → Mechanism Model
            For each Event Card, map to one (or more) mechanisms:
            - liquidity injection/removal
            - positioning shock (funding, basis, OI)
            - solvency risk (bad debt, depegs, forced selling)
            - reflexive loops (price → collateral → liquidations → more selling)
            - narrative rotation (attention and capital migration)
            - structural flow (unlocks, emissions, treasury sales, buybacks)
            - market microstructure (thin books, weekends, low liquidity hours)

            Layer 3 — Counterfactual Scenarios (Mini war-game)
            For each major event cluster, run 3 scenarios:
            1. Base Case: expected outcome given current regime
            2. Bull Case: what must be true for upside surprise
            3. Bear Case: failure mode / downside path

            Each scenario must include:
            - triggers (observable conditions),
            - expected market reaction,
            - invalidation criteria (what proves it wrong),
            - time horizon.

            Layer 4 — Pattern Matching to Historical Templates
            Use "template matching," not vague analogies. Maintain a library of recurring crypto patterns:
            Examples of pattern templates:
            - Funding squeeze / crowded perp unwind
            - Spot-led rally vs perp-led rally (fragility)
            - Unlock + liquidity gap dump
            - Post-listing mean reversion
            - Regulatory headline spike then fade
            - Hack contagion (risk-off across similar protocols)
            - Stablecoin stress → deleveraging cascade
            - BTC dominance expansion vs alt season rotation
            - Narrative rotation (L2 → AI → memes → RWAs)
            - Volatility compression → breakout around macro events

            When you match a template, you must state:
            - why the match is valid,
            - which features align (funding, OI, vol, flows, sentiment proxies),
            - what usually happens next,
            - what is different this time.

            Layer 5 — Strategy Construction (Conditional Playbooks)
            Convert insights into conditional actions:
            Format:
            - Thesis: one sentence
            - Setup conditions: what must be observed
            - Action: what to do (generalized)
            - Risk control: where thesis breaks + what to do then
            - Targets/expectations: expected range of outcomes
            - Time horizon: minutes/hours/days/weeks
            - Confidence: 0–100 with reasons

            No absolute predictions. Everything is contingent and testable.

            ---
            5) Multi-Source Signal Fusion (How you spot buried patterns)
            You must combine signals across layers, including:
            - price action (trend, structure breaks, volatility)
            - derivatives (funding, basis, OI changes, liquidation estimates if available)
            - on-chain (stablecoin supply changes, bridge flows, whale movements, DEX vs CEX activity)
            - protocol internals (emissions, gauges/bribes, fee APR, TVL quality)
            - macro (rates, CPI surprises, FX, risk indices)
            - news (credibility-weighted catalysts)

            Rules:
            - Single-source signals never dominate unless reliability is extremely high.
            - When signals disagree, you must explain the conflict and which signal historically leads.


            ---

            6) Output Requirements (What "Best Actionable Insights" looks like)
            Every response must include:
            Section A — Executive Signal Stack (Top insights)
            Provide the top 3–7 insights with:
            - summary,
            - mechanism,
            - evidence,
            - confidence score,
            - time horizon,
            - what to watch next.

            Section B — Regime Snapshot
            - regime label,
            - key evidence behind it,
            - what regime shift would look like.

            Section C — Scenario Tree (Major catalysts)
            For each major event cluster:
            - base/bull/bear,
            - triggers,
            - invalidation,
            - expected reaction.

            Section D — Conditional Playbooks
            At least 2–5 playbooks (depending on data volume), each with:
            - setup,
            - action,
            - risk control,
            - invalidation,
            - monitoring checklist.

            Section E — "Unknowns & Data Gaps"
            Explicitly list missing data and the cheapest way to obtain/approximate it.

            ---

            7) Reliability, Safety, and Discipline Rules
            Evidence Discipline
            - Always tag statements as: Fact / Inference / Hypothesis.
            - Provide a confidence score and what would increase/decrease it.

            Anti-Hallucination
            - If you cannot verify a claim, treat it as a lead and propose verification steps.

            No Overfitting
            - Avoid "one chart = one conclusion." Require multi-signal confirmation for high-conviction outputs.

            Post-mortem Learning Loop
            - After outcomes (if feedback is provided), you must:
            - classify what happened (which template),
            - identify what signals led vs lagged,
            - update pattern weights and invalidation logic.

            ---
            8) Operating Modes (Switchable)
            - Macro-first Mode: macro liquidity + risk proxies dominate; crypto-specific catalysts are interpreted through macro regime.
            - Crypto-native Mode: on-chain + derivatives positioning dominate; macro is a background constraint.
            - Event-forensics Mode: focus on one major catalyst (hack, unlock, listing, regulation) and map contagion paths.
            - Portfolio-risk Mode: focus on fragility, tail risks, and hedging logic (still generalized, not personal advice).

            ---
            9) Startup Procedure (What you do at the start of every run)
            1. Build or update Regime Snapshot
            2. Ingest + normalize Event Cards
            3. Cluster events + dedupe narrative echoes
            4. Score each event by (reliability × relevance × urgency)
            5. Run scenario trees for top clusters
            6. Produce insight stack + playbooks
            7. Output monitoring triggers for the next cycle
            """}, 
        {"role": "user", "content": update.effective_message.text if update.effective_message.text else ""}]
    
    TOOLS = [
        {
            "type": "function",
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
        },
        {
            "type": "function",
            "name": "web_search",
            "description": "Search the web for current facts and citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "engine": {
                        "type": "string",
                        "description": "Search engine to use (google, bing, duckduckgo)",
                        "default": "google"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 6
                    }
                },
                "required": ["query", "engine"]
            }
        },
        {
            "type": "function",
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
    ]
    
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

    def web_search(query: str, engine: str = "google", max_results: int = 10) -> str:
        try:
            class SerpAPIClient:
                def __init__(self):
                    self.api_key = serp_key
                    self.base_url = "https://serpapi.com/search"
                    
                    if not self.api_key:
                        raise ValueError(
                            "Missing SerpAPI credentials. Set:\n"
                            "SERPAPI_KEY (get free API key at https://serpapi.com)"
                        )
                
                def search(self, query: str, engine: str = "google", max_results: int = 10) -> str:
                    try:
                        valid_engines = ["google", "bing", "duckduckgo"]
                        if engine not in valid_engines:
                            engine = "google"
                        
                        params = {
                            "q": query,
                            "engine": engine,
                            "api_key": self.api_key,
                            "location": "United States",
                            "google_domain": "google.com",
                            "hl": "en",
                            "gl": "us"
                        }
                        
                        response = requests.get(self.base_url, params=params, timeout=15)
                        response.raise_for_status()
                        data = response.json()
                        
                        if "error" in data:
                            return f"ERROR: SerpAPI error - {data['error']}"
                        
                        results = []
                        
                        if engine == "google":
                            if "answer_box" in data:
                                results.append({
                                    "title": "Answer Box",
                                    "snippet": data["answer_box"].get("snippet", ""),
                                    "highlight": data["answer_box"].get("snippet_highlighted_words", "")
                                })

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
                        
                        if not results:
                            return f"No results found for '{query}' on {engine}"
                        
                        if "ai_overview" in data and engine == "google":
                            output += self._format_ai_overview(data["ai_overview"])
                            output += "\n" + "-" * 70 + "\n\n"
                        
                        output = f"Search Results for: {query} (via {engine.capitalize()})\n\n"
                        for i, result in enumerate(results, 1):
                            output += f"{i}. {result['title']}\n"
                            output += f"   URL: {result['url']}\n"
                            if result.get('snippet'):
                                output += f"   {result['snippet']}\n"
                            output += "\n"
                        
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

            try:
                client = SerpAPIClient()
                return client.search(query, engine, max_results)
            except ValueError as e:
                return f"ERROR: {str(e)}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def read_website_html_at_url(url: str) -> str:
        """Fetch HTML content from a URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"ERROR fetching {url}: {str(e)}"
    
    TOOL_REGISTRY: dict[str, Callable] = {
                "python_executor": python_executor,
                "web_search": web_search,
                "read_website_html_at_url": read_website_html_at_url,
            }
    
    def _build_input_from_prompt(prompt: list[dict]) -> tuple[str, str]:
        system_instructions = ""
        user_parts = []
        
        for msg in prompt:
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

    def _call_model_sync(prompt: list[dict], api_key:str, api_url: str, model: str, max_tool_calls: int = 10) -> Optional[str]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=api_url)
            tool_call_count = 0
            model_config = None

            kwargs = {
                "model": model,
                "messages": prompt,
                "tools": TOOLS,
                "tool_choice": "auto",
                "stream": False,
                "reasoning_effort": "high",
                "extra_body": {"thinking": {"type": "enabled"}}
            }
                
            if model_config is not None:
                kwargs["config"] = model_config
                
            while tool_call_count < max_tool_calls:
                print(f"[API Call #{tool_call_count + 1}]")
                response = client.chat.completions.create(**kwargs)
                
                if response.choices[0].message.tool_calls:
                    print(response.choices[0].message.tool_calls)
                    print(f"Model wants to use {len(response.choices[0].message.tool_calls)} tool(s)")
                        
                    prompt.append({
                        "role": "assistant",
                        "content": response.choices[0].message.content or "",
                        "tool_calls": [
                            {"id": tc.id,
                             "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                                },
                             "type": tc.type}
                            for tc in response.choices[0].message.tool_calls
                        ]
                    })
                        
                    for tool_call in response.choices[0].message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_input = json.loads(tool_call.function.arguments)
                            
                        print(f"  → Executing: {tool_name}({tool_input})")
                        if tool_name in TOOL_REGISTRY:
                            tool_result = TOOL_REGISTRY[tool_name](**tool_input)
                        else:
                            tool_result = f"ERROR: Unknown tool {tool_name}"
                            
                        print(f"  ← Result: {tool_result}...")
                            
                        prompt.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })
                        
                    tool_call_count += 1      
                else:
                    print(f"response = {response}")
                    text = getattr(response.choices[0].message, "content", None)
                    if text and text.strip():
                        tool_call_count = 0
                        return text.strip()
                    logger.warning("HF returned empty text")
                    tool_call_count = 0
                    return None
            print(f"Max tool calls ({max_tool_calls}) reached")
            text = getattr(response.choices[0].message, "content", None)
            if text and text.strip():
                tool_call_count = 0
                return text.strip()
            logger.warning("HF returned empty text")
            tool_call_count = 0
            return None
        except Exception as exc:
            logger.warning(f"HF Model sync call failed: {exc}")
            tool_call_count = 0
    
    async def _call_model(prompt: list[dict], api_key: str, api_url: str, model: str) -> Optional[str]:
        """Async wrapper for Gemini. Up to GEMINI_MAX_TRIES attempts."""
        loop = asyncio.get_event_loop()
        for attempt in range(1, MODEL_MAX_TRIES + 1):
            try:
                text = await asyncio.wait_for(
                    loop.run_in_executor(None, _call_model_sync, prompt, api_key, api_url, model),
                    timeout=MODEL_TIMEOUT_SEC,
                )
                if text:
                    logger.info(f"HF Model success on attempt {attempt} (len={len(text)})")
                    return text
            except asyncio.TimeoutError:
                logger.warning(
                    f"HF Model attempt {attempt}/{MODEL_MAX_TRIES}: timeout after {MODEL_TIMEOUT_SEC}s",
                )
            except Exception as exc:
                logger.warning(f"HF Model attempt {attempt}/{MODEL_MAX_TRIES}: error: {exc}")

        return None
       
    def _call_gemini_sync(model_name: str, api_key: str, prompt: list[dict], thinking_level: str = "high", max_tool_calls: int = 10) -> Optional[str]:
        try:
            import google.genai as genai
            client = genai.Client(api_key=api_key)
            
            system_instructions, user_input = _build_input_from_prompt(prompt) 
            print(f"[Gemini Interaction] Model: {model_name}, Thinking: {thinking_level}")
            
            tool_call_count = 0
            while tool_call_count < max_tool_calls:
                print(f"\n[API Call #{tool_call_count + 1}]")
                
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
                    print(f"Model wants to use {len(interaction.steps)} tool(s)")
                    if step.type == "function_call":
                        print(step.name)
                        has_tool_calls = True
                        result = _execute_tool_call(step)
                        print(f"  ✓ Executed: {step.name}()")
                        
                        user_input += f"\n\n[Tool Result: {step.name}]\n{result}"
                        tool_call_count += 1
                    
                    elif hasattr(step, "content") and step.content:
                        for part in step.content:
                            if hasattr(part, "text") and part.text:
                                final_text = part.text
                                print(f"  → Response: {part.text[:80]}...")
                
                if not has_tool_calls and final_text is not None:
                    print(f"\n[Complete] Iterations: {tool_call_count + 1}")
                    return final_text
                
                if has_tool_calls:
                    continue
                
                if final_text:
                    return final_text
                
                print("  ⚠ No response or tool calls found")
                break
            print(f"⚠ Max iterations ({max_tool_calls}) reached")
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

    async def _call_gemini(prompt: str, api_key: str, model: str) -> Optional[str]:
        """Async wrapper for Gemini. Up to GEMINI_MAX_TRIES attempts."""
        loop = asyncio.get_event_loop()
        for attempt in range(1, GEMINI_MAX_TRIES + 1):
            try:
                text = await asyncio.wait_for(
                    loop.run_in_executor(None, _call_gemini_sync, model, api_key, prompt),
                    timeout=GEMINI_TIMEOUT_SEC,
                )
                if text:
                    logger.info(f"Gemini success on attempt {attempt} (len={len(text)})")
                    return text
            except asyncio.TimeoutError:
                logger.warning(
                    f"Gemini attempt {attempt}/{GEMINI_MAX_TRIES}: timeout after {GEMINI_TIMEOUT_SEC}s",
                )
            except Exception as exc:
                logger.warning(f"Gemini attempt {attempt}/{GEMINI_MAX_TRIES}: error: {exc}")

        return None
   
    def _chunk_text(text: str, limit: int = SAFE_MSG_LIMIT) -> list[str]:
        if len(text) <= limit:
            return [text]

        seps = ["\n\n", "\n", " "]
        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= limit:
                chunks.append(remaining)
                break
            cut = -1
            for sep in seps:
                cut = remaining.rfind(sep, 0, limit)
                if cut > 0:
                    cut = cut + len(sep)
                    break
            if cut <= 0:
                cut = limit
            chunk = remaining[:cut].rstrip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[cut:].lstrip()

        return chunks

    async def _send_chunks(update: tg.Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: Optional[str], disable_web_page_preview: bool) -> None:
        chunks = _chunk_text(text, SAFE_MSG_LIMIT)
        logger.info(
            f"Telegram chunking: len={len(text)} chunks={len(chunks)} parse_mode={parse_mode}",
        )
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is None:
            return

        failed_chunks: list[int] = []
        for i, chunk in enumerate(chunks):
            try:
                if i == 0 and update.message is not None:
                    await update.message.reply_text(
                        chunk,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                        do_quote=True
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview,
                    )
            except Exception as chunk_exc:
                logger.warning(
                    f"Chunk {i + 1}/{len(chunks)} failed to send: {chunk_exc} — continuing best-effort delivery"
                )
                failed_chunks.append(i + 1)

            if len(chunks) > 1:
                await asyncio.sleep(0.5)

        if failed_chunks and chat_id is not None:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ Part of the output failed to send "
                        f"(chunk(s) {failed_chunks} of {len(chunks)}) — "
                        "please use /rawsignals for full data."
                    ),
                    parse_mode=None,
                    disable_web_page_preview=True,
                )
            except Exception:
                logger.exception("Failed to send failed chunks notification")

    async def _safe_reply(
        update: tg.Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = True,
    ) -> None:
        """Send with guaranteed delivery and never-raise guarantee."""
        if update.message is None:
            return

        if len(text) > SAFE_MSG_LIMIT:
            logger.info(
                f"Proactive chunking triggered: len={len(text)} > SAFE_MSG_LIMIT={SAFE_MSG_LIMIT}"
            )
            try:
                await _send_chunks(update, context, text,
                                parse_mode=parse_mode,
                                disable_web_page_preview=disable_web_page_preview)
                return
            except Exception as e_chunk:
                logger.warning(f"Proactive chunked send failed; attempting tosend again: {e_chunk}")
                try:
                    await _send_chunks(update, context, text,
                                    parse_mode=None,
                                    disable_web_page_preview=disable_web_page_preview)
                    return
                except Exception as e_plain:
                    logger.exception(f"Plain text chunked send also failed: {e_plain}")
                    try:
                        await update.message.reply_text(
                            text= f"Output was too large to deliver completely",
                            parse_mode=None,
                            disable_web_page_preview=True,
                            do_quote=True
                        )
                    except Exception:
                        pass
                    return

        try:
            await update.message.reply_text(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                do_quote=True
            )
            return
        except tg.error.TelegramError as e:
            err = str(e)
            print(f'Message Error: {err}')
            logger.warning(f"Telegram send failed; recovering. err={err}")

            if "Message is too long" in err:
                try:
                    await _send_chunks(update, context, text,
                                    parse_mode=parse_mode,
                                    disable_web_page_preview=disable_web_page_preview)
                    return
                except tg.error.TelegramError as e2:
                    logger.warning(f"Chunked send failed; plain text fallback. err={e2}")

            try:
                await _send_chunks(update, context, text,
                                parse_mode=None,
                                disable_web_page_preview=disable_web_page_preview)
            except Exception as e3:
                logger.exception(f"Telegram recovery failed: {e3}")
                if update.message is not None:
                    await update.message.reply_text(
                        "Output was too large to deliver completely. Please use /rawsignals.",
                        parse_mode=None,
                        disable_web_page_preview=True,
                    )
        
    if gemini_key:
        try:
            result = await _call_gemini(prompt, hf_key, AI_MODEL)
        except Exception as exc:
            logger.warning(f"Gemini model raised error: {exc}")
            await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('😢')])
            await update.message.reply_text(text=f"AI model raised error: {exc}\nPlease try the prompt again.", do_quote= True)
            result = None
        if result is not None:
            await _safe_reply(update, context, result, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
        
    return RESPONSE
    
async def end_chat(update: tg.Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User: {update.effective_user.username}\nMessage: {update.effective_message.text}\nEnd Chat Triggered by user.")
    try:
        await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('👍')])
    except tg.error.TelegramError as error:
        print(f'Emoji Error: {error}')
    
    try:
        await update.effective_message.reply_text(
            text= f"AI chat session successfully ended.\n\nBye. I hope we can talk again!",
            do_quote=True,
        )
        print("AI Chat session Ended")
    except tg.error.NetworkError as error:
        print(f"Message Error: {error}")
        await update.effective_message.reply_text(
            text= f"Failed to end chat session, Try again: /end_chat",
            do_quote=True,
        )
    return ConversationHandler.END
    
# Main function to run the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, any_message)
    aichat_handler = CommandHandler('ai_chat', ai_chat)
    endchat_handler = CommandHandler('end_chat', end_chat)
    userid_handler = CommandHandler('id', user_id)
    help_handler = CommandHandler('help', help)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    
    # Converstion Handler
    conversation_handler= ConversationHandler(
        entry_points=[CommandHandler('converse', conversation)],
        states={
            GENDER: [MessageHandler(filters.Regex("(?i)^(Boy|Girl|Other)$"), gender)],
            PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("skip", skip_photo)],
            LOCATION: [MessageHandler(filters.LOCATION, location), CommandHandler("skip", skip_location)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # AI Chat Handler
    aichat_handler =ConversationHandler(
        entry_points= [CommandHandler("ai_chat", ai_chat)],
        states= {
            RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, response)]
        },
        fallbacks= [CommandHandler("end_chat", end_chat) ]
    )

    app.add_handler(conversation_handler)
    app.add_handler(aichat_handler)
    app.add_handler(endchat_handler)
    app.add_handler(start_handler)
    app.add_handler(message_handler)
    app.add_handler(userid_handler)
    app.add_handler(help_handler)
    
    app.add_handler(unknown_handler)

    try:
        app.run_polling(timeout= datetime.timedelta(seconds=15), bootstrap_retries= 3)
    except tg.error.TimedOut as error:
        print(f"Start-Up error: {error}")
    except tg.error.NetworkError as net_error:
        print(f"Network Error: {net_error}")

if __name__ == '__main__':
    main()
    
# effective_chat
# effective_user
# effective_sender
# effective_message


# import torch
# from transformers import AutoModelForImageTextToText, AutoTokenizer

# model_id = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M"
# tok = AutoTokenizer.from_pretrained(model_id)
# model = AutoModelForImageTextToText.from_pretrained(
#     model_id, dtype="bfloat16", device_map="auto"
# )

# messages = [
#     {"role": "user",
#     "content": "Walk through the biochemistry of how organophosphate nerve agents inhibit acetylcholinesterase, the resulting cholinergic toxicity, and the medical antidotes."}
# ]
# text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
# inputs = tok(text, return_tensors="pt").to(model.device)

# out = model.generate(
#     **inputs, max_new_tokens=16384, do_sample=True,
#     temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.05,
# )
# # Output opens with <think>...</think> reasoning, then the final answer.
# print(tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))