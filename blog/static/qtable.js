// Collapsible audience/category groups for the reverse-interview question table.
// Groups are folded by default; a click (or Enter/Space) on a group or category
// heading toggles it. A row is visible only when its audience and category are
// both open. Uses the `hidden` attribute, so it degrades to "everything folded"
// without JS.
(function () {
  "use strict";

  function setup(table) {
    var groupRows = Array.prototype.slice.call(table.querySelectorAll("tr.group"));
    var catRows = Array.prototype.slice.call(table.querySelectorAll("tr.cat"));
    var dataRows = Array.prototype.slice.call(table.querySelectorAll("tr.qrow"));

    function isOpen(row) {
      return row.classList.contains("open");
    }

    function render() {
      var openAud = {};
      groupRows.forEach(function (g) {
        openAud[g.dataset.aud] = isOpen(g);
        g.setAttribute("aria-expanded", String(isOpen(g)));
      });

      var openCat = {};
      catRows.forEach(function (c) {
        var audOpen = !!openAud[c.dataset.aud];
        c.hidden = !audOpen;
        openCat[c.dataset.cat] = audOpen && isOpen(c);
        c.setAttribute("aria-expanded", String(openCat[c.dataset.cat]));
      });

      dataRows.forEach(function (r) {
        r.hidden = !(openAud[r.dataset.aud] && openCat[r.dataset.cat]);
      });
    }

    function toggle(row) {
      row.classList.toggle("open");
      render();
    }

    groupRows.concat(catRows).forEach(function (row) {
      var head = row.querySelector("th.toggle");
      if (!head) return;
      head.addEventListener("click", function () { toggle(row); });
      head.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
          e.preventDefault();
          toggle(row);
        }
      });
    });

    render();
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll(".qtable"), setup);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
