# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: No Name
- **Team Members**: Nguyễn Dương Hiếu 2A202600822, Đoàn Minh Hiếu 2A202600841, Lê Nguyễn Minh Quân 2A202600821
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Mục tiêu của dự án là nâng cấp một hệ thống Chatbot cơ bản thành một **ReAct Agent** có khả năng tự suy luận và sử dụng các công cụ (Tools) để thu thập dữ liệu thời gian thực. Bằng cách áp dụng vòng lặp *Thought -> Action -> Observation*, Agent có thể giải quyết các bài toán phức tạp đòi hỏi số liệu chính xác mà Chatbot truyền thống thường hay bịa đặt (hallucinate).

- **Success Rate**: 100% trên các kịch bản kiểm thử (sau khi fix lỗi Regex Parser).
- **Key Outcome**: Agent của chúng tôi vượt trội hoàn toàn so với Baseline Chatbot trong kịch bản truy vấn đa bước (Multi-step). Bằng cách sử dụng công cụ chứng khoán `yfinance`, Agent không chỉ đưa ra được báo giá chính xác đến 2 chữ số thập phân cho AAPL và NVDA mà còn tổng hợp tin tức trong ngày để đưa ra lời khuyên đầu tư, điều mà Chatbot hoàn toàn bất lực.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Hệ thống được thiết kế theo kiến trúc ReAct chuẩn mực:

1. **Thought**: LLM nhận luồng prompt, phân tích xem cần phải làm gì tiếp theo.
2. **Action**: LLM xuất ra chuỗi JSON chứa tên công cụ (`tool`) và tham số (`args`). Hệ thống Python bắt chuỗi này, parse JSON và thực thi hàm tương ứng.
3. **Observation**: Kết quả của hàm (dữ liệu chứng khoán/tin tức) được trả về, đóng gói thành văn bản và nhét ngược lại vào prompt.
4. **Final Answer**: Khi Agent xác định đã đủ dữ kiện, nó dừng vòng lặp và xuất ra câu trả lời cuối cùng cho người dùng.

### 2.2 Tool Definitions (Inventory)

Chúng tôi đã xây dựng bộ 3 công cụ tài chính mạnh mẽ tận dụng thư viện `yfinance`:

| Tool Name            | Input Format             | Use Case                                                                               |
| :------------------- | :----------------------- | :------------------------------------------------------------------------------------- |
| `get_company_info` | `{"ticker": "string"}` | Lấy thông tin tổng quan của công ty (Ngành nghề, vốn hóa, tóm tắt).         |
| `get_stock_price`  | `{"ticker": "string"}` | Lấy giá cổ phiếu thời gian thực (Giá hiện tại, cao/thấp trong ngày).        |
| `get_stock_news`   | `{"ticker": "string"}` | Lấy 5 tin tức mới nhất về mã cổ phiếu bao gồm tiêu đề, publisher và Link. |

### 2.3 LLM Providers Used

- **Primary**: `gpt-4o` (Tốc độ cao, khả năng tuân thủ JSON format xuất sắc).
- **Secondary (Backup)**: `gemini-1.5-flash` (Hỗ trợ thay đổi thông qua biến môi trường trong `.env`).

---

## 3. Telemetry & Performance Dashboard

Dựa trên dữ liệu thu thập được từ hệ thống `logger` trong thư mục `logs/`:

- **Average Latency (ReAct Agent)**: ~15,000ms (Bao gồm 3 steps suy nghĩ và 2 lần call API mạng).
- **Average Latency (Chatbot Baseline)**: ~8,183ms (Chỉ 1 step sinh text).
- **Average Tokens per Task (Chatbot)**: 664 tokens.
- **Average Tokens per Task (ReAct Agent)**: Ước tính ~1,800 tokens (Do cơ chế ReAct phải nhồi lại lịch sử Observation sau mỗi step).
- **Total Cost of Test Suite**: ~0.02$ cho một lần chạy đa bước.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

Trong quá trình phát triển Phase 3, chúng tôi đã gặp một lỗi chí mạng và được ghi nhận rõ ràng trong file log:

### Case Study: JSON Parser Error (Regex tham lam)

- **Input**: "Kiểm tra giá cổ phiếu Apple..."
- **Observation / Log**: Hệ thống ghi nhận `LLM_METRIC` lỗi `JSON_PARSER_ERROR` liên tục 5 lần cho đến khi bị Timeout.
  ```json
  {"error": "JSON_PARSER_ERROR", "content": "{\"tool\": \"get_stock_price\", \"args\": {\"ticker\": \"AAPL\"}"}
  ```
- **Root Cause**: LLM trả về cấu trúc JSON đúng nhưng format lồng nhau. Hàm Regex `r"Action:\s*(\{.*?\})"` của chúng tôi sử dụng toán tử `.*?` không tham lam (non-greedy), dẫn đến việc nó cắt chuỗi ngay ở dấu `}` đầu tiên nó gặp (thuộc về phần `"args": {"ticker": "AAPL"}`), làm mất dấu ngoặc đóng của object cha.
- **Fix**: Viết lại cơ chế Parse JSON. Cắt toàn bộ chuỗi từ ký tự `{` đầu tiên và lặp ngược từ cuối chuỗi để tìm dấu `}` khớp nhất, đảm bảo tính toàn vẹn của JSON dù có lồng bao nhiêu cấp.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

- **Diff**: Cập nhật System Prompt v1 lên v2 sau sự cố Failure Analysis. Thêm Rule: *"MUST be raw, valid JSON. DO NOT wrap it in Markdown code blocks"* và yêu cầu LLM tự xử lý lỗi nếu Observation báo `Error`.
- **Result**: Tỷ lệ lỗi Format/Hallucination giảm xuống 0%. LLM không còn xuất markdown thừa mứa làm kẹt Parser.

### Experiment 2: Chatbot vs Agent

| Case                                                          | Chatbot Result                                                          | Agent Result                                                                            | Winner            |
| :------------------------------------------------------------ | :---------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- | :---------------- |
| Simple Q&A                                                    | Chính xác, phản hồi nhanh (8s)                                      | Trả lời dài dòng, mất thời gian check tool                                        | **Chatbot** |
| Multi-step (Check giá AAPL & NVDA, đọc tin tức, so sánh) | Hallucinated (Bịa đặt hoặc từ chối trả lời vì thiếu Internet) | Chính xác 100%. Lấy đúng giá trị thập phân thực tế và tin tức trong ngày. | **Agent**   |

---

## 6. Production Readiness Review

Để đưa hệ thống ReAct này vào môi trường thực tế (Production), cần cân nhắc các yếu tố:

- **Security**:
  - Validate (Sanitization) đầu vào của Tool. Hàm `get_stock_price` cần kiểm tra xem `ticker` có chứa ký tự đặc biệt hay mã độc không trước khi truyền vào `yfinance`.
- **Guardrails**:
  - Limit số vòng lặp `max_steps` (hiện tại đang set = 5) để tránh việc Agent rơi vào vòng lặp vô tận đốt sạch tiền API.
  - Sử dụng tham số `temperature = 0` hoặc `0.1` để đảm bảo Agent suy luận logic một cách nhất quán (Deterministic), giảm tính sáng tạo không cần thiết.
- **Scaling**:
  - ReAct cơ bản phù hợp cho bài toán có 3-5 tools. Nếu hệ thống lớn hơn (50+ tools), cần chuyển đổi sang mô hình **LangGraph** (State Machine) hoặc **RAG-based Tool Retrieval** để LLM không bị quá tải context khi đọc description của công cụ.
