# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đoàn Minh Hiếu
- **Student ID**: 2A202600841
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

**Primary Contribution**: `src/tools/visual_tools.py` - Tích hợp khả năng vẽ biểu đồ trực quan (`plot_stock_chart`).

**Files Modified**:
- `src/tools/visual_tools.py` - Viết hàm `plot_stock_chart()` sử dụng `matplotlib` và `yfinance`.
- `test_agent.py` - Tích hợp `VISUAL_TOOLS` vào Agent.

### Code Highlights

```python
def plot_stock_chart(ticker: str) -> str:
    # Lấy dữ liệu 6 tháng
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    
    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    
    # Tạo thư mục và lưu biểu đồ
    os.makedirs("charts", exist_ok=True)
    file_path = f"charts/{ticker.upper()}_chart.png"
    
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], label='Close Price')
    plt.plot(hist.index, hist['SMA_20'], label='SMA 20')
    plt.plot(hist.index, hist['SMA_50'], label='SMA 50')
    plt.savefig(file_path)
    
    return json.dumps({
        "status": "ok",
        "message": f"Chart successfully plotted and saved.",
        "file_path": os.path.abspath(file_path)
    }, indent=2)
```

### Documentation & ReAct Integration
Khi Agent gọi `plot_stock_chart`, hệ thống sẽ generate một bức ảnh PNG vật lý lưu vào ổ cứng, và trả về một đường dẫn tuyệt đối cho Agent thông qua Observation. LLM đọc Observation này và biết rằng ảnh đã được lưu thành công, từ đó nó có thể trích dẫn đường dẫn này trong câu Final Answer để phục vụ hiển thị trên Web UI.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Ban đầu LLM cứ bịa (hallucinate) ra kết quả URL của biểu đồ mà không thực sự chờ gọi tool.
- **Log Source**: `{"error": "HALLUCINATION_ERROR", "content": "Action: plot_stock_chart... Observation: {url: '...'}"}`
- **Diagnosis**: LLM không chịu dừng generate text sau khi tạo lệnh Action, mà tiếp tục "tưởng tượng" ra Observation vì nó đã từng thấy các dữ liệu tương tự trong tập training.
- **Solution**: Hợp tác với Quân để thêm đoạn code chặn `content.find("Observation:")` trong `agent.py`, cắt phăng mọi thứ LLM tự chế và ép nó phải dùng dữ liệu thực từ file PNG.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Chatbot truyền thống chỉ sinh ra text thuần túy. Với ReAct, Agent không chỉ "nghĩ" mà còn thực sự "hành động" bằng cách tạo ra các Artifacts (Tệp biểu đồ ảnh) trong thế giới thực.
2. **Reliability**: Trong các trường hợp cần vẽ biểu đồ real-time, Chatbot bất lực. Tuy nhiên Agent lại tốn rất nhiều thời gian (chạy matplotlib mất thêm 1-2s). Đối với những task không cần biểu đồ, chạy Chatbot lại tốt hơn.
3. **Observation**: Agent nhận thức được file đã được sinh ra thông qua `file_path` trong Observation, tạo cảm giác về "môi trường thực tế" thay vì không gian chữ ảo.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thay vì lưu cục bộ bằng file, ta có thể kết nối với AWS S3, upload ảnh lên và trả về Public URL cho người dùng.
- **Safety**: Xóa các file ảnh cũ sau một khoảng thời gian (cron job) để tránh rác ổ cứng.
- **Performance**: Chuyển việc vẽ biểu đồ sang một Queue Service (như Celery/Redis) để không làm block vòng lặp chính của LLM.
