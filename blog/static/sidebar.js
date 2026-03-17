const toggle = document.getElementById('tag-sidebar-toggle');
const sidebar = document.getElementById('tag-sidebar');
if (toggle && sidebar) {
  const KEY = 'tag-sidebar-state';

  function saveState() {
    const state = {
      open: sidebar.classList.contains('open'),
      details: Array.from(sidebar.querySelectorAll('details')).map(d => d.open)
    };
    sessionStorage.setItem(KEY, JSON.stringify(state));
  }

  // Restore state from previous page
  try {
    const saved = JSON.parse(sessionStorage.getItem(KEY));
    if (saved) {
      if (saved.open) sidebar.classList.add('open');
      const details = sidebar.querySelectorAll('details');
      saved.details.forEach((isOpen, i) => {
        if (details[i]) details[i].open = isOpen;
      });
    }
  } catch (e) {}

  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
    saveState();
  });

  document.addEventListener('click', (e) => {
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
      saveState();
    }
  });

  // Save state when any details toggles
  sidebar.querySelectorAll('details').forEach(d => {
    d.addEventListener('toggle', saveState);
  });

  // Prevent details toggle when clicking a tag link inside a summary
  sidebar.querySelectorAll('summary a').forEach(a => {
    a.addEventListener('click', e => e.stopPropagation());
  });
}
