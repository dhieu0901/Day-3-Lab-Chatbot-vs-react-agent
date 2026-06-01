# Local Web UI

Giao diện split-screen so sánh **Chatbot** vs **ReAct Agent**.

UI nằm trong `public/` — backend Python dùng chung logic với `demo.py` và `src/agent/agent.py`.

## Chạy local

```bash
# Từ thư mục gốc project (đã cấu hình .env)
.venv/bin/python web_server.py

# Mở trình duyệt
# http://localhost:8787
```

## Cấu trúc

```
web/
└── public/          # HTML / CSS / JS (frontend only)
    ├── index.html
    ├── css/style.css
    └── js/app.js

web_server.py        # Python HTTP server + API (ở thư mục gốc)
```

## API

| Endpoint | Mô tả |
|---|---|
| `GET /` | Giao diện web |
| `GET /api/health` | Kiểm tra API key |
| `POST /api/demo` | `{"message": "..."}` → `{chatbot, agent}` |

Backend gọi trực tiếp `finance_tools.py` + `ReActAgent` — cùng code với CLI demo.
