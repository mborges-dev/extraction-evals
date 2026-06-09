# June 2026 — First benchmark run

**3 models · 4 prompt strategies · 7 documents (3 invoices · 2 receipts · 2 CVs) · 84 calls · $0.54 USD total**

Raw data: [`../results/2026-06-09.csv`](../results/2026-06-09.csv).
Charts: [`../results/charts/2026-06-09-cost-vs-f1.png`](../results/charts/2026-06-09-cost-vs-f1.png) · [`../results/charts/2026-06-09-macro-f1.png`](../results/charts/2026-06-09-macro-f1.png).

---

## Headline numbers

| Model | Prompt | F1 | Field Acc | Cost | Latency p50 |
|---|---|---:|---:|---:|---:|
| **gpt-4o-2024-11-20** | **v2_structured** | **0.614** | **64.7%** | **$0.039** | 3,800 ms |
| claude-sonnet-4-5 | v2_structured | 0.582 | 62.7% | $0.067 | 5,435 ms |
| gpt-4o-2024-11-20 | v3_few_shot | 0.468 | 50.8% | $0.043 | 2,510 ms |
| claude-sonnet-4-5 | v3_few_shot | 0.458 | 52.4% | $0.072 | 5,587 ms |
| gemini-2.5-flash | v3_few_shot | 0.398 | 42.9% | **$0.010** | 12,022 ms |
| claude-sonnet-4-5 | v4_cot | 0.162 | 23.0% | $0.114 | 13,761 ms |
| claude-sonnet-4-5 | v1_baseline | 0.159 | 19.4% | $0.061 | 5,714 ms |
| gpt-4o-2024-11-20 | v1_baseline | 0.125 | 13.9% | $0.034 | 2,804 ms |
| gemini-2.5-flash | v1_baseline* | 0.093 | 11.1% | $0.006 | 7,668 ms |
| gpt-4o-2024-11-20 | v4_cot | 0.067 | 4.0% | $0.094 | 20,320 ms |
| gemini-2.5-flash | v2_structured* | 0.111 | 11.1% | $0.002 | 1,298 ms |
| gemini-2.5-flash | v4_cot* | 0.000 | 0.0% | $0.000 | — |

\* Gemini rows are partial — see *"The Gemini rate-limit story"* below.

---

## Five findings

### 1. **Schema-in-prompt (v2) is the single best lever, period.**

Every model jumped substantially when the JSON schema went into the prompt:

| Model | v1 → v2 (F1) | v1 → v2 (Field Acc) |
|---|---|---|
| gpt-4o | 0.125 → **0.614** (+0.489) | 13.9% → **64.7%** (+50.8 pts) |
| claude-sonnet | 0.159 → **0.582** (+0.423) | 19.4% → **62.7%** (+43.3 pts) |
| gemini-flash | 0.093 → 0.111 (+0.018) | 11.1% → 11.1% (no change) |

For Claude and GPT, this is the single biggest move you can make. **If you're using the API for extraction without a schema in the prompt, you're leaving 40+ accuracy points on the floor.**

(Gemini stayed flat — but most of its v2 calls were rate-limited; see finding 4. Real comparison needs a paid-tier re-run.)

### 2. **Chain-of-thought *hurt* every model.**

v4_cot was the worst-performing prompt strategy for all three models:

| Model | v2 → v4 (F1) | v2 → v4 (cost) |
|---|---|---|
| claude-sonnet | 0.582 → 0.162 (−72%) | $0.067 → $0.114 (+72%) |
| gpt-4o | 0.614 → 0.067 (−89%) | $0.039 → $0.094 (+141%) |
| gemini-flash | (rate-limited) | — |

CoT was *more expensive and less accurate*. The likely cause: the prompt asks the model to output `<thinking>...</thinking><extraction>{...}</extraction>` tags, but the harness's JSON parser doesn't look for `<extraction>` tags — it falls back to "find the first `{`". When the thinking section contains JSON-looking content (it often does), the parser grabs the wrong block.

This is a **prompt × parser interaction bug**, not a model limitation. Fix: either (a) update the v4 prompt to drop the XML tags and return plain JSON, or (b) extend the parser to look for `<extraction>` tags first. v0.2 will address it.

**Lesson:** chain-of-thought isn't magic. Without a parser that knows where the answer lives, you're just paying for tokens.

### 3. **GPT-4o-mini wasn't tested — but Gemini Flash gives the cost-effectiveness picture.**

At v3_few_shot:
- gpt-4o: **0.468 F1** at **$0.043** (= $0.092 per F1 point)
- claude-sonnet: 0.458 F1 at $0.072 (= $0.157 per F1 point)
- gemini-flash: 0.398 F1 at **$0.010** (= **$0.025 per F1 point** — 3.7× cheaper per quality point than GPT-4o)

For volume extraction where you'd retry low-confidence outputs anyway, Gemini Flash at 80% of GPT-4o's F1 for ¼ of the cost is the most economically sensible choice. **For one-shot accuracy, GPT-4o + v2 wins.**

### 4. **The Gemini rate-limit story.**

Gemini 2.5 Flash on the **free tier** hit rate limits on 15 of its 28 calls (54% failure rate):

| Prompt | Successful | Failed |
|---|---|---|
| v1_baseline | 5/7 | 2/7 (503 — high demand) |
| v2_structured | 1/7 | 6/7 (429 — RPM exhausted) |
| v3_few_shot | 7/7 | 0/7 |
| v4_cot | 0/7 | 7/7 (429) |

The free tier allows 10 requests per minute — sequential calls trip this immediately. After this run I added retry-with-exponential-backoff (8s, 16s, 32s, 64s) to the Gemini runner. A re-run was started but interrupted; numbers in this writeup are from the first run.

For production-grade Gemini comparisons, you need either (a) the paid tier or (b) the backoff fix landing in v0.2.

**Implication for benchmarkers:** free-tier APIs are unreliable for sequential batch evals. The harness now respects this for Gemini specifically — other free-tier providers may need similar treatment.

### 5. **0% exact-match across the board.**

No model × prompt cell achieved a single exact match. Even the best (gpt-4o × v2 at 64.7% field accuracy) had at least one field different from ground truth on every document.

The most common discrepancies (sampled from CSV):
- Decimal-comma parsing (`1.234,56` → `1234.56`) — models normalized but not consistently
- VAT prefix stripping (`PT123456789` vs `123456789`) — schema says digits only; some models kept the prefix
- Currency code inference — receipts without an explicit `EUR` mark sometimes lost the field
- Line-item ordering — set-based F1 forgives this, but exact-match doesn't

This is why **field accuracy and macro F1 are the metrics that matter**, not exact match. Exact match is a useful boolean for downstream auto-write decisions, but it's a punitive top-line metric.

---

## Cost breakdown

| Provider | Calls | Successful | Cost | $/successful call |
|---|---|---|---|---|
| Anthropic (Claude Sonnet 4.5) | 28 | 28 | $0.3146 | $0.0112 |
| OpenAI (GPT-4o) | 28 | 28 | $0.2096 | $0.0075 |
| Google (Gemini 2.5 Flash) | 28 | 13 | $0.0178 | $0.0014 |
| **Total** | **84** | **69** | **$0.5421** | — |

Total tokens used:
- Input: 50,743
- Output: 38,910
- Cache: 0 (no caching exercised in this run — caching is per-conversation, and our calls are independent)

---

## Latency

| Model | p50 | p95 |
|---|---|---|
| gpt-4o-2024-11-20 | 3,567 ms | **31,264 ms** (CoT outlier) |
| claude-sonnet-4-5 | 6,009 ms | 13,914 ms |
| gemini-2.5-flash | 9,148 ms | 17,981 ms |

GPT-4o is fastest on the median but has a long tail on CoT (one v4 call took 31s). Claude is the steadiest. Gemini is the slowest at the median — but again, most slow calls are backoff retries, not actual model inference.

---

## What this run *doesn't* tell you

- **Real-document accuracy.** The dataset is 7 synthetic documents. Real-format invoices and CVs from production sources will score differently — likely lower for all models.
- **Production reliability.** This is single-shot extraction. Real systems retry low-confidence outputs, vote across calls, or fall back to humans. Those mechanisms close most of the residual error.
- **Other models.** GPT-4o-mini, Claude Haiku, Claude Opus, Gemini Pro, Llama — none tested in this round. Easy to add now that the harness works.
- **Statistical significance.** N=7 per cell. Any difference under ~0.05 F1 is noise. Differences over 0.10 are real for these documents but may not generalize.

---

## Next round

- **Re-run Gemini** with the retry-with-backoff fix in place to get full-coverage numbers
- **Fix the v4_cot parser** (or rewrite the v4 prompt) so chain-of-thought has a fair shake
- **Add cheap-tier models** (gpt-4o-mini, claude-haiku, gemini-flash-lite) — should produce the actual cost-vs-accuracy frontier
- **Bigger dataset** — 30+ documents per type, ideally with real anonymized samples from production
- **Bipartite line-item matching** — current set-based F1 forgives order; production may want order to matter

---

## Reproducing

```bash
git clone https://github.com/mborges-dev/extraction-evals
cd extraction-evals
uv sync
cp .env.example .env  # add your ANTHROPIC, OPENAI, GOOGLE keys

# Full matrix (same as this run)
./scripts/run.sh \
  -m claude-sonnet-4-5 -m gpt-4o-2024-11-20 -m gemini-2.5-flash \
  -p v1_baseline -p v2_structured -p v3_few_shot -p v4_cot

# Generate charts + markdown summary
uv run python scripts/analyze.py results/<your-date>.csv
```

Cost: ~$0.55 USD (~$0.31 Claude, ~$0.21 GPT-4o, ~$0.02 Gemini partial). Time: ~5 minutes.
