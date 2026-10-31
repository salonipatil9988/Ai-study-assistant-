const pyqForm = document.querySelector("#pyq-form");
const pyqMessage = document.querySelector("#pyq-message");
const analyzeButton = document.querySelector("#analyze-button");
const analysisPanel = document.querySelector("#analysis-panel");
const historyFeed = document.querySelector("#history-feed");
const historyCount = document.querySelector("#history-count");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
document.querySelector("#refresh-history").addEventListener("click", loadHistory);

function renderTopics(topics) {
  const container = document.querySelector("#repeated-topics");
  container.replaceChildren();
  if (!topics || !topics.length) {
    const empty = document.createElement("p");
    empty.className = "result-copy";
    empty.textContent = "No repeated topics identified.";
    container.append(empty);
    return;
  }
  topics.forEach((topic) => {
    const card = document.createElement("article");
    card.className = "topic-card";
    const heading = document.createElement("div");
    heading.className = "topic-card-heading";
    const title = document.createElement("h3");
    title.textContent = topic.topic;
    const priority = document.createElement("span");
    priority.className = `priority-chip ${String(topic.priority || "Practice").toLowerCase()}`;
    priority.textContent = `${topic.priority || "Practice"} priority`;
    heading.append(title, priority);
    const evidence = document.createElement("p");
    const references = topic.question_ids?.length ? ` · Evidence: ${topic.question_ids.map((id) => `Q${id}`).join(", ")}` : "";
    evidence.textContent = `${topic.question_count || 0} question(s) cited${topic.years?.length ? ` · ${topic.years.join(", ")}` : " · no year labels provided"}${references}`;
    const rationale = document.createElement("p");
    rationale.textContent = topic.rationale || "";
    card.append(heading, evidence, rationale);
    container.append(card);
  });
}

function renderPracticeQuestions(questions) {
  const container = document.querySelector("#practice-questions");
  container.replaceChildren();
  if (!questions || !questions.length) {
    const empty = document.createElement("p");
    empty.className = "result-copy";
    empty.textContent = "No practice questions were returned. Try adding year-tagged questions.";
    container.append(empty);
    return;
  }
  questions.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "practice-card";
    const heading = document.createElement("h3");
    heading.textContent = `${index + 1}. ${item.question}`;
    const detail = document.createElement("p");
    detail.textContent = [item.topic, `${item.priority || "Practice"} priority`, item.rationale].filter(Boolean).join(" · ");
    card.append(heading, detail);
    container.append(card);
  });
}

function displayStudyGuide(data) {
  renderTopics(data.topics || []);
  renderPracticeQuestions(data.practice_questions || []);
  document.querySelector("#trend-summary").textContent = data.trend_summary || "";
  document.querySelector("#exam-strategy").textContent = data.exam_strategy || "";
  document.querySelector("#analysis-confidence").textContent = data.confidence_note || "Priority reflects the supplied PYQs; it is not a prediction guarantee.";
  
  const metrics = document.querySelector("#analysis-metrics");
  metrics.replaceChildren();
  [
    `${data.question_count || 0} question${data.question_count === 1 ? "" : "s"} reviewed`,
    data.exam_name || "Exam not specified",
    data.year_range || "Years not specified",
  ].forEach((label) => {
    const badge = document.createElement("span");
    badge.className = "metric-chip";
    badge.textContent = label;
    metrics.append(badge);
  });

  analysisPanel.hidden = false;
  analysisPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

pyqForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  analyzeButton.disabled = true;
  analyzeButton.innerHTML = "<span>Finding patterns...</span><span aria-hidden=\"true\">✦</span>";
  pyqMessage.textContent = "";
  analysisPanel.hidden = true;

  try {
    const formData = new FormData(pyqForm);
    const response = await fetch("/api/pyq/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({
        subject: String(formData.get("subject") || ""),
        exam_name: String(formData.get("exam_name") || ""),
        academic_level: String(formData.get("academic_level") || ""),
        year_range: String(formData.get("year_range") || ""),
        pyqs: String(formData.get("pyqs") || ""),
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "We couldn't analyze those questions. Please try again.");
    }
    
    displayStudyGuide(result);
    pyqMessage.textContent = "Analysis complete. Your study guide is ready below!";
    pyqMessage.className = "form-message success";
    await loadHistory();
  } catch (error) {
    pyqMessage.textContent = error.message;
    pyqMessage.className = "form-message error";
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.innerHTML = "<span>Analyze questions</span><span aria-hidden=\"true\">✦</span>";
  }
});

async function loadHistory() {
  historyFeed.innerHTML = '<div class="loading-state">Loading your saved analyses...</div>';
  try {
    const response = await fetch("/api/pyq/history");
    const items = await response.json();
    if (!response.ok) throw new Error(items.error || "Could not load your analysis history.");
    historyCount.textContent = items.length;
    if (!items.length) {
      historyFeed.innerHTML = '<div class="empty-state"><span class="empty-icon">◎</span><h3>Your analysis history will appear here.</h3><p>Analyze a set of questions to save your first study guide.</p></div>';
      return;
    }
    historyFeed.replaceChildren(...items.map(renderHistoryItem));
  } catch (error) {
    historyFeed.replaceChildren();
    const message = document.createElement("p");
    message.className = "error-state";
    message.textContent = error.message;
    historyFeed.append(message);
  }
}

function renderHistoryItem(item) {
  const article = document.createElement("article");
  article.className = "history-card";
  const heading = document.createElement("div");
  heading.className = "history-card-heading";
  const title = document.createElement("h3");
  title.textContent = item.subject_name;
  const date = document.createElement("time");
  date.textContent = item.created_at ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(item.created_at)) : "Just now";
  heading.append(title, date);
  const topics = document.createElement("p");
  topics.className = "history-topics";
  topics.textContent = item.repeated_topics;
  const actions = document.createElement("div");
  actions.className = "history-actions";
  const view = document.createElement("button");
  view.className = "button button-outline";
  view.type = "button";
  view.textContent = "View study guide";
  view.addEventListener("click", () => {
    displayStudyGuide(item);
  });
  const remove = document.createElement("button");
  remove.className = "button button-quiet danger-button";
  remove.type = "button";
  remove.textContent = "Delete";
  remove.addEventListener("click", () => deleteHistory(item.id, remove));
  actions.append(view, remove);
  article.append(heading, topics, actions);
  return article;
}

async function deleteHistory(id, button) {
  if (!window.confirm("Delete this saved PYQ analysis?")) return;
  button.disabled = true;
  try {
    const response = await fetch(`/api/pyq/history/${id}`, {
      method: "DELETE",
      headers: { "X-CSRFToken": csrfToken },
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not delete the analysis.");
    await loadHistory();
  } catch (error) {
    window.alert(error.message);
    button.disabled = false;
  }
}

loadHistory();
