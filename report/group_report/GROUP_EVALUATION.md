# Phase 5: Group Evaluation - Chatbot vs ReAct Agent

## 1. Bảng đánh giá số liệu (Metrics Table)

Dựa trên quá trình phân tích `logs/2026-06-01.log` và chạy thử nghiệm thực tế với Model `gpt-4o`, dưới đây là bảng so sánh hiệu suất giữa Baseline Chatbot và ReAct Agent.

| Metric | Baseline Chatbot (Without Tools) | ReAct Agent (With Finance Tools) | 
| :--- | :--- | :--- | 
| **Tổng số bước (Steps)** | 1 (Trả lời trực tiếp) | 3 (1. Lấy Giá -> 2. Lấy Tin tức -> 3. Final Answer) |
| **Độ trễ trung bình (Latency)** | ~8 giây | ~15 - 20 giây (Bao gồm thời gian gọi 2 API `yfinance`) |
| **Chi phí Token (Efficiency)** | Thấp (~600 tokens/lần) | Cao hơn (~1500 tokens/lần do lặp lại prompt nhiều vòng) |
| **Tính chính xác dữ liệu (Accuracy)** | Kém. Không có khả năng truy cập thời gian thực. Đưa ra lời khuyên chung chung. | Xuất sắc. Giá trị thực được lấy đúng tới 2 chữ số thập phân, tin tức được cập nhật đúng ngày hôm nay. |
| **Tỷ lệ lỗi Format (JSON Error)** | 0% | Phase 3: Cao. Phase 4 (v2 Prompt): 0% |
| **Tình trạng Ảo giác (Hallucination)** | Có rủi ro bịa đặt giá cũ từ dữ liệu quá khứ. | Không, LLM chỉ dựa trên thông tin "Observation" do Tool trả về để kết luận. |

---

## 2. Thảo luận (Discussion)

### 2.1 Tại sao ReAct Agent lại chiếm ưu thế tuyệt đối trong các bài toán nhiều bước (Multi-step scenarios)?
Agent giành chiến thắng vì nó được trao khả năng **hành động (Action)** và **quan sát (Observation)** thay vì chỉ đoán bừa.
Trong bài toán phân tích và so sánh chứng khoán (như so sánh Apple và Nvidia), mô hình ReAct đã:
- Cắt nhỏ vấn đề (Check AAPL trước, check NVDA sau).
- Gọi các công cụ bên ngoài (Tools) như `get_stock_price` hay `get_stock_news` để lấp đầy những khoảng trống về kiến thức thời gian thực (Real-time gap).
- Sau khi có đủ dữ kiện thực tế, Agent tự động tổng hợp để đưa ra "Final Answer" với độ tin cậy đạt mức tối đa.

### 2.2 Khi nào thì Baseline Chatbot vẫn là lựa chọn tốt (Simple Q&A)?
Chatbot truyền thống giành chiến thắng trong những tình huống **hỏi đáp kiến thức cơ bản (Q&A)** hoặc cần **phản hồi tức thì** như:
- *"Trí tuệ nhân tạo là gì?"*
- *"Tóm tắt cho tôi cuốn sách Đắc Nhân Tâm trong 3 câu."*
- *"Dịch văn bản sau sang tiếng Anh."*

**Lý do:**
1. **Tốc độ (Latency)**: Chatbot trả lời ngay lập tức (1 step) mà không cần mất thời gian phân tích suy nghĩ hay gọi tool bên ngoài.
2. **Chi phí (Cost)**: ReAct Agent tiêu thụ rất nhiều token vì nó phải gửi đi gửi lại bộ System Prompt chứa toàn bộ công cụ, cộng thêm phần "Thought / Action / Observation" của các bước trước đó. Trong các tác vụ đơn giản, việc dùng ReAct là lãng phí tài nguyên và chi phí không cần thiết.

---
**Kết luận của nhóm:**
Trong bối cảnh xây dựng một trợ lý tài chính thông minh, độ chính xác của dữ liệu là yếu tố sống còn. Do đó, mặc dù ReAct Agent tốn nhiều chi phí Token và thời gian phản hồi (Latency) cao hơn, đây vẫn là một sự đánh đổi hoàn toàn xứng đáng. Bằng chứng là thông qua "Failure Analysis" ở Phase 4, chúng tôi đã khắc phục triệt để lỗi Parser bằng Prompt V2, giúp Agent hoạt động cực kỳ ổn định.
