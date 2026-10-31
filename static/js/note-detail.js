const page = document.querySelector(".note-detail-shell");
const generateButton = document.querySelector("#generate-detail-material");
const detailMessage = document.querySelector("#detail-message");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

generateButton?.addEventListener("click", async () => {
  generateButton.disabled = true;
  generateButton.textContent = "Gemini is reading your note...";
  detailMessage.textContent = "Generating your takeaways and concept-check question...";
  detailMessage.className = "form-message";
  try {
    const response = await fetch(`/api/notes/${page.dataset.noteId}/generate`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Could not generate study material.");
    }
    window.location.reload();
  } catch (error) {
    detailMessage.textContent = `AI generation failed: ${error.message}`;
    detailMessage.className = "form-message error";
    generateButton.disabled = false;
    generateButton.textContent = "Try AI generation again ✦";
  }
});
