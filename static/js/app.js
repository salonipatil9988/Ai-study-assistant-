const noteForm = document.querySelector("#note-form");
const noteFeed = document.querySelector("#notes-feed");
const noteMessage = document.querySelector("#note-message");
const noteCount = document.querySelector("#note-count");
const aiMaterialCount = document.querySelector("#ai-material-count");
const refreshButton = document.querySelector("#refresh-notes");
const searchInput = document.querySelector("#note-search");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
const aiMaterialFeed = document.querySelector("#ai-material-feed");
const notesTab = document.querySelector("#notes-tab");
const aiSpaceTab = document.querySelector("#ai-space-tab");
const notesWorkspace = document.querySelector("#notes-workspace");
const aiWorkspace = document.querySelector("#ai-workspace");

let searchTimer;

notesTab.addEventListener("click", () => selectWorkspace("notes"));
aiSpaceTab.addEventListener("click", () => selectWorkspace("ai"));

function selectWorkspace(workspace) {
  const showNotes = workspace === "notes";
  notesWorkspace.hidden = !showNotes;
  aiWorkspace.hidden = showNotes;
  notesTab.classList.toggle("active", showNotes);
  notesTab.setAttribute("aria-selected", String(showNotes));
  aiSpaceTab.classList.toggle("active", !showNotes);
  aiSpaceTab.setAttribute("aria-selected", String(!showNotes));
}

noteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = noteForm.querySelector('button[type="submit"]');
  setBusy(submitButton, true, "Saving...");
  noteMessage.textContent = "";

  try {
    const formData = new FormData(noteForm);
    const savedNote = await requestJson("/api/notes", {
      method: "POST",
      body: JSON.stringify({
        title: String(formData.get("title") || ""),
        subject: String(formData.get("subject") || ""),
        content: String(formData.get("content") || ""),
      }),
    });
    noteForm.reset();
    searchInput.value = "";
    noteMessage.textContent = "Note saved. Ready when you are!";
    noteMessage.className = "form-message success";
    await loadNotes(savedNote);
  } catch (error) {
    showMessage(noteMessage, error.message);
  } finally {
    setBusy(submitButton, false, "Save note");
  }
});

refreshButton.addEventListener("click", () => loadNotes());
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadNotes, 250);
});

async function loadNotes(recentlySavedNote = null) {
  if (!noteFeed.childElementCount) {
    noteFeed.innerHTML = '<div class="loading-state">Loading your notes...</div>';
  }
  try {
    const searchTerm = searchInput?.value?.trim() || "";
    const notes = await requestJson(`/api/notes?q=${encodeURIComponent(searchTerm)}`);
    const savedNoteMissing = recentlySavedNote?.id != null
      && !notes.some((note) => note.id === recentlySavedNote.id);
    if (savedNoteMissing) {
      notes.unshift(recentlySavedNote);
      noteMessage.textContent = "Note was saved, but your library did not return it. Showing it here temporarily; check that you are signed into the same account.";
      noteMessage.className = "form-message error";
    }
    noteCount.textContent = notes.length;
    const materialNotes = notes.filter((note) => note.ai_summary || note.ai_confuser);
    aiMaterialCount.textContent = materialNotes.length;
    renderAiStudySpace(materialNotes);
    if (notes.length === 0) {
      noteFeed.innerHTML = '<div class="empty-state"><span class="empty-icon">✎</span><h3>Your next great idea starts here.</h3><p>Save a note above and it’ll show up in your library.</p></div>';
      return;
    }
    noteFeed.replaceChildren(...notes.map(renderNote));
  } catch (error) {
    noteCount.textContent = "–";
    const message = document.createElement("p");
    message.className = "error-state library-load-error";
    message.textContent = error.message;
    if (recentlySavedNote) {
      noteFeed.replaceChildren(renderNote(recentlySavedNote), message);
      noteMessage.textContent = `Note was saved, but the library could not refresh: ${error.message}`;
      noteMessage.className = "form-message error";
    } else {
      noteFeed.querySelector(".library-load-error")?.remove();
      noteFeed.append(message);
    }
  }
}

function renderNote(note) {
  const article = document.createElement("article");
  article.className = "note-card";

  const cardHeader = document.createElement("div");
  cardHeader.className = "note-card-header";
  const heading = document.createElement("h3");
  heading.textContent = note.title;
  const date = document.createElement("time");
  date.className = "note-date";
  date.dateTime = note.created_at || "";
  date.textContent = formatDate(note.created_at);
  cardHeader.append(heading, date);

  const content = document.createElement("p");
  content.className = "note-content";
  content.textContent = note.content;
  const subject = document.createElement("p");
  subject.className = "note-subject";
  subject.textContent = note.subject || "General";
  article.append(cardHeader, subject, content);

  if (note.ai_summary || note.ai_confuser) {
    const results = document.createElement("div");
    results.className = "note-results";
    if (note.ai_summary) {
      results.append(createResultBlock("3 key takeaways", note.ai_summary, "purple"));
    }
    if (note.ai_confuser) {
      results.append(createResultBlock("Try this tricky question", note.ai_confuser, "coral"));
    }
    article.append(results);
  }

  const actions = document.createElement("div");
  actions.className = "note-actions";
  const view = document.createElement("a");
  view.className = "button button-quiet";
  view.href = `/notes/${note.id}`;
  view.textContent = "Open full note";
  const edit = document.createElement("button");
  edit.className = "button button-quiet";
  edit.type = "button";
  edit.textContent = "Edit";
  edit.addEventListener("click", () => editNote(note));
  const remove = document.createElement("button");
  remove.className = "button button-quiet danger-button";
  remove.type = "button";
  remove.textContent = "Delete";
  remove.addEventListener("click", () => deleteNote(note.id, remove));
  const generate = document.createElement("button");
  generate.className = "button button-outline";
  generate.type = "button";
  generate.textContent = note.ai_summary || note.ai_confuser ? "Regenerate AI material ✦" : "Generate AI study material";
  generate.addEventListener("click", () => generateMaterial(note.id, generate));
  actions.append(view, edit, remove, generate);
  const actionMessage = document.createElement("p");
  actionMessage.className = "note-action-message";
  actionMessage.setAttribute("role", "status");
  article.append(actions, actionMessage);
  return article;
}

function createResultBlock(title, text, tone) {
  const block = document.createElement("section");
  block.className = `note-result ${tone}`;
  const heading = document.createElement("h4");
  heading.textContent = title;
  const body = document.createElement("p");
  body.textContent = text;
  block.append(heading, body);
  return block;
}

async function generateMaterial(id, button) {
  setBusy(button, true, "Thinking...");
  const actionMessage = button.closest(".note-card").querySelector(".note-action-message");
  actionMessage.textContent = "Gemini is reading your note and preparing your study material...";
  actionMessage.className = "note-action-message";
  try {
    await requestJson(`/api/notes/${id}/generate`, { method: "POST" });
    noteMessage.textContent = "AI study material generated and saved. It’s available in the AI study space.";
    noteMessage.className = "form-message success";
    await loadNotes();
    selectWorkspace("ai");
  } catch (error) {
    actionMessage.textContent = `AI generation failed: ${error.message}`;
    actionMessage.className = "note-action-message error";
  } finally {
    button.disabled = false;
    button.textContent = button.dataset.defaultLabel || "Generate AI study material";
  }
}

async function editNote(note) {
  const title = window.prompt("Update the note title:", note.title);
  if (title === null) return;
  const content = window.prompt("Update the note content:", note.content);
  if (content === null) return;
  const subject = window.prompt("Update the subject (optional):", note.subject || "");
  if (subject === null) return;
  try {
    await requestJson(`/api/notes/${note.id}`, {
      method: "PUT",
      body: JSON.stringify({ title, content, subject }),
    });
    await loadNotes();
  } catch (error) {
    window.alert(error.message);
  }
}

function renderAiStudySpace(notes) {
  if (!notes.length) {
    aiMaterialFeed.innerHTML = '<div class="empty-state"><span class="empty-icon">✦</span><h3>Your AI study material will live here.</h3><p>Open a note and choose “Generate AI study material” to create takeaways and a concept-check question.</p></div>';
    return;
  }
  aiMaterialFeed.replaceChildren(...notes.map(renderAiMaterial));
}

function renderAiMaterial(note) {
  const article = document.createElement("article");
  article.className = "ai-material-card";
  const heading = document.createElement("div");
  heading.className = "ai-material-heading";
  const titleGroup = document.createElement("div");
  const subject = document.createElement("p");
  subject.className = "note-subject";
  subject.textContent = note.subject || "General";
  const title = document.createElement("h3");
  title.textContent = note.title;
  titleGroup.append(subject, title);
  const link = document.createElement("a");
  link.className = "button button-quiet";
  link.href = `/notes/${note.id}`;
  link.textContent = "Open source note";
  heading.append(titleGroup, link);

  const sections = document.createElement("div");
  sections.className = "ai-material-sections";
  if (note.ai_summary) {
    sections.append(createResultBlock("AI Teacher · Key takeaways", note.ai_summary, "purple"));
  }
  if (note.ai_confuser) {
    sections.append(createResultBlock("AI Confuser · Test yourself", note.ai_confuser, "coral"));
  }
  const actions = document.createElement("div");
  actions.className = "ai-material-actions";
  const tutor = document.createElement("a");
  tutor.className = "button button-primary";
  tutor.href = `/tutor?note_id=${note.id}`;
  tutor.textContent = "Ask AI teacher about this ✦";
  const pdf = document.createElement("a");
  pdf.className = "button button-outline";
  pdf.href = `/api/notes/${note.id}/study-material.pdf`;
  pdf.textContent = "Download study PDF ↓";
  actions.append(tutor, pdf);
  article.append(heading, sections, actions);
  return article;
}

async function deleteNote(id, button) {
  if (!window.confirm("Delete this note and its generated study material?")) return;
  button.disabled = true;
  try {
    await requestJson(`/api/notes/${id}`, { method: "DELETE" });
    await loadNotes();
  } catch (error) {
    window.alert(error.message);
    button.disabled = false;
  }
}

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
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  if (busy) {
    button.dataset.defaultLabel = button.textContent;
    button.textContent = label;
  } else {
    button.textContent = button.dataset.defaultLabel || label;
  }
}

function showMessage(element, message) {
  element.textContent = message;
  element.className = "form-message error";
}

function formatDate(value) {
  if (!value) return "Just now";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Just now"
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

loadNotes();
