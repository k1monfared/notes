// Markdown editor with toolbar

export function createEditor(container) {
  container.innerHTML = `
    <div class="editor-toolbar">
      <button type="button" data-action="bold" title="Bold">B</button>
      <button type="button" data-action="italic" title="Italic">I</button>
      <button type="button" data-action="heading" title="Heading">H</button>
      <button type="button" data-action="link" title="Link">&#128279;</button>
      <button type="button" data-action="image" title="Insert Image">&#128247;</button>
      <button type="button" data-action="hr" title="Horizontal Rule">&mdash;</button>
    </div>
    <textarea id="editor-textarea" placeholder="Write your post here..."></textarea>
    <div id="editor-images" class="editor-images"></div>
  `;

  const textarea = container.querySelector('#editor-textarea');
  const toolbar = container.querySelector('.editor-toolbar');

  toolbar.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;
    const action = btn.dataset.action;
    if (action === 'image') {
      // Handled externally via onImageRequest callback
      if (editor.onImageRequest) editor.onImageRequest();
      return;
    }
    applyAction(textarea, action);
  });

  const editor = {
    get value() { return textarea.value; },
    set value(v) { textarea.value = v; },
    get element() { return textarea; },
    onImageRequest: null,
    insertAtCursor(text) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const before = textarea.value.slice(0, start);
      const after = textarea.value.slice(end);
      textarea.value = before + text + after;
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
      textarea.focus();
    },
    getCursorPosition() {
      return textarea.selectionStart;
    },
    focus() {
      textarea.focus();
    },
  };

  return editor;
}

function applyAction(textarea, action) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end);
  let replacement, cursorOffset;

  switch (action) {
    case 'bold':
      replacement = `**${selected || 'bold text'}**`;
      cursorOffset = selected ? replacement.length : 2;
      break;
    case 'italic':
      replacement = `*${selected || 'italic text'}*`;
      cursorOffset = selected ? replacement.length : 1;
      break;
    case 'heading':
      replacement = `## ${selected || 'Heading'}`;
      cursorOffset = replacement.length;
      break;
    case 'link':
      if (selected) {
        replacement = `[${selected}](url)`;
        cursorOffset = replacement.length - 4; // cursor on "url"
      } else {
        replacement = '[link text](url)';
        cursorOffset = 1; // cursor on "link text"
      }
      break;
    case 'hr':
      replacement = '\n---\n';
      cursorOffset = replacement.length;
      break;
    default:
      return;
  }

  const before = textarea.value.slice(0, start);
  const after = textarea.value.slice(end);
  textarea.value = before + replacement + after;
  textarea.selectionStart = textarea.selectionEnd = start + cursorOffset;
  textarea.focus();
}
