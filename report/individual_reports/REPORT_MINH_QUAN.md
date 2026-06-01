# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Nguyễn Minh Quân
- **Student ID**: 2A202600821
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

**Primary Contribution**: `src/agent/agent.py` - Core Parser và Logic Vòng lặp ReAct.

**Files Modified**:
- `src/agent/agent.py` - Xây dựng cơ chế bắt (parse) luồng suy luận của mô hình LLM.
- `web_server.py` - Tích hợp log truy vết của Agent vào Web UI.

### Code Highlights

```python
# Lọc bỏ Observation do LLM bị ảo giác (Agent hallucination fix)
obs_index = content.find("Observation:")
if obs_index != -1:
    content = content[:obs_index].strip()

# Trích xuất JSON từ chuỗi phức tạp có bọc Markdown (Regex greedy fix)
json_start = text.find("{", action_start)
action_data = None
json_str = text[json_start:]
for i in range(len(json_str), 0, -1):
    if json_str[i - 1] == "}":
        try:
            action_data = json.loads(json_str[:i])
            break
        except json.JSONDecodeError:
            continue
```

### Documentation & ReAct Integration
Đoạn code trên đóng vai trò như một bộ lọc (Guardrail) bảo vệ toàn bộ kiến trúc ReAct. LLM trả về kết quả thường đi kèm với markdown `` ` ```json ` ``, hoặc JSON lồng ghép, khiến Regex truyền thống bị lỗi. Việc lặp ngược (reverse parsing) giúp bắt chính xác cụm JSON mà không bị trượt dấu ngoặc. Đồng thời việc cắt bỏ chuỗi `Observation:` ngăn chặn LLM trả lời "đi tắt".

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Lỗi nghiêm trọng nhất là mô hình GPT-4o và Gemini liên tục trả về JSON thiếu dấu ngoặc `}` ở cuối.
- **Log Source**: `JSON_PARSER_ERROR`
- **Diagnosis**: Ban đầu sử dụng Regex `.*?` (non-greedy), nếu trong JSON có nested arguments (vd `args: { ticker: "NVDA" }`), regex sẽ bắt dấu `}` đóng đầu tiên, tức là dấu đóng của args, khiến toàn bộ JSON cha bị thiếu ngoặc đóng.
- **Solution**: Từ bỏ Regex và chuyển sang thuật toán tìm ngoặc ngược (reverse loop parse) như đã thể hiện ở trên. Lỗi giảm ngay lập tức về 0%.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: ReAct Agent thực sự biến LLM từ một cái "máy nhại chữ" thành một bộ não có suy tính chiến lược. Mỗi khi đọc được một lỗi từ tool, LLM lại tự ghi vào lịch sử hội thoại (`Thought`) và quyết định "thử lại" cách khác. Chatbot thì chỉ nhả lời khuyên suông.
2. **Reliability**: Khuyết điểm lớn nhất của Agent là tốc độ. Nó phải chạy 4-6 vòng lặp cho một câu hỏi so sánh. Đối với các hệ thống yêu cầu Real-time chat (phản hồi trong 200ms), Agent trở nên bất lợi hơn hẳn.
3. **Observation**: Rất thú vị khi LLM có thể thay đổi thái độ hoàn toàn nếu Observation báo lỗi. Ví dụ: Tool thông báo "No data found for NVDA", LLM sẽ tự nói "Ồ có vẻ không có dữ liệu, để tôi báo cho người dùng biết".

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thay vì sử dụng vòng lặp `while` đơn giản, nên chuyển sang framework như **LangGraph** để biến các Tool thành các Node, dễ dàng định tuyến (routing) phức tạp hơn.
- **Safety**: Nên thiết lập các Filter ở bước Action để kiểm tra nếu tham số đầu vào có khả năng chứa mã độc (Prompt Injection/SQL Injection).
- **Performance**: Nén bộ nhớ ngữ cảnh. Khi vòng lặp quá dài (10 bước), lượng Token tốn kém rất nhiều. Cần cài đặt hàm rút gọn (summarize) bớt Observation của các bước đầu.
