const ARTIFACT_URL = "../../artifacts/va_case_management_workflow_support_v1/requirement_kernels.json";

const state = {
  artifact: null,
  family: "all",
  query: "",
  selectedKernelId: null,
};

const searchInput = document.getElementById("search-input");
const familyFilter = document.getElementById("family-filter");
const summaryGrid = document.getElementById("summary-grid");
const heroMeta = document.getElementById("hero-meta");
const resultsLabel = document.getElementById("results-label");
const kernelList = document.getElementById("kernel-list");
const detailEmpty = document.getElementById("detail-empty");
const kernelDetail = document.getElementById("kernel-detail");

initialize();

async function initialize() {
  try {
    const response = await fetch(ARTIFACT_URL);
    if (!response.ok) {
      throw new Error(`Failed to load artifact: ${response.status}`);
    }
    state.artifact = await response.json();
    state.selectedKernelId = state.artifact.kernels[0]?.kernel_id ?? null;
    renderSummary();
    renderFamilyOptions();
    render();
  } catch (error) {
    detailEmpty.innerHTML = `<p>Unable to load the kernel artifact.<br /><code>${escapeHtml(error.message)}</code></p>`;
  }
}

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value.trim().toLowerCase();
  syncSelectedKernel();
  render();
});

familyFilter.addEventListener("change", (event) => {
  state.family = event.target.value;
  syncSelectedKernel();
  render();
});

function renderSummary() {
  const { counts, corpus, generated_at: generatedAt } = state.artifact;

  const stats = [
    ["Generated", formatTimestamp(generatedAt)],
    ["Selected docs", counts.documents],
    ["Candidates", counts.requirement_candidates],
    ["Kernels", counts.kernels],
    ["Corpus", corpus.label],
  ];

  heroMeta.innerHTML = stats
    .map(
      ([label, value]) => `
        <div class="stat-card">
          <span class="stat-label">${escapeHtml(label)}</span>
          <strong>${escapeHtml(String(value))}</strong>
        </div>
      `
    )
    .join("");

  const familyCounts = new Map();
  for (const kernel of state.artifact.kernels) {
    familyCounts.set(kernel.family_label, (familyCounts.get(kernel.family_label) ?? 0) + 1);
  }

  summaryGrid.innerHTML = [...familyCounts.entries()]
    .map(
      ([family, count]) => `
        <div class="summary-card">
          <span class="summary-label">${escapeHtml(family)}</span>
          <strong>${count} kernels</strong>
        </div>
      `
    )
    .join("");
}

function renderFamilyOptions() {
  const families = [...new Set(state.artifact.kernels.map((kernel) => kernel.family_label))].sort();
  familyFilter.innerHTML = [
    `<option value="all">All families</option>`,
    ...families.map((family) => `<option value="${escapeHtml(family)}">${escapeHtml(family)}</option>`),
  ].join("");
}

function render() {
  const kernels = filteredKernels();
  resultsLabel.textContent = `${kernels.length} visible kernels`;

  kernelList.innerHTML = kernels.length ? kernels.map(renderKernelCard).join("") : renderEmptyResults();
  for (const button of kernelList.querySelectorAll("[data-kernel-id]")) {
    button.addEventListener("click", () => {
      state.selectedKernelId = button.dataset.kernelId;
      render();
    });
  }

  const selectedKernel = kernels.find((kernel) => kernel.kernel_id === state.selectedKernelId) ?? kernels[0] ?? null;
  state.selectedKernelId = selectedKernel?.kernel_id ?? null;
  renderDetail(selectedKernel);
}

function filteredKernels() {
  return state.artifact.kernels.filter((kernel) => {
    if (state.family !== "all" && kernel.family_label !== state.family) {
      return false;
    }
    if (!state.query) {
      return true;
    }
    const haystack = [
      kernel.label,
      kernel.family_label,
      kernel.representative_requirement,
      kernel.representative_requirement_raw,
      ...kernel.top_terms,
      ...kernel.evidence.flatMap((evidence) => [evidence.cleaned_snippet_text, evidence.raw_snippet_text, evidence.title]),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(state.query);
  });
}

function syncSelectedKernel() {
  const kernels = filteredKernels();
  if (!kernels.some((kernel) => kernel.kernel_id === state.selectedKernelId)) {
    state.selectedKernelId = kernels[0]?.kernel_id ?? null;
  }
}

function renderKernelCard(kernel) {
  const isActive = kernel.kernel_id === state.selectedKernelId;
  return `
    <button class="kernel-card${isActive ? " active" : ""}" data-kernel-id="${escapeHtml(kernel.kernel_id)}" type="button">
      <h3>${escapeHtml(kernel.label)}</h3>
      <div class="kernel-meta">
        <span class="meta-pill">${escapeHtml(kernel.family_label)}</span>
        <span class="meta-pill">${kernel.recurrence_count} snippets</span>
        <span class="meta-pill">${kernel.document_count} notices</span>
      </div>
      <p class="kernel-preview">${escapeHtml(kernel.representative_requirement)}</p>
    </button>
  `;
}

function renderDetail(kernel) {
  if (!kernel) {
    kernelDetail.hidden = true;
    detailEmpty.hidden = false;
    return;
  }

  detailEmpty.hidden = true;
  kernelDetail.hidden = false;
  kernelDetail.innerHTML = `
    <div class="detail-header">
      <div>
        <p class="eyebrow">Analyst Review</p>
        <h2>${escapeHtml(kernel.label)}</h2>
        <p>${escapeHtml(kernel.family_label)}</p>
      </div>
      <div class="detail-badges">
        <div class="detail-badge">Recurrence ${kernel.recurrence_count}</div>
        <div class="detail-badge">Notices ${kernel.document_count}</div>
        <div class="detail-badge">Confidence ${kernel.confidence}</div>
      </div>
    </div>

    <div class="detail-grid">
      <article class="representative-card">
        <h3>Representative Requirement</h3>
        <p class="block-label">Analyst-facing snippet</p>
        <div class="snippet-block"><code>${escapeHtml(kernel.representative_requirement)}</code></div>
        <p class="block-label">Raw extracted evidence</p>
        <div class="snippet-block raw-block"><code>${escapeHtml(kernel.representative_requirement_raw)}</code></div>
      </article>

      <article class="representative-card">
        <h3>Top Terms</h3>
        <div class="terms">
          ${kernel.top_terms.map((term) => `<span class="term-pill">${escapeHtml(term)}</span>`).join("")}
        </div>
      </article>
    </div>

    <section class="evidence-grid">
      ${kernel.evidence.map(renderEvidenceCard).join("")}
    </section>
  `;
}

function renderEvidenceCard(evidence) {
  return `
    <article class="evidence-card">
      <div class="evidence-meta">
        <span class="meta-chip">${escapeHtml(evidence.posted_date)}</span>
        <span class="meta-chip">${escapeHtml(evidence.source_part)}</span>
        <span class="meta-chip">${escapeHtml(evidence.section_title)}</span>
      </div>
      <h3>${escapeHtml(evidence.title)}</h3>
      <p class="block-label">Analyst-facing snippet</p>
      <div class="snippet-block"><code>${escapeHtml(evidence.cleaned_snippet_text)}</code></div>
      <p class="block-label">Raw extracted evidence</p>
      <div class="snippet-block raw-block"><code>${escapeHtml(evidence.raw_snippet_text)}</code></div>
      <p class="source-link-row">
        <a href="${escapeHtml(evidence.source_url)}" target="_blank" rel="noreferrer">Open source notice</a>
      </p>
    </article>
  `;
}

function renderEmptyResults() {
  return `
    <div class="empty-results">
      No kernels match the current search/filter. Try clearing the query or switching back to all families.
    </div>
  `;
}

function formatTimestamp(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
