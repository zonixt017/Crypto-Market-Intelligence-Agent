# MUST Market Intelligence Agent

> An AI-powered multi-agent system that monitors Binance markets and delivers 
> plain-English, prioritized intelligence reports for traders and fintech 
> decision-makers who don't have time to stare at charts.

---

## The Problem — Why I Built This

My name is Advay Binu. I started my crypto journey on Binance, moved through 
Web3 wallets, discovered decentralized exchanges, and eventually found myself 
trading memecoins on the Solana network.

I once made a profitable trade — picked the right coin, got in at the right time. 
And still lost money.

Why? Because when I tried to sell, the liquidity wasn't there. My sell order 
moved the price against me. I had the right call and the wrong exit.

That experience taught me something nobody's crypto tool actually addresses: 
**the real problem isn't finding opportunities — it's understanding whether 
you can act on them safely.**

Every crypto intelligence tool I've used since then — DexTools, Birdeye, 
TradingView — is built for people who already speak the language. Charts, 
RSI, order book depth, candlestick patterns. They give you data. Nobody gives 
you clarity.

This agent does one thing: it takes Binance market complexity and converts it 
into prioritized, plain-English decisions — for traders and fintech business 
owners who need to act, not analyze.

---

## Why This Problem Is #1 Priority

In AI-native fintech, the bottleneck is no longer data. Data is everywhere, 
free, and real-time. The bottleneck is **translation** — converting market 
signals into decisions that non-technical stakeholders can act on.

A product owner at a crypto startup doesn't need another dashboard. They need 
an agent that taps them on the shoulder and says: *"SOL is showing unusual 
volume with deep liquidity right now — this looks real and actionable."*

That's the gap this agent fills. And in a world where AI can compress 3 months 
of development into a week, the teams that define this problem clearly and solve 
it first will create enormous value.

---

## Architecture — Three Agents, One Pipeline

This project follows a strict three-agent architecture where each agent owns 
exactly one responsibility:
```
Binance Public API
       │
       ▼
┌─────────────────┐
│  Watcher Agent  │  ← Detects anomalies vs each coin's own baseline
└────────┬────────┘
         │ flagged symbols
         ▼
┌─────────────────┐
│  Analyst Agent  │  ← Scores momentum, volume, liquidity, authenticity
└────────┬────────┘
         │ scored results
         ▼
┌─────────────────┐
│ Narrator Agent  │  ← Generates plain-English reports via Groq LLaMA
└────────┬────────┘
         │
         ▼
  Prioritized Report
  (HIGH / MONITOR / IGNORE)
```

### Agent 1 — Watcher
Polls Binance public endpoints continuously. Compares each coin's current 
behavior against its own recent baseline — not against the market average. 
A coin that normally trades 1M volume/hour suddenly trading 8M is flagged. 
A coin that normally trades 50M trading 8M is ignored.

Endpoints used (all public, no authentication):
- `/api/v3/ticker/24hr` — price change and volume data
- `/api/v3/klines` — candlestick history for baseline calculation
- `/api/v3/depth` — order book for liquidity assessment
- `/api/v3/trades` — recent trades for authenticity analysis

### Agent 2 — Analyst
Takes flagged coins and produces four component scores (0-100 each):

| Score | What It Measures |
|-------|-----------------|
| Momentum | Speed and strength of price movement |
| Volume | How unusual current volume is vs baseline |
| Liquidity | Whether a position could be exited safely |
| Authenticity | Whether volume looks genuine vs wash trading |

Also detects market-wide anomaly events — when everything moves together, 
individual signals are less actionable and scores are penalized accordingly.

### Agent 3 — Narrator
Powered by Groq LLaMA 3.3 70B. Takes the Analyst's structured scores and 
generates a three-sentence plain-English report calibrated for a non-technical 
audience. Strict prompt engineering ensures consistent format, no jargon, and 
direct actionable output every time.

**Example output:**
```
🔴 HIGH — SOLUSDT — Score: 78.4/100
SOL is seeing a volume surge 8x its normal level at $87, backed by deep 
liquidity that would support a real position exit. This looks like genuine 
market activity rather than artificial pumping, making it one of the more 
credible signals in today's session. HIGH: worth serious attention — 
conditions support both entry and exit at current levels.
```

---

## Performance Metrics — Scored 6125 / 10000

The agent is scored on a custom 1-10,000 scale across four dimensions:

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Signal Accuracy | 40% (4000 pts) | 800 | Conservative — improves with more market data |
| Narration Quality | 35% (3500 pts) | 3325 | 95% — reports consistently meet all quality criteria |
| Pipeline Speed | 15% (1500 pts) | 1000 | 10.4 seconds — expected for 3 sequential API calls |
| Coverage | 10% (1000 pts) | 1000 | 100% — all results have complete component scores |

**Final Score: 6125 / 10000**

### Calculation Method
```
Signal Accuracy:   (meaningful_signals / total_results) × 4000
                   meaningful = priority not IGNORE and score > 35

Narration Quality: (quality_points / max_points) × 3500
                   quality = length 40-90 words + priority present + 
                   no jargon + price reference

Pipeline Speed:    <10s = 1500pts | 10-20s = 1000pts | 
                   20-30s = 500pts | >30s = 200pts

Coverage:          (results_with_all_4_scores / total_results) × 1000
```

---

## Benchmark — vs Default Claude in Cursor

Same live Binance data. Two approaches.

| Criteria | This Agent | Default Claude in Cursor |
|----------|-----------|------------------------|
| Output format | Consistent 3-sentence report every time | Varies — sometimes bullets, sometimes paragraphs |
| Audience | Non-technical decision maker | Defaults to technical framing |
| Speed | ~10 seconds automated | Manual copy-paste required |
| Jargon | None by design | RSI, MACD, support levels common |
| Actionability | Always ends with clear recommendation | Often hedged with "it depends" |
| Runs autonomously | Yes — continuous mode available | No |
| Liquidity assessment | Built-in from order book data | Not assessed unless explicitly asked |

**Key insight:** Default Claude is more flexible but less consistent. This agent 
is purpose-built — it trades flexibility for reliability, which is exactly what 
a production tool needs.

---

## Quickstart

### Prerequisites
- Python 3.9+
- Groq API key (free at console.groq.com — no credit card required)

### Setup
```bash
git clone https://github.com/zonixt017/must-market-intel
cd must-market-intel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### Run
```bash
# Single scan
python run.py --once

# Autonomous continuous monitoring
python run.py --continuous

# Test mode with mock data (no API key needed for Binance)
python run.py --test
```

### Configure
Edit `config.yaml` to customize:
```yaml
scan_interval: 300          # seconds between scans
user_symbols: []            # empty = top 20 by volume
                            # or specify: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
anomaly_thresholds:
  volume_ratio: 2.0         # flag if volume is 2x baseline
  price_change_ratio: 1.8   # flag if price move is 1.8x baseline
```

---

## Project Structure
```
must-market-intel/
├── agents/
│   ├── watcher.py          # Agent 1 — anomaly detection
│   ├── analyst.py          # Agent 2 — multi-dimensional scoring
│   └── narrator.py         # Agent 3 — LLM report generation
├── core/
│   ├── binance_client.py   # All Binance API calls
│   ├── orchestrator.py     # Pipeline coordination
│   └── scorer.py           # Performance benchmarking
├── output/
│   └── reports/            # Saved JSON + text reports
├── tests/
│   └── test_pipeline.py    # Mock data pipeline tests
├── .cursorrules            # Cursor multi-agent configuration
├── config.yaml             # User configuration
├── run.py                  # Main entry point
└── requirements.txt
```

---

## Design Decisions

**Why Binance public API only?**
Security and shareability. No authentication means no credentials to manage, 
no risk of accidental exposure, and the repo can be fully public immediately.

**Why three separate agents instead of one script?**
Each agent is independently testable, replaceable, and improvable. If a better 
liquidity scoring method emerges, only analyst.py changes. If we switch from 
Groq to another LLM, only narrator.py changes. This is how production systems 
should be built.

**Why Groq LLaMA instead of Claude or GPT?**
Generous free tier (14,400 requests/day), no regional restrictions, 
OpenAI-compatible API, and fast inference. For a portfolio project and an 
agent running continuously, free and reliable beats expensive and capable.

**Why plain-English output instead of dashboards?**
Because the user who needs a dashboard already has ten of them. The user who 
needs this agent is the one who doesn't have time to learn another tool.

---

## Roadmap — What's Coming

This is v1.0 — the intelligence layer. The roadmap builds toward full autonomy:

**v1.1 — Smarter Signals**
- DEX data integration (Raydium, Uniswap) for memecoin and low-cap coverage
- On-chain wallet concentration analysis
- News sentiment correlation

**v1.2 — User Personalization**
- Portfolio-aware monitoring (watch only coins you hold)
- Custom alert thresholds per coin
- Telegram/Discord notification integration

**v2.0 — Autonomous Execution**
- Rule-based trade execution via Binance authenticated API
- User-defined risk parameters and position sizing
- Eliminate FOMO — the agent monitors everything simultaneously and acts 
  within your defined rules while you sleep

The vision: a personal AI trading companion that watches markets 24/7, 
understands context, and acts on your behalf — so you never miss an 
opportunity because you weren't watching, and never get trapped in an 
illiquid position because you weren't paying attention.

---

## Security

- Zero hardcoded credentials — all secrets via environment variables
- Only public Binance endpoints — no authentication required
- `.env` excluded from repository via `.gitignore`
- No user data stored or transmitted beyond local output files

---

## Built By

Advay Binu — AI-native developer focused on building systems that translate 
complexity into clarity.

Built as a quest submission for MUST Company's FDE/APO hiring process.
Even if it doesn't land the job, it solves a real problem I personally faced.
That's the only reason worth building anything.

---

*"Don't compete with a shovel against an excavator in a digging battle."*
— MUST Company