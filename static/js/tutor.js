const threadList = document.querySelector("#thread-list");
const messagesPanel = document.querySelector("#chat-messages");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatTitle = document.querySelector("#chat-title");
const chatStatus = document.querySelector("#chat-status");
const sendButton = document.querySelector("#send-chat");
const newChatButton = document.querySelector("#new-chat");
const threadDeleteButton = document.querySelector("#delete-chat");
const contextPicker = document.querySelector("#note-context");
const welcome = document.querySelector("#chat-welcome");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

let activeThread = null;
let threadCache = [];

newChatButton.addEventListener("click", createNewThread);
document.querySelector("#refresh-chats").addEventListener("click", loadThreads);
threadDeleteButton.addEventListener("click", deleteActiveThread);
chatForm.addEventListener("submit", sendMessage);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => {
    chatInput.value = button.textContent;
    chatInput.focus();
  });
});

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.method && options.method !== "GET" ? { "X-CSRFToken": csrfToken } : {}),
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}

async function loadNoteOptions() {
  try {
    const notes = await requestJson("/api/notes");
    contextPicker.replaceChildren();
    notes.forEach((note) => {
      const option = document.createElement("option");
      option.value = note.id;
      option.textContent = `${note.subject ? `${note.subject} · ` : ""}${note.title}`;
      contextPicker.append(option);
    });
    const noteId = Number(new URLSearchParams(window.location.search).get("note_id"));
    if (Number.isInteger(noteId) && noteId > 0) {
      const option = [...contextPicker.options].find((item) => Number(item.value) === noteId);
      if (option) option.selected = true;
    }
  } catch (error) {
    setStatus(error.message);
  }
}

async function loadThreads() {
  threadList.replaceChildren();
  try {
    threadCache = await requestJson("/api/chat/threads");
    if (!threadCache.length) {
      const empty = document.createElement("p");
      empty.className = "thread-empty";
      empty.textContent = "Your conversations will appear here.";
      threadList.append(empty);
      if (!activeThread) await createNewThread();
      return;
    }
    threadCache.forEach((thread) => threadList.append(renderThreadLink(thread)));
    if (activeThread) {
      const refreshed = threadCache.find((thread) => thread.id === activeThread.id);
      if (refreshed) activeThread = refreshed;
    }
  } catch (error) {
    setStatus(error.message);
  }
}

function renderThreadLink(thread) {
  const row = document.createElement("div");
  row.className = `thread-row${activeThread?.id === thread.id ? " active" : ""}`;
  const button = document.createElement("button");
  button.className = "thread-link";
  button.type = "button";
  button.textContent = thread.title;
  button.addEventListener("click", () => openThread(thread.id));
  row.append(button);
  return row;
}

async function createNewThread() {
  newChatButton.disabled = true;
  try {
    const noteIds = [...contextPicker.selectedOptions].map((option) => Number(option.value));
    const thread = await requestJson("/api/chat/threads", {
      method: "POST",
      body: JSON.stringify({ note_ids: noteIds }),
    });
    activeThread = thread;
    await renderThread(thread, []);
    await loadThreads();
    chatInput.focus();
  } catch (error) {
    setStatus(error.message);
  } finally {
    newChatButton.disabled = false;
  }
}

async function openThread(id) {
  try {
    const thread = await requestJson(`/api/chat/threads/${id}`);
    activeThread = thread;
    contextPicker.selectedIndex = -1;
    (thread.context_note_ids || []).forEach((noteId) => {
      const option = [...contextPicker.options].find((item) => Number(item.value) === noteId);
      if (option) option.selected = true;
    });
    await renderThread(thread, thread.messages || []);
    await loadThreads();
  } catch (error) {
    setStatus(error.message);
  }
}

async function renderThread(thread, messages) {
  activeThread = thread;
  chatTitle.textContent = thread.title || "New study session";
  threadDeleteButton.hidden = !thread.id;
  messagesPanel.replaceChildren();
  if (!messages.length) {
    welcome.hidden = false;
    messagesPanel.append(welcome);
  } else {
    welcome.hidden = true;
    messages.forEach((message) => messagesPanel.append(renderMessage(message)));
  }
  messagesPanel.scrollTop = messagesPanel.scrollHeight;
  chatInput.disabled = false;
  sendButton.disabled = false;
}

function renderMessage(message) {
  const article = document.createElement("article");
  article.className = `chat-message ${message.role === "assistant" ? "assistant-message" : "user-message"}`;
  const role = document.createElement("span");
  role.className = "message-role";
  role.textContent = message.role === "assistant" ? "AI STUDY TUTOR" : "YOU";
  const body = document.createElement("p");
  body.className = "message-content";
  body.textContent = message.content;
  article.append(role, body);
  if (message.role === "assistant" && message.sources?.length) {
    const sources = document.createElement("div");
    sources.className = "message-sources";
    const label = document.createElement("span");
    label.textContent = "STUDY CONTEXT";
    sources.append(label);
    message.sources.forEach((source) => {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.textContent = `${source.label}: ${source.title || source.subject}`;
      sources.append(chip);
    });
    article.append(sources);
  }
  return article;
}

async function sendMessage(event) {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  if (!activeThread?.id) {
    await createNewThread();
    if (!activeThread?.id) return;
  }

  const draft = renderMessage({ role: "user", content: message });
  chatInput.value = "";
  chatInput.disabled = true;
  sendButton.disabled = true;
  welcome.hidden = true;
  if (messagesPanel.contains(welcome)) welcome.remove();
  messagesPanel.append(draft);

  const thinking = document.createElement("div");
  thinking.className = "thinking-indicator";
  thinking.textContent = "Tutor is looking at your study context...";
  messagesPanel.append(thinking);
  messagesPanel.scrollTop = messagesPanel.scrollHeight;
  setStatus("Searching your notes and PYQ history...");
  try {
    const result = await requestJson(`/api/chat/threads/${activeThread.id}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    thinking.remove();
    messagesPanel.append(renderMessage(result.assistant_message));
    activeThread = result.thread;
    chatTitle.textContent = activeThread.title;
    setStatus("Your conversation is saved privately.");
    await loadThreads();
  } catch (error) {
    thinking.remove();
    draft.remove();
    if (messagesPanel.childElementCount === 0) {
      welcome.hidden = false;
      messagesPanel.append(welcome);
    }
    const failure = document.createElement("p");
    failure.className = "error-state";
    failure.textContent = error.message;
    messagesPanel.append(failure);
    chatInput.value = message;
    setStatus("Your message was not saved. You can try again.");
  } finally {
    chatInput.disabled = false;
    sendButton.disabled = false;
    chatInput.focus();
    messagesPanel.scrollTop = messagesPanel.scrollHeight;
  }
}

async function deleteActiveThread() {
  if (!activeThread?.id || !window.confirm("Delete this conversation and all its messages?")) return;
  threadDeleteButton.disabled = true;
  try {
    await requestJson(`/api/chat/threads/${activeThread.id}`, { method: "DELETE" });
    activeThread = null;
    await loadThreads();
  } catch (error) {
    setStatus(error.message);
  } finally {
    threadDeleteButton.disabled = false;
  }
}

function setStatus(message) {
  chatStatus.textContent = message;
}

async function initialize() {
  await loadNoteOptions();
  await loadThreads();
  const initialNote = Number(new URLSearchParams(window.location.search).get("note_id"));
  if (initialNote && threadCache.length && !activeThread?.messages?.length) {
    const newThread = threadCache.find((thread) => thread.id === activeThread?.id);
    if (newThread) await openThread(newThread.id);
  }
}

initialize();
