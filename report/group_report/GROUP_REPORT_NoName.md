# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: No Name
- **Team Members**: Nguyễn Dương Hiếu 2A202600822, Đoàn Minh Hiếu 2A202600841, Lê Nguyễn Minh Quân 2A202600821
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Mục tiêu của dự án là nâng cấp một **Baseline Chatbot** (chỉ LLM, không tools) thành **ReAct Agent** có khả năng tự suy luận và gọi công cụ thực tế. Agent áp dụng vòng lặp *Thought → Action → Observation* để xử lý các truy vấn đa bước về chứng khoán — việc mà Chatbot thường hallucinate hoặc từ chối vì không có dữ liệu live.

- **Success Rate**: 100% trên kịch bản kiểm thử chính (sau fix JSON parser + Observation hallucination).
- **Key Outcome**: Với bộ **5 tools** (finance + visual), Agent hoàn thành được pipeline phân tích NVDA/AAPL: lấy tin tức, tính SMA/RSI, vẽ biểu đồ lưu vào `charts/`, rồi tổng hợp lời khuyên. Chatbot baseline (`test_chatbot.py`) chỉ trả lời từ trí nhớ LLM — không thể thực hiện các bước trên.

**Entry points:**

| Mode | File | Mô tả |
| :--- | :--- | :--- |
| Chatbot baseline | `test_chatbot.py` | LLM-only, prompt tiếng Việt |
| ReAct Agent | `test_agent.py` | Agent + 5 tools |
| So sánh song song | `demo.py` | Chatbot vs Agent cùng câu hỏi |
| Web local | `web_server.py` | UI tại `http://localhost:8787` |

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Thought   │ ──► │    Action    │ ──► │ Observation │ ──► │ Final Answer │
│  (reasoning)│     │ (JSON tool)  │     │ (tool result)│     │  (to user)   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
     ▲                    │                                         │
     └────────────────────┘         (lặp tối đa max_steps=10)         ▼
```

1. **Thought**: LLM phân tích cần làm gì tiếp theo.
2. **Action**: LLM xuất JSON `{"tool": "...", "args": {"ticker": "AAPL"}}` — hệ thống parse và gọi hàm Python.
3. **Observation**: Kết quả tool (JSON) được append vào conversation — **hệ thống cung cấp**, LLM không được tự viết.
4. **Final Answer**: Khi đủ dữ liệu, Agent dừng vòng lặp và trả lời user.

**Fixes quan trọng trong `src/agent/agent.py`:**
- Parse JSON bằng cách tìm cặp `{}` khớp (tránh lỗi nested args).
- Strip nội dung sau `Observation:` nếu LLM tự hallucinate Observation (bug Phase 4).
- System Prompt v2: cấm markdown code block, cấm bịa tool name.

### 2.2 Tool Definitions (Inventory)

Agent sử dụng **`FINANCE_TOOLS + VISUAL_TOOLS`** (5 tools):

| Tool Name | Input | Output | Use Case |
| :--- | :--- | :--- | :--- |
| `get_company_info` | `{"ticker": "AAPL"}` | JSON | Tên công ty, sector, industry, market cap, summary |
| `get_stock_price` | `{"ticker": "AAPL"}` | JSON | Giá hiện tại, open/high/low, volume (yfinance) |
| `get_stock_news` | `{"ticker": "NVDA"}` | JSON | 5 tin tức mới nhất (title, publisher, link) |
| `get_technical_indicators` | `{"ticker": "AAPL"}` | JSON | SMA 20, SMA 50, RSI 14, trend Bullish/Bearish (6 tháng data) |
| `plot_stock_chart` | `{"ticker": "AAPL"}` | JSON + PNG | Vẽ biểu đồ giá 6 tháng + SMA 20/50, lưu `charts/{TICKER}_chart.png` |

**Phân loại:**
- `src/tools/finance_tools.py` — 4 tools dữ liệu (yfinance + pandas)
- `src/tools/visual_tools.py` — 1 tool visualization (matplotlib)

### 2.3 Chatbot Baseline vs Agent

| | Chatbot (`test_chatbot.py`) | Agent (`test_agent.py`) |
| :--- | :--- | :--- |
| Tools | Không | 5 tools |
| Prompt | *"Bạn là trợ lý tài chính thông minh..."* | ReAct system prompt v2 |
| Dữ liệu | Trí nhớ LLM | yfinance live + chart file |
| LLM calls | 1 | 1–10 (multi-step) |

### 2.4 LLM Providers Used

- **Primary**: OpenAI **gpt-4o-mini** (cấu hình trong `.env`, tiết kiệm chi phí)
- **Secondary**: Google Gemini (`DEFAULT_PROVIDER=gemini`)
- **Local (optional)**: Phi-3-mini qua `llama-cpp`

---

## 3. Telemetry & Performance Dashboard

Dựa trên log `logs/` và test thực tế:

| Metric | Chatbot Baseline | ReAct Agent |
| :--- | :--- | :--- |
| Avg Latency | ~3–8s | ~15–60s (tùy số tools gọi) |
| LLM calls | 1 | 3–8 (query phức tạp NVDA+AAPL) |
| Tools used | 0 | 4–6 (news ×2, indicators ×2, chart ×2) |
| Tokens (ước tính) | ~650 | ~1,800+ |

- **Test query chuẩn** (dùng trong `test_chatbot.py` / `test_agent.py`):
  > *"Phân tích NVDA và AAPL: tin tức, SMA/RSI, vẽ biểu đồ 6 tháng, lời khuyên đầu tư"*
- **Total Cost**: ~$0.02–0.05 / lần chạy full pipeline (gpt-4o-mini)
- **Trade-off**: Agent chậm hơn nhưng có output có thể verify (giá, RSI, file PNG)

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: JSON Parser Error (nested args)

- **Input**: Agent gọi `get_stock_price` với ticker AAPL
- **Log**: `JSON_PARSER_ERROR` — JSON bị cắt sớm tại `}` trong `"args"`
- **Root Cause**: Regex non-greedy `.*?` cắt JSON lồng nhau
- **Fix**: Parse từ `{` đầu tiên, lặp ngược tìm `}` khớp → **0% lỗi parse** sau fix

### Case Study 2: Observation Hallucination

- **Input**: Agent tự viết `Observation: Giá AAPL là 150 USD...` trong output LLM
- **Root Cause**: LLM hallucinate Observation trước khi hệ thống gọi tool → dữ liệu sai
- **Fix**: Strip mọi nội dung sau `Observation:` trong LLM output trước khi parse Action
- **Result**: Agent buộc phải chờ Observation thật từ tool execution

### Case Study 3: Multi-ticker + Chart pipeline

- **Input**: Phân tích cả NVDA và AAPL (6+ tool calls)
- **Risk**: Timeout nếu `max_steps` quá thấp
- **Mitigation**: Tăng `max_steps=10`, sleep 3s giữa các step tránh rate limit API

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs v2

- **v1**: Action format lỏng, LLM hay wrap JSON trong markdown
- **v2**: Raw JSON only, cấm hallucinate Observation, cấm invent tool names
- **Result**: Format error giảm về 0%; tool call success rate 100%

### Experiment 2: 3 tools vs 5 tools

| Giai đoạn | Tools | Khả năng |
| :--- | :--- | :--- |
| Phase 3 | 3 (price, info, news) | Trả lời giá + tin tức |
| Phase 4+ | + `get_technical_indicators`, + `plot_stock_chart` | Phân tích xu hướng (SMA/RSI) + biểu đồ PNG |

Agent mới đáp ứng được full test query của lab (tin tức + chỉ số kỹ thuật + chart).

### Experiment 3: Chatbot vs Agent

| Case | Chatbot (`test_chatbot.py`) | Agent (`test_agent.py`) | Winner |
| :--- | :--- | :--- | :--- |
| Câu hỏi đơn giản (sector AAPL) | Trả lời nhanh từ memory | Gọi tool, verified | Draw |
| Giá live AAPL/NVDA | Từ chối / đoán | Giá thật từ yfinance | **Agent** |
| Tin tức + SMA/RSI | Hallucinate số liệu | SMA_20, SMA_50, RSI_14 thật | **Agent** |
| Vẽ biểu đồ 6 tháng | Không thể | `charts/AAPL_chart.png`, `charts/NVDA_chart.png` | **Agent** |
| Full pipeline NVDA+AAPL | Text chung chung | Multi-step 6+ tools, tổng hợp có căn cứ | **Agent** |

---

## 6. Production Readiness Review

- **Security**: Validate `ticker` input (uppercase, alphanumeric); API keys trong `.env`; không execute arbitrary code từ LLM
- **Guardrails**:
  - `max_steps=10` — đủ cho multi-ticker + chart, tránh loop vô hạn
  - Strip LLM-hallucinated Observations
  - Tool whitelist-only (5 tools đã đăng ký)
- **Observability**: JSON logs (`AGENT_START`, `LLM_METRIC`, `TOOL_CALL`, `AGENT_END`) trong `logs/`; web UI hiển thị trace Thought/Action/Observation
- **Scaling**: Với 5 tools, ReAct loop đủ dùng. Mở rộng >10 tools → cân nhắc LangGraph hoặc RAG tool retrieval
- **Artifacts**: Chart PNG lưu tại `charts/` — cần cleanup policy nếu deploy production

---

## Appendix: Reproduce

```bash
# Chatbot baseline (không tools)
.venv/bin/python test_chatbot.py

# ReAct Agent (5 tools)
.venv/bin/python test_agent.py

# So sánh song song
.venv/bin/python demo.py "Phân tích NVDA và AAPL"

# Web local
.venv/bin/python web_server.py   # → http://localhost:8787
```
