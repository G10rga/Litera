/* ==========================================================================
   LITERA — საერთო ლოგიკა (icons, homepage render, work page render, tabs)
   ========================================================================== */

const ICONS = {
  cross: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M12 2v20M6 8h12"/></svg>`,
  tiger: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 14c0-4 3-8 8-8s8 4 8 8-3 6-8 6-8-2-8-6Z"/><path d="M8 9 6 5m10 4 2-4M9 14h.01M15 14h.01M10 17c1 1 3 1 4 0"/></svg>`,
  quill: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M20 4c-6 0-13 5-15 13l3 3C16 18 20 11 20 4Z"/><path d="M5 20 3 22"/></svg>`,
  star: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M12 2l2.6 6.6L22 9l-5.3 4.6L18.2 21 12 17.3 5.8 21l1.5-7.4L2 9l7.4-.4Z"/></svg>`,
  lamp: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M9 3h6l2 7-5 3-5-3 2-7Z"/><path d="M12 13v6m-4 2h8"/></svg>`,
  tower: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M8 21V9l4-5 4 5v12"/><path d="M8 13h8M8 17h8M10 9V4h4v5"/></svg>`,
  moon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg>`,
  leaf: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M20 4S6 4 5 15c-1 8 6 6 9 3 6-6 6-14 6-14Z"/><path d="M6 18c3-6 9-9 13-11"/></svg>`,
  book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5c3 0 6 1 8 3 2-2 5-3 8-3v14c-3 0-6 1-8 3-2-2-5-3-8-3V5Z"/><path d="M12 8v14"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>`,
  chev: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m6 9 6 6 6-6"/></svg>`
};

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function findAuthor(id) {
  return LITERA_AUTHORS.find((a) => a.id === id);
}
function findCategory(id) {
  return LITERA_CATEGORIES.find((c) => c.id === id);
}

/* --------------------------------------------------------------------------
   მთავარი გვერდის რენდერი
-------------------------------------------------------------------------- */
function renderHome() {
  const chaptersEl = document.getElementById("chapters");
  if (!chaptersEl) return;

  let html = "";
  LITERA_CATEGORIES.forEach((cat) => {
    const authors = LITERA_AUTHORS.filter((a) => a.category === cat.id);
    if (!authors.length) return;

    html += `<section class="chapter" data-chapter="${cat.id}">
      <div class="chapter-head">
        <div class="emblem">${ICONS[cat.emblem] || ICONS.book}</div>
        <h2>${escapeHtml(cat.title)}</h2>
        <div class="sub">${escapeHtml(cat.subtitle)}</div>
      </div>
      <div class="card-grid">
        ${authors.map((a) => authorCardHtml(a)).join("")}
      </div>
    </section>`;
  });

  chaptersEl.innerHTML = html;
}

function authorCardHtml(author) {
  const titles = author.works.map((w) => w.title).join(" • ");
  return `<a class="author-card" href="work.html?author=${encodeURIComponent(author.id)}" data-search="${escapeHtml((author.name + " " + titles).toLowerCase())}">
    <div class="name">${escapeHtml(author.name)}</div>
    <div class="works">${escapeHtml(titles)}</div>
    <span class="count">${author.works.length} ნაწარმოები</span>
  </a>`;
}

function setupSearch() {
  const input = document.getElementById("search-input");
  if (!input) return;
  const emptyMsg = document.getElementById("search-empty");

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    let anyVisible = false;
    document.querySelectorAll(".chapter").forEach((chapter) => {
      let chapterHasVisible = false;
      chapter.querySelectorAll(".author-card").forEach((card) => {
        const match = !q || card.dataset.search.includes(q);
        card.style.display = match ? "" : "none";
        if (match) chapterHasVisible = true;
      });
      chapter.style.display = chapterHasVisible ? "" : "none";
      if (chapterHasVisible) anyVisible = true;
    });
    if (emptyMsg) emptyMsg.style.display = anyVisible ? "none" : "block";
  });
}

/* --------------------------------------------------------------------------
   ავტორის გვერდის რენდერი (work.html?author=id)
-------------------------------------------------------------------------- */
function renderAuthorPage() {
  const root = document.getElementById("author-root");
  if (!root) return;

  const params = new URLSearchParams(location.search);
  const authorId = params.get("author");
  const author = findAuthor(authorId);

  if (!author) {
    root.innerHTML = `<div class="page-head">
      <div class="breadcrumb"><a href="index.html">← მთავარი</a></div>
      <h1>ავტორი ვერ მოიძებნა</h1>
      <p>შეამოწმეთ ბმული ან დაბრუნდით <a href="index.html">მთავარ გვერდზე</a>.</p>
    </div>`;
    return;
  }

  const category = findCategory(author.category);
  document.title = `${author.name} — ლიტერა`;

  let head = `<div class="page-head">
    <div class="breadcrumb"><a href="index.html">მთავარი</a> / <a href="index.html#${category.id}">${escapeHtml(category.title)}</a></div>
    <h1>${escapeHtml(author.name)}</h1>
    <div class="category-tag">${escapeHtml(category.subtitle)}</div>
  </div>`;

  let body = "";
  author.works.forEach((work, wi) => {
    const uid = `w${wi}`;
    body += `<div class="work-block">
      <div class="work-title-row">
        <h2>${escapeHtml(work.title)}</h2>
        <span class="work-type">${escapeHtml(work.type)}</span>
      </div>
      ${work.note ? `<div class="work-note">${escapeHtml(work.note)}</div>` : ""}

      <div class="tabs" role="tablist">
        <button class="tab-btn active" data-tab="${uid}-summary">მოკლე შინაარსი</button>
        <button class="tab-btn" data-tab="${uid}-chars">პერსონაჟები</button>
        <button class="tab-btn" data-tab="${uid}-essays">საკითხავი თემები</button>
      </div>

      <div class="tab-panel active" id="${uid}-summary">
        ${work.parts.map((p, pi) => partHtml(p, pi)).join("")}
      </div>

      <div class="tab-panel" id="${uid}-chars">
        ${work.characters && work.characters.length ? charGridHtml(work.characters) : placeholderNote("პერსონაჟების პროფილები ჯერ არ არის დამატებული — დაამატეთ js/data.js ფაილში, characters მასივში.")}
      </div>

      <div class="tab-panel" id="${uid}-essays">
        ${work.essayThemes && work.essayThemes.length ? essayListHtml(work.essayThemes) : placeholderNote("ესეს თემები ჯერ არ არის დამატებული — დაამატეთ js/data.js ფაილში, essayThemes მასივში.")}
      </div>
    </div>`;
  });

  root.innerHTML = head + body;
  setupTabs();
  setupAccordions();
}

function partHtml(part, idx) {
  const num = String(idx + 1).padStart(2, "0");
  return `<div class="part">
    <button class="part-head">
      <span>${escapeHtml(part.title)}</span>
      <span style="display:flex;align-items:center;">
        <span class="idx">${num}</span>
        <span class="chev">${ICONS.chev}</span>
      </span>
    </button>
    <div class="part-body">
      ${part.summary && part.summary.trim()
        ? `<div>${part.summary}</div>`
        : placeholderNote("მოკლე შინაარსი ჯერ არ არის დამატებული — შეავსეთ js/data.js ფაილში, ამ ნაწილის summary ველი.")}
    </div>
  </div>`;
}

function charGridHtml(chars) {
  return `<div class="char-grid">${chars.map((c) => `
    <div class="char-card">
      <div class="name">${escapeHtml(c.name || "")}</div>
      ${c.role ? `<div class="role">${escapeHtml(c.role)}</div>` : ""}
      <div class="desc">${escapeHtml(c.description || "")}</div>
    </div>`).join("")}</div>`;
}

function essayListHtml(themes) {
  return `<ol class="essay-list">${themes.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ol>`;
}

function placeholderNote(text) {
  return `<div class="placeholder-note">${escapeHtml(text)}</div>`;
}

function setupTabs() {
  document.querySelectorAll(".work-block").forEach((block) => {
    const btns = block.querySelectorAll(".tab-btn");
    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        btns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        block.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        document.getElementById(btn.dataset.tab).classList.add("active");
      });
    });
  });
}

function setupAccordions() {
  document.querySelectorAll(".part-head").forEach((head) => {
    head.addEventListener("click", () => {
      head.closest(".part").classList.toggle("open");
    });
  });
  // ავტომატურად გახსენი პირველი ნაწილი თითოეულ ნაწარმოებში
  document.querySelectorAll(".tab-panel .part:first-child").forEach((p) => p.classList.add("open"));
}

document.addEventListener("DOMContentLoaded", () => {
  renderHome();
  setupSearch();
  renderAuthorPage();
});
