const toggle = document.getElementById('tag-sidebar-toggle');
const sidebar = document.getElementById('tag-sidebar');
if (toggle && sidebar) {
  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
    }
  });
  // Prevent details toggle when clicking a tag link inside a summary
  sidebar.querySelectorAll('summary a').forEach(a => {
    a.addEventListener('click', e => e.stopPropagation());
  });
}
