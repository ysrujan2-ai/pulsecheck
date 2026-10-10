
const checkForm = document.getElementById("checkForm");
const websiteUrl = document.getElementById("websiteUrl");
const checkBtn = document.getElementById("checkBtn");
const result = document.getElementById("result");
const refreshBtn = document.getElementById("refreshBtn");


function drawResponseChart(records) {
    const canvas = document.getElementById("responseChart");
    const summary = document.getElementById("chartSummary");

    if (!canvas || !summary) return;

    const ctx = canvas.getContext("2d");

    // Keep only records with valid response times.
    // Reverse the newest-first history into chronological order.
    const data = records
        .filter(record =>
            typeof record.response_time_ms === "number" &&
            Number.isFinite(record.response_time_ms)
        )
        .slice(0, 20)
        .reverse();

    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    if (data.length === 0) {
        summary.textContent = "No response-time data available yet.";
        ctx.fillStyle = "#64748b";
        ctx.font = "14px Segoe UI, Arial";
        ctx.fillText("Run a website check to populate the chart.", 12, 30);
        return;
    }

    const padding = { top: 20, right: 20, bottom: 40, left: 58 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    if (plotWidth <= 0 || plotHeight <= 0) return;

    const maxTime = Math.max(
        100,
        ...data.map(record => record.response_time_ms)
    );
    const yMax = Math.ceil(maxTime / 100) * 100;

    const x = index => data.length === 1
        ? padding.left + plotWidth / 2
        : padding.left + (index / (data.length - 1)) * plotWidth;

    const y = value =>
        padding.top + plotHeight - (value / yMax) * plotHeight;

    // Horizontal grid and Y-axis labels.
    ctx.font = "11px Segoe UI, Arial";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let i = 0; i <= 4; i++) {
        const value = (yMax / 4) * i;
        const py = y(value);

        ctx.beginPath();
        ctx.strokeStyle = "#e2e8f0";
        ctx.lineWidth = 1;
        ctx.moveTo(padding.left, py);
        ctx.lineTo(width - padding.right, py);
        ctx.stroke();

        ctx.fillStyle = "#64748b";
        ctx.fillText(`${Math.round(value)} ms`, padding.left - 8, py);
    }

    // Response-time line.
    ctx.beginPath();
    data.forEach((record, index) => {
        const px = x(index);
        const py = y(record.response_time_ms);

        if (index === 0) {
            ctx.moveTo(px, py);
        } else {
            ctx.lineTo(px, py);
        }
    });

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Data points.
    data.forEach((record, index) => {
        const px = x(index);
        const py = y(record.response_time_ms);

        ctx.beginPath();
        ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#2563eb";
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
    });

    // X-axis labels.
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    const labelCount = Math.min(data.length, 5);

    for (let i = 0; i < labelCount; i++) {
        const index = labelCount === 1
            ? 0
            : Math.round(i * (data.length - 1) / (labelCount - 1));

        ctx.fillText(
            `#${index + 1}`,
            x(index),
            height - padding.bottom + 12
        );
    }

    const average = data.reduce(
        (sum, record) => sum + record.response_time_ms, 0
    ) / data.length;

    const fastest = Math.min(
        ...data.map(record => record.response_time_ms)
    );

    summary.textContent =
        `${data.length} checks plotted · ` +
        `Average: ${average.toFixed(2)} ms · ` +
        `Fastest: ${fastest.toFixed(2)} ms`;
}



async function loadHistory() {
    const historyBody = document.getElementById("historyBody");
    const historyCount = document.getElementById("historyCount");

    try {
        const response = await fetch("/history");

        if (!response.ok) {
            throw new Error("Could not load check history.");
        }

        const records = await response.json();
        drawResponseChart(records);

        const successful = records.filter(
            record => record.status_code >= 200 &&
                record.status_code < 300
        ).length;

        const failed = records.length - successful;

        const validTimes = records
            .map(record => record.response_time_ms)
            .filter(value => typeof value === "number");

        const average = validTimes.length
            ? validTimes.reduce((sum, value) => sum + value, 0)
            / validTimes.length
            : null;

        document.getElementById("totalChecks").textContent =
            records.length;

        document.getElementById("successfulChecks").textContent =
            successful;

        document.getElementById("failedChecks").textContent =
            failed;

        document.getElementById("averageResponse").textContent =
            average === null ? "—" : `${average.toFixed(0)} ms`;

        historyCount.textContent =
            `${records.length} record${records.length === 1 ? "" : "s"}`;

        historyBody.replaceChildren();

        if (records.length === 0) {
            const row = historyBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 4;
            cell.className = "empty-state";
            cell.textContent = "No checks recorded yet.";
            return;
        }

        records.forEach(record => {
            const row = historyBody.insertRow();

            const urlCell = row.insertCell();
            const link = document.createElement("a");
            link.href = record.url;
            link.textContent = record.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            urlCell.appendChild(link);

            const statusCell = row.insertCell();
            const badge = document.createElement("span");
            const isUp = record.is_up === true || record.is_up === 1;

            badge.className = `status ${isUp ? "status-up" : "status-down"
                }`;

            badge.textContent = isUp
                ? `UP (${record.status_code ?? "OK"})`
                : "DOWN";

            statusCell.appendChild(badge);

            row.insertCell().textContent =
                typeof record.response_time_ms === "number"
                    ? `${record.response_time_ms.toFixed(2)} ms`
                    : "—";

            row.insertCell().textContent = record.checked_at
                ? new Date(record.checked_at).toLocaleString()
                : "—";
        });
    } catch (error) {
        historyBody.replaceChildren();

        const row = historyBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 4;
        cell.className = "empty-state error";
        cell.textContent = error.message;

        historyCount.textContent = "History unavailable";
    }
}

checkForm.addEventListener("submit", async event => {
    event.preventDefault();

    const url = websiteUrl.value.trim();

    checkBtn.disabled = true;
    checkBtn.textContent = "Checking...";
    result.replaceChildren();

    const loading = document.createElement("p");
    loading.textContent = "Checking website availability...";
    result.appendChild(loading);

    try {
        const response = await fetch(
            `/check?url=${encodeURIComponent(url)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Website check failed.");
        }

        const box = document.createElement("div");
        box.className = `result-box ${data.is_up ? "result-up" : "result-down"
            }`;

        const heading = document.createElement("h3");
        heading.textContent = data.is_up
            ? "✓ Website is reachable"
            : "✕ Website check unsuccessful";

        const details = document.createElement("p");
        details.textContent =
            `URL: ${data.url} | HTTP: ${data.status_code} | ` +
            `Response time: ${data.response_time_ms} ms`;

        box.append(heading, details);
        result.replaceChildren(box);

        await loadHistory();
    } catch (error) {
        const message = document.createElement("p");
        message.className = "error";
        message.textContent = error.message;
        result.replaceChildren(message);

        await loadHistory();
    } finally {
        checkBtn.disabled = false;
        checkBtn.textContent = "Check Website →";
    }
});

refreshBtn.addEventListener("click", loadHistory);

loadHistory();

window.addEventListener("resize", () => {
    loadHistory();
});
