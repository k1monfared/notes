/* Static hybrid search UI.
 *
 * Two retrieval arms:
 *   - keyword (BM25-ish) via MiniSearch, built in the browser from docs.json
 *   - semantic via int8 document vectors (vectors.bin) and a query embedding
 *     computed in the browser with Transformers.js (the same model the build
 *     used), fused with keyword results by Reciprocal Rank Fusion.
 *
 * No server: every asset is static, queries never leave the page. The semantic
 * arm is opt-in because its model is large; keyword search works with zero
 * download.
 */
(function () {
  "use strict";

  var DOCS_URL = new URL("search/docs.json", document.baseURI);
  var MANIFEST_URL = new URL("search/manifest.json", document.baseURI);
  var VECTORS_URL = new URL("search/vectors.bin", document.baseURI);
  var TRANSFORMERS_URL =
    "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/+esm";

  var RRF_K = 60;
  var KW_WEIGHT = 1.0;
  var VEC_WEIGHT = 1.15;
  var MIN_AND_RESULTS = 5;
  var VECTOR_FLOOR = 0.7;
  var RESULT_CAP = 30;

  var overlay, input, resultsEl, statusEl, semanticToggle;
  var mini = null;
  var docs = null;
  var manifest = null;
  var apiMode = false;
  var apiUrl = null;
  var apiController = null;
  var loadingPromise = null;
  var isOpen = false;
  var selected = -1;
  var debounceTimer = null;
  var searchSeq = 0;

  var vectors = null;
  var vectorsPromise = null;
  var extractor = null;
  var modelPromise = null;
  var semanticEnabled = false;
  var semanticState = "off"; // off | loading | ready | error

  // --- Text normalization (mirrors search/text.py) ---

  function normalizeFa(s) {
    return s
      .normalize("NFKC")
      .replace(/[\u064b-\u065f\u0670]/g, "")
      .replace(/\u0640/g, "")
      .replace(/\u0643/g, "\u06a9")
      .replace(/\u06aa/g, "\u06a9")
      .replace(/\u064a/g, "\u06cc")
      .replace(/\u0649/g, "\u06cc")
      .replace(/[\u200b-\u200f\u202a-\u202e\ufeff]/g, "");
  }

  function tokenize(text) {
    return text
      .toLowerCase()
      .split(/[\s\p{P}\p{S}]+/u)
      .filter(function (t) { return t.length > 0; });
  }

  function processTerm(term) {
    var t = normalizeFa(term).toLowerCase();
    return t.length ? t : null;
  }

  function queryTerms(query) {
    return tokenize(query)
      .map(processTerm)
      .filter(function (t) { return t && t.length > 1; });
  }

  // Query operators: +must -not "exact phrase". Single-word quotes behave
  // like +word (exact token); multi-word quotes require the words adjacently.
  function dedupWords(words) {
    var seen = {};
    return words.filter(function (w) {
      if (seen[w]) return false;
      seen[w] = true;
      return true;
    });
  }

  function normDate(value) {
    var m = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/.exec(value);
    if (!m) return null;
    var mo = m[2] || "01", day = m[3] || "01";
    if (+mo < 1 || +mo > 12 || +day < 1 || +day > 31) return null;
    return m[1] + "-" + mo + "-" + day;
  }

  function parseSearchQuery(q) {
    var must = [], not = [], phrases = [], notPhrases = [], optional = [];
    var tags = [], notTags = [], langs = [], notLangs = [];
    var after = null, before = null;
    function pushWord(word, target) {
      tokenize(word).forEach(function (t) {
        var p = processTerm(t);
        if (p) target.push(p);
      });
    }
    function pushFacet(field, value, negated) {
      if (field === "tag") {
        var t = value.toLowerCase().trim();
        if (!t) return false;
        (negated ? notTags : tags).push(t);
        return true;
      }
      if (field === "lang") {
        var l = value.toLowerCase().trim();
        if (!l) return false;
        (negated ? notLangs : langs).push(l);
        return true;
      }
      var iso = normDate(value.trim());
      if (!iso) return false;
      if (field === "after") after = !after || iso > after ? iso : after;
      else before = !before || iso < before ? iso : before;
      return true;
    }
    var re = /([+-]?)(tag|lang|after|before):(?:"([^"]+)"|(\S+))|([+-]?)"([^"]+)"|([+-]?)(\S+)/g, m;
    while ((m = re.exec(q)) !== null) {
      if (m[2] !== undefined) {
        var raw = (m[3] !== undefined ? m[3] : m[4] || "").trim();
        if (raw && !pushFacet(m[2], raw, m[1] === "-")) pushWord(m[0], optional);
        continue;
      }
      if (m[6] !== undefined) {
        var joined = tokenize(m[6]).map(processTerm).filter(Boolean).join(" ");
        if (!joined) continue;
        if (m[5] === "-") {
          if (joined.indexOf(" ") >= 0) notPhrases.push(joined);
          else pushWord(joined, not);
        } else {
          if (joined.indexOf(" ") >= 0) phrases.push(joined);
          else pushWord(joined, must);
        }
      } else if (m[7] === "+") {
        pushWord(m[8], must);
      } else if (m[7] === "-") {
        pushWord(m[8], not);
      } else {
        pushWord(m[8], optional);
      }
    }
    var phraseWords = [];
    phrases.forEach(function (p) {
      p.split(" ").forEach(function (w) { phraseWords.push(w); });
    });
    var engineTerms = dedupWords(must.concat(optional, phraseWords));
    return {
      must: dedupWords(must),
      not: dedupWords(not),
      phrases: dedupWords(phrases),
      notPhrases: dedupWords(notPhrases),
      tags: dedupWords(tags),
      notTags: dedupWords(notTags),
      langs: dedupWords(langs),
      notLangs: dedupWords(notLangs),
      after: after,
      before: before,
      positives: engineTerms.filter(function (t) { return t.length > 1; }),
      engineTerms: engineTerms,
      highlightTerms: engineTerms.filter(function (t) { return t.length > 1; }),
      vectorText: dedupWords(must.concat(optional, phrases)).join(" ")
    };
  }

  function hasFacets(pq) {
    return pq.tags.length + pq.notTags.length + pq.langs.length +
      pq.notLangs.length > 0 || pq.after !== null || pq.before !== null;
  }

  function chunkMatchesOps(doc, ops) {
    var fields = [doc.t || "", doc.h || "", (doc.g || []).join(" "), doc.x || ""];
    var tokens = {}, parts = [];
    fields.forEach(function (f) {
      var tks = tokenize(f).map(processTerm).filter(Boolean);
      tks.forEach(function (t) { tokens[t] = true; });
      parts.push(tks.join(" "));
    });
    var joined = parts.join(" ");
    for (var i = 0; i < ops.must.length; i++) {
      if (!tokens[ops.must[i]]) return false;
    }
    for (var j = 0; j < ops.not.length; j++) {
      if (tokens[ops.not[j]]) return false;
    }
    for (var k = 0; k < ops.phrases.length; k++) {
      if (joined.indexOf(ops.phrases[k]) < 0) return false;
    }
    for (var l = 0; l < ops.notPhrases.length; l++) {
      if (joined.indexOf(ops.notPhrases[l]) >= 0) return false;
    }
    var tags = (doc.g || []).map(function (g) { return String(g).toLowerCase(); });
    for (var ti = 0; ti < (ops.tags || []).length; ti++) {
      if (tags.indexOf(ops.tags[ti]) < 0) return false;
    }
    for (var tj = 0; tj < (ops.notTags || []).length; tj++) {
      if (tags.indexOf(ops.notTags[tj]) >= 0) return false;
    }
    var lang = String(doc.l || "").toLowerCase();
    if ((ops.langs || []).length && ops.langs.indexOf(lang) < 0) return false;
    for (var lk = 0; lk < (ops.notLangs || []).length; lk++) {
      if (lang === ops.notLangs[lk]) return false;
    }
    var date = doc.d || "";
    if (ops.after && date < ops.after) return false;
    if (ops.before && date >= ops.before) return false;
    return true;
  }

  function filterOps(entries, ops) {
    return entries.filter(function (e) { return chunkMatchesOps(e.doc, ops); });
  }

  // --- Small helpers ---

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function makeSnippet(text, terms) {
    if (!text) return "";
    var lower = normalizeFa(text).toLowerCase();
    var at = -1;
    for (var i = 0; i < terms.length; i++) {
      var idx = lower.indexOf(terms[i]);
      if (idx >= 0 && (at < 0 || idx < at)) at = idx;
    }
    var start = at > 60 ? at - 60 : 0;
    var snippet = text.slice(start, start + 260);
    var html = escapeHtml(snippet);
    if (terms.length) {
      var re = new RegExp("(" + terms.map(escapeRegExp).join("|") + ")", "giu");
      html = html.replace(re, "<mark>$1</mark>");
    }
    if (start > 0) html = "\u2026" + html;
    if (start + 260 < text.length) html += "\u2026";
    return html;
  }

  function makeResult(doc, terms, semantic) {
    var li = document.createElement("li");
    li.className = "search-result";

    var a = document.createElement("a");
    a.href = doc.u + (doc.a ? "#" + doc.a : "");
    a.target = "_blank";
    a.rel = "noopener";

    var head = document.createElement("div");
    head.className = "sr-head";

    var title = document.createElement("span");
    title.className = "sr-title";
    title.textContent = doc.t || "(untitled)";
    head.appendChild(title);

    if (semantic === true || semantic === "vec") {
      var badge = document.createElement("span");
      badge.className = "sr-badge";
      badge.textContent = "AI";
      badge.title = "Matched semantically";
      head.appendChild(badge);
    }

    if (doc.d) {
      var date = document.createElement("span");
      date.className = "sr-date";
      date.textContent = doc.d;
      head.appendChild(date);
    }
    a.appendChild(head);

    if (doc.h) {
      var heading = document.createElement("div");
      heading.className = "sr-heading";
      heading.textContent = doc.h;
      a.appendChild(heading);
    }

    var snippet = document.createElement("div");
    snippet.className = "sr-snippet";
    snippet.innerHTML = makeSnippet(doc.x, terms);
    a.appendChild(snippet);

    if (doc.g && doc.g.length) {
      var tags = document.createElement("div");
      tags.className = "sr-tags";
      doc.g.forEach(function (tag) {
        var span = document.createElement("span");
        span.className = "sr-tag";
        span.textContent = tag;
        tags.appendChild(span);
      });
      a.appendChild(tags);
    }

    li.appendChild(a);
    return li;
  }

  // --- Index loading ---

  function loadIndex() {
    if (mini) return Promise.resolve(mini);
    if (loadingPromise) return loadingPromise;

    statusEl.textContent = "Loading search index\u2026";

    loadingPromise = Promise.all([
      fetch(DOCS_URL).then(function (r) {
        if (!r.ok) throw new Error("index not found");
        return r.json();
      }),
      fetch(MANIFEST_URL)
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; })
    ])
      .then(function (res) {
        if (typeof MiniSearch === "undefined") {
          throw new Error("search engine failed to load");
        }
        docs = res[0];
        manifest = res[1];
        var fields = (manifest && manifest.fields && manifest.fields.indexed) ||
          ["t", "h", "g", "x"];
        var stored = (manifest && manifest.fields && manifest.fields.stored) ||
          ["p", "u", "t", "d", "g", "l", "h", "a", "x"];
        mini = new MiniSearch({
          idField: "i",
          fields: fields,
          storeFields: stored,
          tokenize: tokenize,
          processTerm: processTerm,
          searchOptions: {
            boost: { t: 3, h: 2, g: 2, x: 1 },
            fuzzy: 0.2,
            prefix: true
          }
        });
        mini.addAll(docs);
        var vecMeta = manifest && manifest.vectors;
        apiMode = !!(vecMeta && vecMeta.backend === "cloudflare" && vecMeta.api);
        apiUrl = apiMode ? vecMeta.api : null;
        setupSemanticAvailability();
        return mini;
      })
      .catch(function (err) {
        loadingPromise = null;
        throw err;
      });

    return loadingPromise;
  }

  // --- Vectors ---

  function loadVectors() {
    if (vectors) return Promise.resolve(vectors);
    if (vectorsPromise) return vectorsPromise;
    vectorsPromise = fetch(VECTORS_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("vectors not found");
        return r.arrayBuffer();
      })
      .then(function (buf) {
        vectors = parseVectors(buf);
        return vectors;
      })
      .catch(function (err) {
        vectorsPromise = null;
        throw err;
      });
    return vectorsPromise;
  }

  function parseVectors(buf) {
    var dv = new DataView(buf);
    var magic = String.fromCharCode(
      dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3)
    );
    if (magic !== "NSEV") throw new Error("bad vectors file");
    var count = dv.getUint32(8, true);
    var dim = dv.getUint32(12, true);
    var scales = new Float32Array(count);
    var off = 16;
    for (var i = 0; i < count; i++) {
      scales[i] = dv.getFloat32(off, true);
      off += 4;
    }
    var vecs = new Int8Array(buf, off, count * dim);
    return { count: count, dim: dim, scales: scales, vecs: vecs };
  }

  // --- Model ---

  function loadModel() {
    if (extractor) return Promise.resolve(extractor);
    if (modelPromise) return modelPromise;
    var modelId = (manifest && manifest.model && manifest.model.id) ||
      "Xenova/multilingual-e5-small";
    modelPromise = import(TRANSFORMERS_URL)
      .then(function (mod) {
        return mod.pipeline("feature-extraction", modelId, {
          dtype: "q8",
          progress_callback: onModelProgress
        });
      })
      .then(function (ex) {
        extractor = ex;
        return ex;
      })
      .catch(function (err) {
        modelPromise = null;
        throw err;
      });
    return modelPromise;
  }

  function onModelProgress(p) {
    if (!isOpen) return;
    if (p && p.status === "progress" && p.total) {
      var pct = Math.round((p.loaded / p.total) * 100);
      statusEl.textContent = "Downloading AI model\u2026 " + pct + "%";
    } else if (p && p.status === "ready") {
      statusEl.textContent = "AI model ready";
    }
  }

  function embedQuery(q) {
    return loadModel().then(function (ex) {
      var prefix = (manifest && manifest.model && manifest.model.query_prefix) || "query: ";
      return ex([prefix + q], { pooling: "mean", normalize: true }).then(function (out) {
        return out.data; // Float32Array, already unit norm
      });
    });
  }

  function vectorSearch(qvec, k) {
    var n = vectors.count;
    var dim = vectors.dim;
    var v = vectors.vecs;
    var sc = vectors.scales;
    var scores = new Float64Array(n);
    for (var r = 0; r < n; r++) {
      var base = r * dim;
      var dot = 0;
      for (var i = 0; i < dim; i++) dot += v[base + i] * qvec[i];
      scores[r] = sc[r] * dot;
    }
    var order = new Array(n);
    for (var j = 0; j < n; j++) order[j] = j;
    order.sort(function (a, b) { return scores[b] - scores[a]; });
    var out = [];
    for (var t = 0; t < k && t < n; t++) {
      if (scores[order[t]] < VECTOR_FLOOR) break;
      out.push(docs[order[t]]);
    }
    return out;
  }

  // --- Fusion ---

  function fuse(keyword, vec, terms, ops) {
    var map = {};
    function add(doc, rank, arm, weight) {
      var e = map[doc.i];
      if (!e) { e = map[doc.i] = { doc: doc, score: 0, arms: {} }; }
      e.score += weight / (RRF_K + rank + 1);
      e.arms[arm] = rank + 1;
    }
    keyword.forEach(function (d, i) { add(d, i, "kw", KW_WEIGHT); });
    vec.forEach(function (d, i) { add(d, i, "vec", VEC_WEIGHT); });

    if (Object.keys(map).length === 0 && ops && hasFacets(ops)) {
      // Facet-only browsing: every chunk is a candidate, newest first.
      docs.forEach(function (doc) {
        map[doc.i] = { doc: doc, score: 0, arms: {} };
      });
    }

    var list = Object.keys(map).map(function (k) { return map[k]; });
    list.forEach(function (e) {
      var d = e.doc;
      var title = normalizeFa(d.t || "").toLowerCase();
      var inTitle = 0;
      terms.forEach(function (t) { if (title.indexOf(t) >= 0) inTitle++; });
      if (terms.length && inTitle === terms.length) e.score *= 3.0;
      else if (inTitle) e.score *= 1.2;

      var when = Date.parse(d.d);
      if (!isNaN(when)) {
        var years = (Date.now() - when) / (365.25 * 24 * 3600 * 1000);
        e.score *= 1 / (1 + 0.03 * Math.max(0, years));
      }
    });

    list.sort(function (a, b) { return b.score - a.score; });

    var filtered = ops ? list.filter(function (e) { return chunkMatchesOps(e.doc, ops); }) : list;

    var seen = {};
    var out = [];
    for (var i = 0; i < filtered.length && out.length < RESULT_CAP; i++) {
      var e = filtered[i];
      if (seen[e.doc.p]) continue;
      seen[e.doc.p] = true;
      e.semantic = e.arms.vec && !e.arms.kw ? true : false;
      out.push(e);
    }
    return out;
  }

  // --- Search + render ---

  function dedupeByPost(entries, max) {
    var seen = {};
    var out = [];
    for (var i = 0; i < entries.length && out.length < max; i++) {
      var d = entries[i].doc || entries[i];
      if (seen[d.p]) continue;
      seen[d.p] = true;
      out.push(entries[i]);
    }
    return out;
  }

  function renderEntries(entries, terms, query, ai) {
    resultsEl.innerHTML = "";
    selected = -1;

    if (!entries.length) {
      statusEl.textContent = 'No results for "' + query + '"';
      var empty = document.createElement("li");
      empty.className = "search-empty";
      empty.textContent = "No matching posts.";
      resultsEl.appendChild(empty);
      return;
    }

    var suffix = ai ? " \u00b7 AI" : "";
    statusEl.textContent = entries.length +
      (entries.length === 1 ? " result" : " results") + suffix;
    entries.forEach(function (e) {
      resultsEl.appendChild(makeResult(e.doc, terms, e.semantic));
    });
  }

  function runSearch() {
    if (!mini) return;
    var q = (input.value || "").trim();
    var seq = ++searchSeq;

    if (!q) {
      resultsEl.innerHTML = "";
      statusEl.textContent = "";
      selected = -1;
      return;
    }

    var pq = parseSearchQuery(q);
    var terms = pq.highlightTerms;
    if (!pq.engineTerms.length && !pq.phrases.length && !hasFacets(pq)) {
      renderEntries([], terms, q, false);
      return;
    }
    var engineQuery = pq.engineTerms.join(" ");
    // AND first for precision; fall back to OR when almost nothing matches.
    var keyword = [];
    if (engineQuery) {
      keyword = mini.search(engineQuery, { combineWith: "AND" }).slice(0, 50);
      if (keyword.length < MIN_AND_RESULTS) {
        keyword = mini.search(engineQuery, { combineWith: "OR" }).slice(0, 50);
      }
    }
    var keywordPosts = dedupeByPost(filterOps(keyword.map(function (d) {
      return { doc: d };
    }), pq), RESULT_CAP);

    if (apiMode) {
      // Instant local keyword first, upgraded by the server hybrid when it
      // lands. Offline or on error, the keyword list simply stays.
      renderEntries(keywordPosts, terms, q, false);
      fetchApiResults(q, terms, seq);
      return;
    }

    renderEntries(keywordPosts, terms, q, semanticEnabled);

    if (semanticEnabled && pq.vectorText) {
      embedQuery(pq.vectorText)
        .then(function (qvec) {
          if (seq !== searchSeq) return;
          var vec = vectorSearch(qvec, 50);
          if (vec.length || keyword.length || hasFacets(pq)) {
            renderEntries(fuse(keyword, vec, terms, pq), terms, q, true);
          }
        })
        .catch(function (err) {
          if (seq !== searchSeq) return;
          semanticState = "error";
          updateToggle();
          statusEl.textContent = "AI search failed: " + err.message;
        });
    }
  }

  function fetchApiResults(q, terms, seq) {
    if (apiController) {
      try { apiController.abort(); } catch (e) {}
    }
    apiController = new AbortController();
    var timer = setTimeout(function () {
      try { apiController.abort(); } catch (e) {}
    }, 10000);

    fetch(apiUrl + "?q=" + encodeURIComponent(q) + "&scope=blog", {
      signal: apiController.signal
    })
      .then(function (r) {
        clearTimeout(timer);
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (payload) {
        if (seq !== searchSeq || !payload || !payload.results) return;
        var entries = payload.results.map(function (d) {
          return { doc: d, semantic: !!d.semantic };
        });
        if (entries.length) renderEntries(entries, terms, q, true);
      })
      .catch(function () {
        clearTimeout(timer);
        // Keep the local keyword results already on screen.
      });
  }

  function searchInput() {
    var q = input.value;
    if (mini) {
      runSearch();
      return;
    }
    loadIndex()
      .then(function () { runSearch(); })
      .catch(function (err) {
        statusEl.textContent = "Search unavailable: " + err.message;
      });
  }

  // --- Semantic toggle ---

  function setupSemanticAvailability() {
    if (!semanticToggle) return;
    if (apiMode) {
      // Server does the embeddings: no download, no toggle needed.
      semanticToggle.hidden = true;
      semanticEnabled = false;
      return;
    }
    // The on-device toggle only makes sense for local-backend vectors the
    // browser can actually embed. Cloudflare vectors need the API (or nothing).
    var vecMeta = manifest && manifest.vectors;
    var available = !!(vecMeta && vecMeta.backend !== "cloudflare");
    if (!available) {
      semanticToggle.hidden = true;
      return;
    }
    semanticToggle.hidden = false;
    var stored = null;
    try { stored = localStorage.getItem("search.semantic"); } catch (e) { stored = null; }
    semanticEnabled = stored === "1";
    if (semanticEnabled) {
      semanticState = "loading";
      ensureSemanticReady().then(function () {
        semanticState = "ready";
        updateToggle();
        if (isOpen && input.value.trim()) {
          if (mini) runSearch();
        }
      }).catch(function (err) {
        semanticState = "error";
        updateToggle();
      });
    }
    updateToggle();
  }

  function updateToggle() {
    if (!semanticToggle) return;
    if (!semanticEnabled) {
      semanticToggle.textContent = "AI search: off";
      semanticToggle.classList.remove("on");
    } else if (semanticState === "ready") {
      semanticToggle.textContent = "AI search: on";
      semanticToggle.classList.add("on");
    } else if (semanticState === "error") {
      semanticToggle.textContent = "AI search: error";
      semanticToggle.classList.remove("on");
    } else {
      semanticToggle.textContent = "AI search: loading\u2026";
    }
  }

  function setSemantic(on) {
    semanticEnabled = on;
    try { localStorage.setItem("search.semantic", on ? "1" : "0"); } catch (e) {}
    if (on) {
      semanticState = "loading";
      updateToggle();
      ensureSemanticReady()
        .then(function () {
          semanticState = "ready";
          updateToggle();
          if (isOpen && input.value.trim()) searchInput();
        })
        .catch(function (err) {
          semanticState = "error";
          updateToggle();
          statusEl.textContent = "AI search failed: " + err.message;
        });
    } else {
      semanticState = "off";
      updateToggle();
      if (isOpen && input.value.trim()) searchInput();
    }
  }

  function ensureSemanticReady() {
    return Promise.all([loadVectors(), loadModel()]);
  }

  // --- Keyboard navigation ---

  function move(delta) {
    var items = resultsEl.querySelectorAll(".search-result");
    if (!items.length) return;
    if (selected >= 0 && items[selected]) items[selected].classList.remove("selected");
    selected += delta;
    if (selected < 0) selected = 0;
    if (selected > items.length - 1) selected = items.length - 1;
    var el = items[selected];
    el.classList.add("selected");
    el.scrollIntoView({ block: "nearest" });
  }

  function openSelected() {
    var items = resultsEl.querySelectorAll(".search-result");
    if (!items.length) return;
    var el = items[selected >= 0 ? selected : 0];
    var a = el && el.querySelector("a");
    if (a) a.click();
  }

  // --- Open / close ---

  function openSearch() {
    if (isOpen) return;
    isOpen = true;
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    input.value = "";
    statusEl.textContent = "";
    resultsEl.innerHTML = "";
    selected = -1;
    input.focus();
    loadIndex()
      .then(function () {
        if (input.value.trim()) runSearch();
      })
      .catch(function (err) {
        statusEl.textContent = "Search unavailable: " + err.message;
      });
  }

  function closeSearch() {
    if (!isOpen) return;
    isOpen = false;
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  // --- Init ---

  function init() {
    overlay = document.getElementById("search-overlay");
    input = document.getElementById("search-input");
    resultsEl = document.getElementById("search-results");
    statusEl = document.getElementById("search-status");
    semanticToggle = document.getElementById("search-semantic-toggle");
    if (!overlay || !input || !resultsEl || !statusEl) return;

    var toggle = document.getElementById("search-toggle");
    if (toggle) toggle.addEventListener("click", openSearch);

    var closeBtn = document.getElementById("search-close");
    if (closeBtn) closeBtn.addEventListener("click", closeSearch);

    if (semanticToggle) {
      semanticToggle.addEventListener("click", function () {
        setSemantic(!semanticEnabled);
      });
    }

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeSearch();
    });

    input.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(searchInput, 100);
    });

    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        if (isOpen) closeSearch(); else openSearch();
        return;
      }
      if (!isOpen) return;
      if (e.key === "Escape") {
        e.preventDefault();
        closeSearch();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        move(1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        move(-1);
      } else if (e.key === "Enter") {
        e.preventDefault();
        openSelected();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
