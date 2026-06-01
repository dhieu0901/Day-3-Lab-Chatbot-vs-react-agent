const $ = (sel) => document.querySelector(sel);

const input = $("#user-input");
const runBtn = $("#run-btn");
const errorBanner = $("#error-banner");

function setLoading(on) {
  runBtn.disabled = on;
  runBtn.querySelector(".btn-text").classList.toggle("hidden", on);
  runBtn.querySelector(".btn-spinner").classList.toggle("hidden", !on);
}

function showError(msg) {
  errorBanner.textContent = msg;
  errorBanner.classList.remove("hidden");
}

function clearError() {
  errorBanner.classList.add("hidden");
}

function renderTrace(container, steps) {
  container.innerHTML = "";
  if (!steps?.length) {
    container.innerHTML = '<div class="trace-step info"><div class="trace-content">Không có trace</div></div>';
    return;
  }
  for (const step of steps) {
    const el = document.createElement("div");
    el.className = `trace-step ${step.type}`;
    el.innerHTML = `
      <div class="trace-label">${escapeHtml(step.label)}</div>
      <div class="trace-content">${escapeHtml(step.content)}</div>
    `;
    container.appendChild(el);
  }
}

function renderAnswer(el, text) {
  el.classList.remove("empty");
  el.textContent = text;
}

function renderStats(el, data) {
  el.textContent = `${data.latency_ms}ms · ${data.tools_used} tool(s)`;
}

function renderIndicators(container, indicators) {
  container.innerHTML = "";
  if (!indicators?.length) {
    container.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");
  const title = document.createElement("h4");
  title.className = "artifacts-title";
  title.textContent = "Chỉ số kỹ thuật";
  container.appendChild(title);

  const grid = document.createElement("div");
  grid.className = "indicators-grid";

  for (const item of indicators) {
    const trend = (item.trend || "").toLowerCase();
    const trendClass = trend === "bullish" ? "bullish" : trend === "bearish" ? "bearish" : "";
    const card = document.createElement("div");
    card.className = "indicator-card";
    card.innerHTML = `
      <div class="indicator-head">
        <strong>${escapeHtml(item.ticker || "—")}</strong>
        <span class="trend-badge ${trendClass}">${escapeHtml(item.trend || "N/A")}</span>
      </div>
      <div class="indicator-metrics">
        <div><span>SMA 20</span><strong>${formatNum(item.SMA_20)}</strong></div>
        <div><span>SMA 50</span><strong>${formatNum(item.SMA_50)}</strong></div>
        <div><span>RSI 14</span><strong>${formatNum(item.RSI_14)}</strong></div>
      </div>
    `;
    grid.appendChild(card);
  }

  container.appendChild(grid);
}

function renderCharts(container, charts) {
  container.innerHTML = "";
  if (!charts?.length) {
    container.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");
  const title = document.createElement("h4");
  title.className = "artifacts-title";
  title.textContent = "Biểu đồ giá (6 tháng)";
  container.appendChild(title);

  const grid = document.createElement("div");
  grid.className = "charts-grid";

  const cacheBust = Date.now();
  for (const chart of charts) {
    const url = `${chart.url}?t=${cacheBust}`;
    const wrap = document.createElement("div");
    wrap.className = "chart-card";
    wrap.innerHTML = `
      <div class="chart-label">${escapeHtml(chart.ticker)} — Close + SMA 20/50</div>
      <img src="${escapeHtml(url)}" alt="Chart ${escapeHtml(chart.ticker)}" loading="lazy" />
    `;
    grid.appendChild(wrap);
  }

  container.appendChild(grid);
}

function formatNum(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function runDemo() {
  const message = input.value.trim();
  if (!message) {
    showError("Vui lòng nhập câu hỏi.");
    return;
  }

  clearError();
  setLoading(true);

  const chatbotAnswer = $("#chatbot-answer");
  const agentAnswer = $("#agent-answer");
  chatbotAnswer.classList.add("empty");
  agentAnswer.classList.add("empty");
  chatbotAnswer.textContent = "Đang xử lý...";
  agentAnswer.textContent = "Đang xử lý...";
  $("#chatbot-trace").innerHTML = "";
  $("#agent-trace").innerHTML = "";
  renderIndicators($("#agent-indicators"), []);
  renderCharts($("#agent-charts"), []);

  try {
    const res = await fetch("/api/demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    renderTrace($("#chatbot-trace"), data.chatbot.trace);
    renderAnswer(chatbotAnswer, data.chatbot.answer);
    renderStats($("#chatbot-stats"), data.chatbot);

    renderTrace($("#agent-trace"), data.agent.trace);
    renderIndicators($("#agent-indicators"), data.agent.indicators);
    renderCharts($("#agent-charts"), data.agent.charts);
    renderAnswer(agentAnswer, data.agent.answer);
    renderStats($("#agent-stats"), data.agent);
  } catch (err) {
    showError(err.message);
    chatbotAnswer.textContent = "Lỗi";
    agentAnswer.textContent = "Lỗi";
  } finally {
    setLoading(false);
  }
}

runBtn.addEventListener("click", runDemo);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runDemo();
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    input.value = chip.dataset.q;
    input.focus();
  });
});

fetch("/api/health")
  .then((r) => r.json())
  .then((data) => {
    if (!data.has_openai && !data.has_gemini) {
      showError("Chưa cấu hình API key. Thêm OPENAI_API_KEY vào file .env rồi restart server.");
    }
  })
  .catch(() => {});
