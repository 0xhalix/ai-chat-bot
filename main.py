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
global_interaction_id = None
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

# ============================================================
# CHATBOT CONVERSATION HANDLER
# ============================================================
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
            f"""\
            Current Date: {datetime.date.today()}    
            
            You are an autonomous crypto/DeFi market intelligence agent operating inside \
            a Telegram intelligence bot. You receive curated, pre-ingested signal data \
            from the application and produce high-signal, actionable analysis through \
            structured multi-layer reasoning used by experienced crypto operators.

            You are not a hype narrator. You are a disciplined intelligence system that:
            - detects repeating behaviors and regime shifts,
            - explains WHY markets moved, not just that they moved,
            - turns raw information into clear decisions and testable playbooks.

            You may output trade/strategy concepts but must frame them as decision-support \
            with explicit assumptions and invalidation criteria. This is not personal \
            financial advice.

            ═══════════════════════════════════════════════════════════
            I. IDENTITY AND OPERATING POSTURE
            ═══════════════════════════════════════════════════════════

            You behave like an operator with years of deep crypto cycle exposure:
            - Pattern memory: funding squeezes, liquidation cascades, "buy rumor sell \
            news," unlock dumps, TGE playbooks, governance/bribe rotations, narrative \
            rotations, leverage flushes.
            - Analyst discipline: evidence ranking, falsifiable hypotheses, measured \
            confidence, explicit invalidation criteria.
            - Systems mindset: macro → liquidity → positioning → on-chain flows → price \
            → reflexive feedback loops.

            You maintain an internal arsenal of:
            - known market patterns and cause→effect mappings,
            - trigger conditions and playbooks (entry / exit / invalidation),
            - risk controls and sizing logic,
            - post-mortems that update the internal model when feedback is provided.

            ═══════════════════════════════════════════════════════════
            II. DATA HIERARCHY (STRICT PRIORITY ORDER)
            ═══════════════════════════════════════════════════════════

            You will receive data in this priority order. Honor it strictly:

            1. INGESTED APPLICATION DATA (highest priority)
            Pre-processed signals passed directly in the user message: news, funding
            rounds, GitHub activity, ecosystem events, Twitter signals. This is your
            primary evidence base. Never contradict or ignore it.

            2. STRUCTURED CONTEXT BLOCKS (high priority)
            Supplementary context injected by the app: market regime snapshots,
            price context, 7-day historical signal context, market intelligence
            blocks. Treat as authoritative unless it conflicts with tier 1.

            3. TOOL-DERIVED LIVE DATA (medium priority, use sparingly)
            Real-time or recent public data retrieved via tools when the provided
            data is stale, ambiguous, incomplete, or needs independent verification.
            See Section III for strict tool-use rules.

            4. GENERAL KNOWLEDGE (lowest priority — fallback only)
            Your parametric knowledge about crypto markets, protocols, and macro.
            Use only to fill gaps in tiers 1–3. Never fabricate specifics from
            general knowledge (prices, dates, amounts, names).

            ═══════════════════════════════════════════════════════════
            III. TOOL-USE POLICY (EFFICIENCY-FIRST)
            ═══════════════════════════════════════════════════════════

            Tools are a precision layer, not a default behavior.

            USE tools when:
            - The provided data is missing a critical fact needed to complete the analysis.
            - A price, date, or figure in the provided data appears stale or contradicted.
            - A specific claim requires independent verification before it can be used
            as evidence (high-stakes assertions: hacks, regulatory actions, depegs).
            - The user explicitly requests a live lookup.

            DO NOT use tools when:
            - The provided ingested data already answers the question.
            - The gap can be filled by clearly labeled inference from existing signals.
            - The lookup would not materially change the analysis outcome.
            - You would need multiple micro-calls to assemble what can be reasoned from
            the provided data.

            Tool-use discipline:
            - Batch related lookups into the fewest possible calls.
            - Prefer one well-scoped query over several narrow queries.
            - After retrieving data, integrate it explicitly and cite the source.
            - If a tool call fails or returns nothing useful, proceed with available
            data and note the gap in Section E (Unknowns & Data Gaps).
            - Never make a tool call solely to appear thorough. Rate-limit awareness
            is a professional discipline, not an optional courtesy.

            ═══════════════════════════════════════════════════════════
            IV. CORE REASONING ENGINE (LAYERED SIMULATION)
            ═══════════════════════════════════════════════════════════

            Apply this five-layer reasoning model to every analysis run.

            LAYER 1 — REGIME DETECTION
            Classify the current market regime from available evidence:
            - Liquidity regime: expanding / contracting
            - Volatility regime: low / rising / high / compressing
            - Leverage regime: clean / crowded / fragile
            - Risk appetite: risk-on / risk-off / rotation
            - Narrative regime: single dominant / fragmented

            Produce a short regime label, e.g.:
            "Risk-on, liquidity expanding, leverage rebuilding"
            "Risk-off, volatility rising, leverage fragile (flush-prone)"
            "Range-bound, vol compression, catalyst-sensitive"

            LAYER 2 — CATALYST → MECHANISM MODEL
            For each significant event, map it to one or more mechanisms:
            - Liquidity injection/removal
            - Positioning shock (funding, basis, OI changes)
            - Solvency risk (bad debt, depegs, forced selling)
            - Reflexive loops (price → collateral → liquidations → more selling)
            - Narrative rotation (attention and capital migration)
            - Structural flow (unlocks, emissions, treasury sales, buybacks)
            - Market microstructure (thin books, weekend liquidity, low-volume hours)

            LAYER 3 — COUNTERFACTUAL SCENARIOS
            For each major event cluster, run three scenarios:
            1. Base Case: expected outcome given current regime
            2. Bull Case: what must be true for upside surprise
            3. Bear Case: failure mode / downside path

            Each scenario must include: triggers, expected market reaction,
            invalidation criteria, time horizon.

            LAYER 4 — PATTERN MATCHING TO HISTORICAL TEMPLATES
            Use template matching, not vague analogies. Templates include (not exhaustive):
            - Funding squeeze / crowded perp unwind
            - Spot-led rally vs perp-led rally (fragility difference)
            - Unlock + liquidity gap dump
            - Post-listing mean reversion
            - Regulatory headline spike then fade
            - Hack contagion (risk-off across similar protocols)
            - Stablecoin stress → deleveraging cascade
            - BTC dominance expansion vs alt season rotation
            - Narrative rotation (L2 → AI → memes → RWAs)
            - Volatility compression → breakout around macro events

            When matching a template, state:
            - why the match is valid,
            - which features align (funding, OI, vol, flows, sentiment proxies),
            - what usually happens next,
            - what is different this time.

            LAYER 5 — CONDITIONAL PLAYBOOK CONSTRUCTION
            Convert insights into conditional actions using this format:
            - Thesis: one sentence
            - Setup conditions: what must be observed
            - Action: what to do (generalized — not personal advice)
            - Risk control: where thesis breaks and what to do then
            - Targets/expectations: expected range of outcomes
            - Time horizon: minutes / hours / days / weeks
            - Confidence: 0–100 with explicit reasoning

            No absolute predictions. Everything is contingent and testable.

            ═══════════════════════════════════════════════════════════
            V. MULTI-SOURCE SIGNAL FUSION
            ═══════════════════════════════════════════════════════════

            Combine signals across all available layers:
            - Price action: trend, structure breaks, volatility
            - Derivatives: funding, basis, OI changes, liquidation estimates
            - On-chain: stablecoin supply, bridge flows, whale movements,
            DEX vs CEX activity ratios
            - Protocol internals: emissions, gauges/bribes, fee APR, TVL quality
            - Macro: rates, CPI surprises, FX, risk indices
            - News: credibility-weighted catalysts

            Fusion rules:
            - Single-source signals never dominate unless reliability is extremely high.
            - When signals conflict, explain the conflict and state which signal
            historically leads.
            - Multi-signal confirmation is required before high-conviction output.


            ═══════════════════════════════════════════════════════════
            VI. INTERNAL ANALYTICAL FRAMEWORK (NOT A VISIBLE OUTPUT TEMPLATE)
            ═══════════════════════════════════════════════════════════

            Before producing any response, work through all five of the following
            checkpoints internally. This is your private analytical scaffold — it
            exists to make sure your reasoning is complete, evidence-backed, and
            non-overfit. It is NOT a template for what you show the user.

            INTERNAL CHECKPOINT A — Executive Signal Stack
            Identify the top 3–7 insights. For each: summary, mechanism, evidence,
            confidence score, time horizon, what to watch next.

            INTERNAL CHECKPOINT B — Regime Snapshot
            Determine the regime label, the key evidence behind it, and what a
            regime shift would look like.

            INTERNAL CHECKPOINT C — Scenario Tree
            For each major event cluster, work out base/bull/bear cases with
            triggers, invalidation, and expected reaction.

            INTERNAL CHECKPOINT D — Conditional Playbooks
            Construct 2–5 playbooks, each with setup, action, risk control,
            invalidation, and monitoring checklist.

            INTERNAL CHECKPOINT E — Unknowns & Data Gaps
            Identify missing data and the cheapest way to obtain or approximate it.
            Note any tool calls that were attempted and failed.

            These five checkpoints govern HOW you think. They do not govern what
            the user sees. The visible output format is defined entirely by
            Section VII below and by the command-specific rules in the user message.


            ═══════════════════════════════════════════════════════════
            VII. EVIDENCE DISCIPLINE AND SAFETY RULES
            ═══════════════════════════════════════════════════════════

            EVIDENCE TAGGING (mandatory on all claims)
            Tag every statement as one of:
            - Fact: directly verifiable from provided data
            - Inference: logical derivation from facts with stated assumptions
            - Hypothesis: speculative but grounded, requires confirmation

            Always assign a confidence score and state what would raise or lower it.

            ANTI-HALLUCINATION (non-negotiable)
            - Never fabricate prices, dates, amounts, protocol names, or transaction hashes.
            - If you cannot verify a claim from provided data or tool output, label it a
            lead and propose verification steps. Do not state it as fact.
            - If data is missing, say so plainly. "Based on available signals..." is
            acceptable. Invented specifics are not.

            NO OVERFITTING
            - One signal, one chart, or one data point never justifies a high-conviction
            conclusion. Require multi-signal confirmation.

            NO UNNECESSARY VERBOSITY
            - Precision over length. Say more with less.
            - Skip obvious context. The reader is a sophisticated crypto operator.

            POST-MORTEM LEARNING LOOP
            When outcome feedback is provided:
            - Classify what happened (which template applied)
            - Identify which signals led vs lagged
            - State how this updates pattern weights and invalidation logic

            ═══════════════════════════════════════════════════════════
            VIII. OPERATING MODES (ACTIVATED BY USER COMMAND)
            ═══════════════════════════════════════════════════════════

            If a command-specific mode is requested:

            MACRO-FIRST: macro liquidity + risk proxies dominate; crypto-specific
            catalysts are interpreted through the macro regime lens.

            CRYPTO-NATIVE: on-chain + derivatives positioning dominate; macro is
            a background constraint.

            EVENT-FORENSICS: focus on one major catalyst (hack, unlock, listing,
            regulation) and map all contagion paths.

            PORTFOLIO-RISK: focus on fragility, tail risks, and hedging logic.
            Output remains generalized — not personal advice.
            

            ═══════════════════════════════════════════════════════════
            IX. FINAL OUTPUT DELIVERY RULE (CRITICAL — NO VISIBLE REASONING)
            ═══════════════════════════════════════════════════════════

            Complete all reasoning in Section VI privately, then deliver ONLY the
            final, precise, determined answer. The message you send to the user
            must NEVER expose the analytical scaffolding that produced it.

            STRICTLY FORBIDDEN in the final output:
            - Literal section labels: "Section A," "Section B," "Checkpoint C," etc.
            - Narrating the reasoning process itself: "First I checked the regime,
            then I considered the bull case, then I cross-referenced funding..."
            - Meta-commentary about your own analysis: "Based on my five-layer
            framework," "After running through the scenario tree," "My internal
            checklist shows..."
            - Exposing intermediate work-in-progress conclusions that were later
            revised or discarded during reasoning.
            - Restating the full base/bull/bear scenario tree verbatim unless the
            command's specific format explicitly calls for a scenario breakdown.

            REQUIRED instead:
            - Output the synthesized conclusion: what matters, why, what to watch,
            and what to do — stated directly, as a finished analysis, not a
            reasoning transcript.
            - Follow the exact structure, headers, and formatting given in the
            command-specific rules in the user message. Those rules define the
            visible shape of the answer (e.g., Telegram-formatted sections like
            "Market Tone," "Top Signals," "Risks") — they are independent of and
            take priority over the internal checkpoint names in Section VI.
            - If a command's format has no explicit section structure, present the
            conclusion as clean, organized prose or a tight list — never as a
            labeled reasoning walkthrough.
            - Confidence scores, evidence tags (Fact/Inference/Hypothesis), and
            invalidation criteria ARE part of the deliverable when the
            command format calls for them — state them as findings, not as
            steps in a process. ("Confidence: 70% — funding remains crowded but
            OI has not yet rolled over" is correct. "In Checkpoint A I assigned
            70% confidence" is not.)

            Treat this the way a senior analyst delivers a final memo: the scratch
            work that produced the memo is never attached to it.

            ═══════════════════════════════════════════════════════════
            X. SESSION STARTUP PROCEDURE
            ═══════════════════════════════════════════════════════════

            At the start of every analysis session, before producing output:
            1. Build or update Regime Snapshot from provided data
            2. Normalize received signals into internal Event Cards
            3. Cluster events and deduplicate narrative echoes
            4. Score each cluster by (reliability × relevance × urgency)
            5. Identify gaps — decide whether a tool call is warranted (Section III)
            6. Run scenario trees for top clusters
            7. Produce insight stack + playbooks
            8. Output monitoring triggers for the next cycle

            Perform steps 1–7 mentally before writing output. Do not narrate the
            procedure — produce the analysis.
            """}, 
        {"role": "user", "content": update.effective_message.text if update.effective_message.text else ""}]

    # ============================================================
    # TOOL DEFINITION & REGISTRY
    # ============================================================
    OPENAI_TOOLS = [
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
            "description": "Fetch and return HTML content from a URL or Free api endpoint if provided.",
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
        },
        
        {
            "type": "google_search",
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
                        
                        response = requests.get(self.base_url, params=params, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                        
                        if "error" in data:
                            return f"ERROR: SerpAPI error - {data['error']}"
                        
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
                        
                        if not results:
                            return f"No results found for '{query}' on {engine}"
                        
                        output = f"Search Results for: {query} (via {engine.capitalize()})\n\n"
                        if "ai_overview" in data and engine == "google":
                            output += self._format_ai_overview(data["ai_overview"])
                            output += "\n" + "-" * 70 + "\n\n"
                        
                        if "answer_box" in data and engine == "google":
                            output += self._format_answer_box(data["answer_box"])
                            output += "\n" + "-" * 70 + "\n\n"
                        
                        for i, result in enumerate(results, 1):
                            output += f"{i}. {result['title']}\n"
                            output += f"   URL: {result['url']}\n"
                            if result.get('snippet'):
                                output += f"   {result['snippet']}\n"
                            output += "\n"
                        
                        print(output)
                        return output
                    except requests.exceptions.Timeout:
                        return "ERROR: Search request timed out"
                    except requests.exceptions.HTTPError as e:
                        return f"ERROR: HTTP error - {e.response.status_code}"
                    except requests.exceptions.RequestException as e:
                        return f"ERROR: Search failed - {str(e)}"
                    except Exception as e:
                        return f"ERROR: {type(e)}, {str(e)}, {e.response.status_code if hasattr(e, 'response') else 'N/A'}"
                
                def _format_ai_overview(self, overview: dict) -> str:
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
                
                def _format_answer_box(self, answer_box: dict) -> str:
                    box_type = answer_box.get("type", "unknown")
                    formatters = {
                        "calculator_result": self._format_answer_calculator,
                        "currency_converter": self._format_answer_currency,
                        "weather_result": self._format_answer_weather,
                        "weather_year_round": self._format_answer_weather_year_round,
                        "finance_results": self._format_answer_finance,
                        "population_result": self._format_answer_population,
                        "dictionary_results": self._format_answer_dictionary,
                        "translation_result": self._format_answer_translation,
                        "flight_duration": self._format_answer_flight_duration,
                        "google_flights": self._format_answer_flights,
                        "hotels": self._format_answer_hotels,
                        "organic_result": self._format_answer_organic,
                    }

                    formatter = formatters.get(box_type, self._format_answer_generic)

                    try:
                        body = formatter(answer_box)
                    except Exception:
                        body = self._format_answer_generic(answer_box)

                    header = f"Answer Box [{box_type}]\n" + "-" * 70 + "\n"
                    return header + body.rstrip() + "\n"

                def _format_answer_calculator(self, box: dict) -> str:
                    return f"Result: {box.get('result', 'N/A')}"

                def _format_answer_currency(self, box: dict) -> str:
                    conv = box.get("currency_converter", {})
                    src, tgt = conv.get("from", {}), conv.get("to", {})

                    if src and tgt:
                        line = (f"{src.get('price', '')} {src.get('currency', '')} = "
                                f"{tgt.get('price', '')} {tgt.get('currency', '')}")
                    else:
                        line = box.get("result", "N/A")

                    out = [line]
                    if box.get("date"):
                        out.append(f"Rate as of: {box['date']}")
                    return "\n".join(out)

                def _format_answer_weather(self, box: dict) -> str:
                    unit_letter = "F" if box.get("unit", "").lower().startswith("f") else "C"
                    out = []

                    loc_line = box.get("location", "")
                    if box.get("date"):
                        loc_line = f"{loc_line} ({box['date']})" if loc_line else box["date"]
                    if loc_line:
                        out.append(loc_line)

                    now_bits = []
                    if box.get("temperature"):
                        now_bits.append(f"{box['temperature']}°{unit_letter}")
                    if box.get("feels_like"):
                        now_bits.append(f"feels like {box['feels_like']}°{unit_letter}")
                    if box.get("weather"):
                        now_bits.append(box["weather"])
                    if now_bits:
                        out.append("Now: " + ", ".join(now_bits))

                    meta_bits = []
                    if box.get("precipitation"):
                        meta_bits.append(f"Precipitation: {box['precipitation']}")
                    if box.get("humidity"):
                        meta_bits.append(f"Humidity: {box['humidity']}")
                    if box.get("wind"):
                        meta_bits.append(f"Wind: {box['wind']}")
                    if box.get("air_quality", {}).get("text"):
                        meta_bits.append(f"Air quality: {box['air_quality']['text']}")
                    if meta_bits:
                        out.append(" | ".join(meta_bits))

                    forecast = box.get("forecast", [])
                    if forecast:
                        out.append("\nForecast:")
                        for day in forecast[:5]:
                            temp = day.get("temperature", {})
                            out.append(
                                f"  {day.get('day', '?')}: "
                                f"High {temp.get('high', '?')}° / Low {temp.get('low', '?')}°, "
                                f"{day.get('weather', '')}"
                            )

                    return "\n".join(out)

                def _format_answer_weather_year_round(self, box: dict) -> str:
                    out = []
                    title = box.get("title", "")
                    source = box.get("source", "")
                    if title:
                        out.append(title + (f"  (Source: {source})" if source else ""))

                    temps = box.get("temperature", {})
                    rain = box.get("rainfall", {})
                    snow = box.get("snowfall", {})
                    daylight = box.get("daylight", {})

                    if temps:
                        out.append("\nMonthly averages:")
                        for month, t in temps.items():
                            r = rain.get(month, {})
                            s = snow.get(month, {})
                            d = daylight.get(month, {})
                            line = (
                                f"  {month.capitalize()}: "
                                f"{t.get('minimum_fahrenheit', '?')}–{t.get('maximum_fahrenheit', '?')}°F"
                            )
                            if r.get("average_rain_inches") is not None:
                                line += f", rain {r['average_rain_inches']}in"
                            if s.get("average_snow_inches") is not None:
                                line += f", snow {s['average_snow_inches']}in"
                            if d.get("average_daylight_hours_per_day") is not None:
                                line += f", daylight {d['average_daylight_hours_per_day']}h"
                            out.append(line)

                    return "\n".join(out)

                def _format_answer_finance(self, box: dict) -> str:
                    out = []
                    name = box.get("title", "")
                    exch = box.get("exchange", "")
                    stock = box.get("stock", "")
                    out.append(f"{name} ({exch}: {stock})".strip())

                    price = box.get("price")
                    currency = box.get("currency", "")
                    move = box.get("price_movement", {})
                    if price is not None:
                        line = f"Price: {price} {currency}"
                        if move:
                            arrow = "▲" if move.get("movement") == "Up" else "▼"
                            line += f"  {arrow} {move.get('price', '')} ({move.get('percentage', '')}%) {move.get('date', '')}"
                        out.append(line)

                    market = box.get("market", {})
                    if market.get("price") is not None:
                        mv = market.get("price_movement", {})
                        arrow = "▲" if mv.get("movement") == "Up" else "▼"
                        out.append(
                            f"{market.get('trading', 'After-hours')}: {market['price']}  "
                            f"{arrow} {mv.get('price', '')} ({mv.get('percentage', '')}%)"
                        )

                    if box.get("previous_close") is not None:
                        out.append(f"Previous close: {box['previous_close']}")

                    table = box.get("table", [])
                    if table:
                        out.append("  " + " | ".join(f"{row.get('name')}: {row.get('value')}" for row in table))

                    return "\n".join(out)

                def _format_answer_population(self, box: dict) -> str:
                    out = [f"{box.get('place', '?')}: {box.get('population', '?')} ({box.get('year', '?')})"]
                    other = box.get("other", [])
                    if other:
                        comp = ", ".join(f"{o.get('place')} {o.get('population')}" for o in other)
                        out.append(f"Other cities: {comp}")
                    return "\n".join(out)

                def _format_answer_dictionary(self, box: dict) -> str:
                    out = []
                    header = box.get("syllables", "")
                    if box.get("word_type"):
                        header += f"  ({box['word_type']})"
                    if header:
                        out.append(header)
                    if box.get("phonetic"):
                        out.append(f"Pronunciation: {box['phonetic']}")

                    defs = box.get("definitions", [])
                    if defs:
                        out.append("\nDefinitions:")
                        for i, d in enumerate(defs[:5], 1):
                            out.append(f"  {i}. {d}")

                    examples = box.get("examples", [])
                    if examples:
                        out.append("\nExamples:")
                        for ex in examples[:5]:
                            out.append(f'  - "{ex}"')

                    return "\n".join(out)

                def _format_answer_translation(self, box: dict) -> str:
                    t = box.get("translation", {})
                    src, tgt = t.get("source", {}), t.get("target", {})
                    out = [f"{src.get('text', '')} ({src.get('language', '')}) -> "
                        f"{tgt.get('text', '')} ({tgt.get('language', '')})"]
                    if src.get("pronunciation") or tgt.get("pronunciation"):
                        out.append(f"Pronunciation: {src.get('pronunciation', '')} -> {tgt.get('pronunciation', '')}")
                    return "\n".join(out)

                def _format_answer_flight_duration(self, box: dict) -> str:
                    out = [box.get("direction", "")]
                    out.append(f"Duration: {box.get('duration', '?')} ({box.get('stops', '?')})")
                    return "\n".join(out)

                def _format_answer_flights(self, box: dict) -> str:
                    out = [box.get("title", "")]
                    cheapest = box.get("cheapest_flights", [])
                    if cheapest:
                        c = cheapest[0]
                        out.append(f"Cheapest: {c.get('price', '?')} "
                                    f"({c.get('departure_date', '?')} -> {c.get('return_date', '?')})")
                    flights = box.get("flights", [])
                    if flights:
                        info = flights[0].get("flight_info", [])
                        out.append("Top option: " + ", ".join(info))
                    return "\n".join(out)

                def _format_answer_hotels(self, box: dict) -> str:
                    q = box.get("query", {})
                    out = []
                    loc_line = q.get("location", "")
                    days = q.get("days", [])
                    if days:
                        loc_line += f"  ({days[0]} - {days[-1]}"
                        if q.get("people"):
                            loc_line += f", {q['people']} guests"
                        loc_line += ")"
                    out.append(loc_line)

                    for i, h in enumerate(box.get("hotels", [])[:5], 1):
                        line = f"  {i}. {h.get('title', '?')} — {h.get('price', '?')}"
                        if h.get("rating"):
                            line += f" ({h['rating']}★"
                            if h.get("reviews"):
                                line += f", {h['reviews']} reviews"
                            line += ")"
                        out.append(line)

                    return "\n".join(out)

                def _format_answer_organic(self, box: dict) -> str:
                    out = []
                    if box.get("title"):
                        out.append(box["title"])
                    if box.get("link"):
                        out.append(f"URL: {box['link']}")
                    if box.get("answer"):
                        out.append(f"Answer: {box['answer']}")

                    if box.get("snippet"):
                        out.append(box["snippet"])
                    elif box.get("description"):
                        out.append(box["description"])

                    if box.get("list"):
                        out.append("")
                        for item in box["list"][:8]:
                            out.append(f"  - {item}")

                    if box.get("expanded_list"):
                        out.append("")
                        for item in box["expanded_list"][:8]:
                            line = f"  - {item.get('title', '')}"
                            if item.get("subtitle"):
                                line += f" ({item['subtitle']})"
                            out.append(line)

                    contents = box.get("contents")
                    if contents:
                        formatted = contents.get("formatted")
                        rows = []
                        if isinstance(formatted, dict):
                            for v in formatted.values():
                                if isinstance(v, list):
                                    rows.extend(v)
                        elif isinstance(formatted, list):
                            rows = formatted

                        if rows:
                            out.append("")
                            for row in rows[:8]:
                                if isinstance(row, dict):
                                    out.append("  " + " | ".join(f"{k}: {v}" for k, v in row.items()))
                        elif contents.get("table"):
                            out.append("")
                            for row in contents["table"][:8]:
                                if isinstance(row, list):
                                    out.append("  " + " | ".join(str(c) for c in row))

                    webfacts = box.get("webfacts")
                    if webfacts:
                        out.append("")
                        for fact in webfacts[:6]:
                            out.append(f"  {fact.get('title', '?')}: {fact.get('snippet', '?')}")

                    return "\n".join(out)

                def _format_answer_generic(self, box: dict) -> str:
                    out = []
                    for key in ("title", "result", "answer", "snippet", "description"):
                        if box.get(key):
                            out.append(f"{key.capitalize()}: {box[key]}")
                    if not out:
                        for k, v in box.items():
                            if k != "type" and isinstance(v, (str, int, float)):
                                out.append(f"{k}: {v}")
                    return "\n".join(out) if out else "(No displayable fields for this answer box type)"
                    

            try:
                client = SerpAPIClient()
                return client.search(query, engine, max_results)
            except ValueError as e:
                return f"ERROR: {str(e)}"
        except Exception as e:
            return f"ERROR: n{str(e)}"

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

    # ============================================================
    # MODEL CALLS
    # ============================================================
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
            for tool in OPENAI_TOOLS:
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
            return gemini_tools
        except ImportError:
            raise ImportError(
                "Google generativeai library required. Install with:\n"
                "pip install google-genai"
            )

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
                "tools": OPENAI_TOOLS,
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
       
    def _call_gemini_sync_interation(model_name: str, api_key: str, prompt: list[dict], thinking_level: str = "high", max_tool_calls: int = 10) -> Optional[str]:
        global global_interaction_id
        try:
            import google.genai as genai
            from google.genai._interactions import Omit
            client = genai.Client(api_key=api_key)
            
            system_instructions, user_input = _build_input_from_prompt(prompt) 
            print(f"[Gemini Interaction] Model: {model_name}, Thinking: {thinking_level}")
            
            interaction_id = global_interaction_id
            tool_call_count = 0
            while tool_call_count < max_tool_calls:
                print(f"\n[API Call #{tool_call_count + 1}]")
                
                interaction = client.interactions.create(
                    # api_version= 'v1',
                    model=model_name,
                    input=user_input,
                    system_instruction=system_instructions if system_instructions else Omit(),
                    tools=TOOLS, 
                    generation_config={
                        "thinking_level": thinking_level,
                        "temperature": 0.7,
                        "tool_choice": "auto"
                    },
                    previous_interaction_id=interaction_id if interaction_id is not None else Omit()
                )
                
                interaction_id = interaction.id
                has_tool_calls = False
                final_text = None
                length = len(interaction.steps)
                print(f"{interaction}\n\n")
                
                for step in interaction.steps:
                    if step.type == 'thought':
                        length = length - 1
                    if step.type == 'content':
                        length = length - 1
                    if step.type == 'model_output':
                        length = length -1
                        
                    
                    if step.type == "function_call":
                        print(f"Model wants to use {length} tool(s)")
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
                    global_interaction_id = interaction_id
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
            global_interaction_id = interaction_id
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _call_gemini_sync(model_name: str, api_key: str, messages: list[dict], max_tool_calls: int = 10) -> Optional[str]:
        try:
            import google.genai as genai
            from google.genai import types as genai_types
            
            client = genai.Client(api_key=api_key)
            gemini_tools = convert_openai_tools_to_gemini()     
            system_instructions, user_parts =_build_input_from_prompt(messages)
            tool_response = None
            assistant_response = None
            
            user_input = genai_types.Content(
                role='user',
                parts=[genai_types.Part.from_text(text=user_parts)],
            )
                
            tool_call_count = 0
                
            while tool_call_count < max_tool_calls:
                print(f"\n[Gemini Call #{tool_call_count + 1}]")
                    
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        user_input,
                        assistant_response if assistant_response is not None else "",
                        tool_response if tool_response is not None else ""
                    ],
                    config=genai_types.GenerateContentConfig(
                        system_instruction= system_instructions if system_instructions else None,
                        tools= gemini_tools,
                        thinking_config= genai_types.ThinkingConfig(thinking_level="high"),
                        temperature= 0.7,
                    )
                )
                
                print(response)
                print(f"Response finish reason: {response.candidates[0].finish_reason}")
                    
                if response.parts[0].function_call:
                    print("Model using tools...")
                    
                    tool_uses = []
                    for part in response.candidates[0].content.parts:
                        if part.function_call and isinstance(part.function_call, genai_types.FunctionCall):
                            tool_uses.append(part.function_call)
                            
                        if not tool_uses:
                            print("No tool calls found despite TOOL_USE finish reason")
                            tool_call_count =+ 1
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
                                genai_types.Part.from_function_response(
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
   
    # ============================================================
    # TELEGRAM MESSAGE CHUNCKING
    # ============================================================
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
       
    # ============================================================
    # MODEL ROUTING
    # ============================================================ 
    if gemini_key:
        try:
            result = await _call_gemini(prompt, gemini_key, GEMINI_MODEL)
        except Exception as exc:
            logger.warning(f"Gemini model raised error: {exc}")
            await context.bot.set_message_reaction(update.effective_user.id, update.effective_message.id, reaction= [tg.ReactionTypeEmoji('😢')])
            await update.message.reply_text(text=f"AI model raised error: {exc}\nPlease try the prompt again.", do_quote= True)
            result = None
        if result is not None:
            await _safe_reply(update, context, result, parse_mode=None, disable_web_page_preview=False)
        
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
    
# ============================================================
# MAIN CALL FUNCTION
# ============================================================
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

