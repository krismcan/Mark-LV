// Public viewer only. All programme values come from the curated local snapshot.
const PHASE_STATES = ['COMPLETE', 'IN PROGRESS', 'NOT STARTED'];
const STAGES = { bounded: 'Bounded complete', progress: 'In progress', 'not-started': 'Not started', prototype: 'Offline prototype', future: 'Future / excluded' };
const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  layers: '<path d="m12 3 10 5-10 5L2 8l10-5Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
  shield: '<path d="M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  roadmap: '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h9a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h9"/>',
  check: '<path d="m5 12 4 4L19 6"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
  activity: '<path d="M2 12h4l3-8 6 16 3-8h4"/>',
  evidence: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
  external: '<path d="M14 3h7v7m0-7L10 14M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"/>',
  core: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v5m6-5v5M9 18v5m6-5v5M1 9h5m-5 6h5m12-6h5m-5 6h5"/>',
  brain: '<path d="M12 5c-2-4-8-2-7 2-4 1-4 6-1 7-2 4 3 8 6 5l2-2m0-12c2-4 8-2 7 2 4 1 4 6 1 7 2 4-3 8-6 5l-2-2V5Zm-7 2 3 3m-4 4h4m11-7-3 3m4 4h-4"/>',
  interaction: '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M8 21h8m-4-4v4M7 8h10M7 12h5"/>',
  product: '<path d="m12 3 9 5v9l-9 5-9-5V8l9-5Zm0 10v9M3 8l9 5 9-5M7.5 5.5l9 5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>'
};
const GROUP_ICONS = ['core', 'shield', 'brain', 'interaction', 'product'];
export const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const e = escapeHTML;
const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.layers}</svg>`;
const tone = status => status.toLowerCase().replaceAll(' ', '-');
const badge = (status, kind = tone(status)) => `<span class="badge ${e(kind)}"><span class="dot" aria-hidden="true"></span>${e(status)}</span>`;
const number = value => value.toLocaleString('en-GB');
const external = (url, label) => `<a class="external" href="${e(url)}" target="_blank" rel="noopener noreferrer">${e(label)}${icon('external')}</a>`;

export function sourceLinks(data) {
  const url = new URL(data.evidence.github);
  if (url.origin !== 'https://github.com' || !/^\/[^/]+\/[^/]+\/tree\/[^/]+$/.test(url.pathname) || url.search || url.hash) throw new Error('Expected a public GitHub branch URL.');
  const repo = `${url.origin}/${url.pathname.split('/').slice(1, 3).join('/')}`;
  for (const key of ['finalCommit', 'productCommit']) if (!/^[a-f0-9]{40}$/.test(data.evidence[key])) throw new Error(`Invalid ${key}.`);
  return { branch: url.href, final: `${repo}/commit/${data.evidence.finalCommit}`, product: `${repo}/commit/${data.evidence.productCommit}` };
}

export function validateData(data) {
  const assert = (ok, message) => { if (!ok) throw new Error(message); };
  const text = value => typeof value === 'string' && value.trim().length > 0;
  assert(data?.schemaVersion === 1 && data.publicSnapshot === true, 'Expected a version 1 public snapshot.');
  assert(text(data.title) && text(data.scope) && /^\d{4}-\d{2}-\d{2}$/.test(data.asOf) && !Number.isNaN(Date.parse(data.asOf)), 'Missing snapshot identity or date.');
  assert(Array.isArray(data.phases) && data.phases.length > 0 && data.phases.length === data.formal?.phaseTotal, 'Phase denominator does not match the snapshot.');
  assert(data.phases.every((p, i) => p.id === i && text(p.name) && text(p.group) && PHASE_STATES.includes(p.status)), 'Invalid phase or source status.');
  assert(Array.isArray(data.capabilities) && data.capabilities.length > 0 && data.capabilities.every(c => [c.name, c.group, c.stage, c.note].every(text) && Object.hasOwn(STAGES, c.kind)), 'Invalid capability scope or stage.');
  assert(new Set(data.capabilities.map(c => c.name)).size === data.capabilities.length, 'Duplicate capability.');
  const groups = new Set(data.capabilities.map(c => c.group));
  assert(groups.has('Security & Control') && data.phases.every(p => groups.has(p.group)), 'Missing capability group.');
  const stageStatuses = { complete: 'COMPLETE', 'in progress': 'IN PROGRESS', 'not started': 'NOT STARTED' };
  for (const capability of data.capabilities) {
    const reference = capability.stage.match(/Phase (\d+) (complete|in progress|not started)/i);
    if (reference) assert(data.phases.find(p => p.id === Number(reference[1]))?.status === stageStatuses[reference[2].toLowerCase()], `Capability and phase status disagree: ${capability.name}.`);
  }
  assert(Array.isArray(data.releaseGates) && data.releaseGates.length === data.formal.releaseGates && data.releaseGates.every((g, i) => g.id === i + 1 && text(g.name) && ['VERIFIED', 'NOT VERIFIED'].includes(g.status)), 'Invalid release gates.');
  const regression = data.metrics?.fullRegression;
  assert(regression && Number.isSafeInteger(regression.passed) && Number.isSafeInteger(regression.total) && regression.passed >= 0 && regression.total > 0 && regression.passed <= regression.total, 'Invalid regression counts.');
  assert(text(data.metrics.latestClosed) && text(data.metrics.next) && data.metrics.latestClosed !== data.metrics.next && typeof data.metrics.githubVerified === 'boolean' && typeof data.metrics.masterUpdated === 'boolean', 'Invalid verification metadata.');
  assert(data.formal.capabilityScore === 'NOT SCORED' && text(data.formal.closeDefinition) && text(data.formal.source) && text(data.formal.phaseRange), 'Readiness has no audited numeric denominator.');
  assert(Array.isArray(data.milestones) && data.milestones.length > 0 && data.milestones.every(m => [m.phase, m.date, m.name, m.note].every(text) && Number.isSafeInteger(m.tests) && m.tests > 0), 'Invalid milestone evidence.');
  assert(data.milestones.at(-1).phase === data.metrics.latestClosed && data.milestones.at(-1).tests === regression.total, 'Latest milestone and regression evidence disagree.');
  assert(data.flags?.noPublicEdits === true && data.flags.noProviderCalls === true && data.flags.noPrivateMasterContents === true, 'Public information boundary must be enabled.');
  assert(Array.isArray(data.notes) && data.notes.every(text) && text(data.evidence?.sourceDocument) && text(data.evidence.lastVerified), 'Missing methodology evidence.');
  sourceLinks(data);
  return data;
}

export function deriveSummary(data) {
  const counts = Object.fromEntries(PHASE_STATES.map(s => [s, data.phases.filter(p => p.status === s).length]));
  return {
    counts, total: data.phases.length,
    closure: (counts.COMPLETE / data.phases.length * 100).toFixed(1),
    verifiedGates: data.releaseGates.filter(g => g.status === 'VERIFIED').length,
    gateTotal: data.releaseGates.length,
    groups: [...new Set(data.capabilities.map(c => c.group))]
  };
}

// pathLength=100 makes every SVG arc exactly proportional, with no decorative gaps.
export function ringSegments(data) {
  const { counts, total } = deriveSummary(data);
  let offset = 0;
  return PHASE_STATES.map((status, i) => {
    const length = counts[status] / total * 100;
    const segment = { status, length, offset, color: ['#5de0c3', '#86b9ff', '#2b374b'][i] };
    offset += length;
    return segment;
  });
}

function phaseBar(data) {
  const { counts } = deriveSummary(data);
  return `<svg class="segmented-bar" viewBox="0 0 100 1" preserveAspectRatio="none" role="img" aria-label="${e(PHASE_STATES.map(status => `${counts[status]} ${status.toLowerCase()}`).join(', '))}">${ringSegments(data).map(a => `<rect x="${a.offset}" y="0" width="${a.length}" height="1" fill="${a.color}"/>`).join('')}</svg>`;
}

export function selectCapabilities(data, { search = '', group = '', stage = '', sort = 'source' } = {}) {
  const query = search.trim().toLocaleLowerCase('en-GB');
  const results = data.capabilities.filter(c => (!group || c.group === group) && (!stage || c.kind === stage) && (!query || [c.name, c.group, c.stage, c.note].join(' ').toLocaleLowerCase('en-GB').includes(query)));
  if (sort === 'name') results.sort((a, b) => a.name.localeCompare(b.name, 'en-GB'));
  if (sort === 'group') results.sort((a, b) => a.group.localeCompare(b.group, 'en-GB') || a.name.localeCompare(b.name, 'en-GB'));
  if (sort === 'stage') results.sort((a, b) => Object.keys(STAGES).indexOf(a.kind) - Object.keys(STAGES).indexOf(b.kind) || a.name.localeCompare(b.name, 'en-GB'));
  return results;
}

export function renderCapabilities(capabilities) {
  if (!capabilities.length) return '<p class="empty">No capabilities match these filters. Try another search or reset the filters.</p>';
  return capabilities.map(c => `<details class="capability-row"><summary><span class="capability-name">${e(c.name)}</span><span class="row-group">${e(c.group)}</span>${badge(c.stage, c.kind)}<span class="chevron">${icon('down')}</span></summary><div class="scope-note"><strong>Verified scope & limitations</strong>${e(c.note)}</div></details>`).join('');
}

export function renderPhases(data, filter = '') {
  return data.phases.filter(p => !filter || p.status === filter).map(p => `<article class="phase-card ${tone(p.status)}"><span class="phase-id">PHASE ${e(p.id)}</span><h3>${e(p.name)}</h3>${badge(p.status)}</article>`).join('');
}

function sectionTitle(id, index, title, intro, extra = '') {
  return `<div class="section-heading"><div><h2 id="${id}"><span class="section-number" aria-hidden="true">${index}</span>${title}</h2><p class="intro">${intro}</p></div>${extra}</div>`;
}

export function renderDashboard(data) {
  const s = deriveSummary(data);
  const links = sourceLinks(data);
  const date = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${data.asOf}T00:00:00Z`));
  const regression = data.metrics.fullRegression;
  const nav = [['overview', 'overview', 'Overview'], ['capabilities', 'layers', 'Capabilities'], ['roadmap', 'roadmap', 'Phase roadmap'], ['release', 'shield', 'Release gates'], ['milestones', 'activity', 'Milestones'], ['methodology', 'evidence', 'Evidence & scoring']];
  const security = data.phases.filter(p => p.group === 'Security & Control');
  const correction = name => { const c = data.capabilities.find(c => c.name.toLowerCase() === name.toLowerCase()); return c ? `<article class="correction"><div class="correction-title"><strong>${e(c.name)}</strong>${badge(c.stage, c.kind)}</div><p>${e(c.note)}</p></article>` : ''; };
  return `<aside class="sidebar" aria-label="Dashboard navigation"><a class="brand" href="#overview"><span class="brand-mark" aria-hidden="true">n</span><span>${e(data.title)}</span></a><p class="eyebrow">Programme intelligence</p><nav class="nav-links" aria-label="Sections">${nav.map(([id, glyph, name], i) => `<a href="#${id}"${i === 0 ? ' aria-current="location"' : ''}>${icon(glyph)}${name}</a>`).join('')}</nav><div class="sidebar-bottom"><strong>${icon('lock')} Public, read-only snapshot</strong>Curated evidence. Bounded claims.<br>Maintained in source control.</div></aside>
  <div class="shell"><header class="topbar"><div class="breadcrumb"><span>Programme</span><span aria-hidden="true">/</span><strong>Verified dashboard</strong></div><div class="header-actions"><span class="status-pill"><span class="dot" aria-hidden="true"></span>Offline-only prototype</span>${external(links.branch, 'GitHub source')}</div></header>
  <main class="main" id="main" tabindex="-1"><section class="section" id="overview" aria-labelledby="overview-title"><div class="hero"><div><p class="eyebrow">Evidence over estimates</p><h1 id="overview-title">Verified Programme Dashboard</h1><p>${e(data.title)} · Architecture, capability scope & release readiness</p></div><div class="snapshot"><span>Snapshot as of</span><time datetime="${e(data.asOf)}">${date}</time><span class="snapshot-status"><span class="dot" aria-hidden="true"></span>Curated public snapshot</span></div></div>
  <div class="kpi-grid"><article class="kpi closure" aria-label="Architecture phase closure: ${s.counts.COMPLETE} of ${s.total}, ${s.closure} percent"><div class="ring"><svg viewBox="0 0 100 100" role="img" aria-label="${e(PHASE_STATES.map(status => `${s.counts[status]} ${status.toLowerCase()}`).join(', '))}"><circle class="ring-track" cx="50" cy="50" r="42"/>${ringSegments(data).map(a => `<circle cx="50" cy="50" r="42" pathLength="100" stroke="${a.color}" stroke-dasharray="${a.length} ${100 - a.length}" stroke-dashoffset="${-a.offset}"/>`).join('')}</svg><div class="ring-label" aria-hidden="true"><strong>${s.closure}%</strong><small>PHASE CLOSURE</small></div></div><div><p class="kpi-label">Architecture closure</p><p class="kpi-value">${s.counts.COMPLETE}<span class="denominator"> / ${s.total}</span></p><p class="kpi-caption">Phases marked COMPLETE</p></div></article>
  <article class="kpi"><p class="kpi-label">${icon('shield')}Release gates</p><p class="kpi-value">${s.verifiedGates}<span class="denominator"> / ${s.gateTotal}</span></p><p class="kpi-caption">${s.verifiedGates === 0 ? 'Release acceptance not verified' : 'Gates marked VERIFIED'}</p></article>
  <article class="kpi"><p class="kpi-label">${icon('activity')}Windows regressions</p><p class="kpi-value">${number(regression.passed)}<span class="denominator"> / ${number(regression.total)}</span></p><p class="kpi-caption"><span class="dot" aria-hidden="true"></span>${regression.passed === regression.total ? 'Full regression passing' : 'Regression failures recorded'}</p></article>
  <article class="kpi"><p class="kpi-label">${icon('check')}Latest closed milestone</p><p class="kpi-value">${e(data.metrics.latestClosed)}</p><p class="kpi-caption">${e(data.milestones.at(-1).name)}</p></article></div>
  <p class="metric-footnote">${icon('info')}<span>${e(data.formal.closeDefinition)}</span></p>
  <div class="panel security-panel"><div><div class="security-title">${icon('shield')}<h2>Security & Control</h2></div><p>Bounded controls are tracked independently from release assurance. Completion of a control milestone does not certify the product for release.</p><a class="small-link" href="#release">Review release acceptance gates <span aria-hidden="true">↗</span></a></div><div class="security-phases">${security.map(p => `<div class="security-phase"><span>PHASE ${e(p.id)}</span><strong>${e(p.name)}</strong>${badge(p.status)}</div>`).join('')}</div></div>
  <div class="group-grid">${s.groups.map((group, i) => { const caps = data.capabilities.filter(c => c.group === group); return `<article class="panel group-card${group === 'Security & Control' ? ' featured' : ''}"><div class="group-icon">${icon(GROUP_ICONS[i])}<small>${caps.length} capabilities</small></div><h3>${e(group)}</h3><div class="group-capabilities">${caps.map(c => `<div class="group-capability"><span class="cap-name">${e(c.name)}</span>${badge(c.stage, c.kind)}</div>`).join('')}</div></article>`; }).join('')}</div>
  <div class="score-band"><span class="score-title">Capability readiness</span><strong>${e(data.formal.capabilityScore.toLowerCase().replace(/^./, x => x.toUpperCase()))}</strong><p>No audited weighting or overall readiness denominator.</p><button class="text-button" id="why-score" type="button" aria-haspopup="dialog">Why no 40%?</button></div></section>
  <section class="section" id="capabilities" aria-labelledby="capabilities-title">${sectionTitle('capabilities-title', '01', 'Capability explorer', `${data.capabilities.length} capabilities. Expand any row for the verified scope and limitations.`)}<div class="corrections">${correction('Computer control')}${correction('Memory')}</div><div class="panel explorer-panel"><div class="toolbar" role="search" aria-label="Filter capabilities"><div class="field"><label for="cap-search">Search capabilities</label><input id="cap-search" type="search" placeholder="Search name, scope or status…" autocomplete="off" aria-controls="capability-results"></div><div class="field"><label for="cap-group">Group</label><select id="cap-group" aria-controls="capability-results"><option value="">All groups</option>${s.groups.map(g => `<option>${e(g)}</option>`).join('')}</select></div><div class="field"><label for="cap-stage">Stage</label><select id="cap-stage" aria-controls="capability-results"><option value="">All stages</option>${Object.entries(STAGES).filter(([key]) => data.capabilities.some(c => c.kind === key)).map(([key, label]) => `<option value="${key}">${label}</option>`).join('')}</select></div><div class="field"><label for="cap-sort">Sort by</label><select id="cap-sort" aria-controls="capability-results"><option value="source">Source order</option><option value="name">Name A–Z</option><option value="group">Group A–Z</option><option value="stage">Stage</option></select></div><button id="reset-filters" type="button">Reset</button></div><div class="results-bar"><span id="cap-result-count" role="status" aria-live="polite" aria-atomic="true">Showing ${data.capabilities.length} of ${data.capabilities.length} capabilities</span><span>Read-only · select a row for scope</span></div><div class="explorer-columns" aria-hidden="true"><span>Capability</span><span>Group</span><span>Verified stage</span><span></span></div><div id="capability-results">${renderCapabilities(data.capabilities)}</div></div></section>
  <section class="section" id="roadmap" aria-labelledby="roadmap-title">${sectionTitle('roadmap-title', '02', 'Architecture roadmap', `Build Plan phases ${e(data.formal.phaseRange)} · source status, without maturity estimates.`)}<div class="filter-chips" role="group" aria-label="Filter architecture phases">${[['', 'All phases', s.total], ...PHASE_STATES.map(status => [status, status.charAt(0) + status.slice(1).toLowerCase(), s.counts[status]])].map(([value, label, count]) => `<button type="button" class="filter-chip" data-phase-filter="${value}" aria-pressed="${value === ''}" aria-controls="phase-results">${value ? `<span class="badge ${tone(value)}"><span class="dot" aria-hidden="true"></span></span>` : ''}${label}<span class="count">${count}</span></button>`).join('')}</div><div class="roadmap-summary">${phaseBar(data)}<div class="legend">${PHASE_STATES.map(status => `<span><span class="badge ${tone(status)}"><span class="dot" aria-hidden="true"></span></span>${s.counts[status]} ${status.toLowerCase()}</span>`).join('')}</div></div><p class="muted" id="phase-result-count" role="status" aria-live="polite" aria-atomic="true">Showing ${s.total} of ${s.total} phases</p><div class="roadmap-grid" id="phase-results">${renderPhases(data)}</div><div class="planned-note"><strong>${e(data.metrics.next)} · Planned only</strong><span>Next proposed target. No implementation or completion is claimed.</span></div></section>
  <section class="section" id="release" aria-labelledby="release-title">${sectionTitle('release-title', '03', 'Release acceptance gates', 'Engineering evidence and a runnable offline prototype do not establish release acceptance.')}<div class="gates-layout"><article class="panel gates-overview"><p class="eyebrow">Verified for release</p><div class="kpi-value">${s.verifiedGates}<span class="denominator"> / ${s.gateTotal}</span></div>${badge(s.verifiedGates === s.gateTotal ? 'VERIFIED' : 'NOT VERIFIED')}<p>Each gate requires explicit end-to-end evidence. Unverified gates remain open regardless of architecture closure.</p></article><div class="gate-grid">${data.releaseGates.map(g => `<article class="gate-card"><span class="gate-number" aria-hidden="true">${String(g.id).padStart(2, '0')}</span><div><h3><span class="sr-only">Gate ${g.id}: </span>${e(g.name)}</h3>${badge(g.status)}</div></article>`).join('')}</div></div></section>
  <section class="section" id="milestones" aria-labelledby="milestones-title">${sectionTitle('milestones-title', '04', 'Recent verified milestones', 'Windows regression evidence at each closure. Test totals describe scope, not product readiness.')}<div class="timeline">${data.milestones.map(m => `<article class="panel milestone"><div class="milestone-top"><span class="milestone-version">${e(m.phase)}</span><time>${e(m.date)}</time></div><h3>${e(m.name)}</h3><p>${e(m.note)}</p><div class="test-track"><div><strong>${number(m.tests)}</strong><small>regression tests at closure</small></div>${external(m.phase === data.metrics.latestClosed ? links.product : links.branch, m.phase === data.metrics.latestClosed ? 'Product commit' : 'Source branch')}</div></article>`).join('')}</div><div class="planned-note"><strong>${e(data.metrics.next)} · Proposed</strong><span>Future work is outside the verified milestone and regression track.</span></div></section>
  <section class="section" id="methodology" aria-labelledby="methodology-title">${sectionTitle('methodology-title', '05', 'How scores are determined', 'A transparent boundary between closed phases, delivered scope and release assurance.')}<div class="panel methodology"><div class="method-grid"><article class="method-item"><p class="eyebrow">01 / Architecture</p><h3>Count closed phases</h3><p>${e(data.formal.closeDefinition)}</p><p><strong>${s.counts.COMPLETE} ÷ ${s.total} × 100 = ${s.closure}%.</strong> Each phase has equal weight. Commercial backend is future scope, outside this denominator.</p></article><article class="method-item"><p class="eyebrow">02 / Capability</p><h3>Describe the verified boundary</h3><p>${e(data.scope)}</p><p>Stages describe bounded evidence. “Not scored” is intentional; historical estimates are unaudited and retired.</p></article><article class="method-item"><p class="eyebrow">03 / Provenance</p><h3>Curated from sealed evidence</h3><p>${e(data.formal.source)} ${e(data.evidence.sourceDocument)}.</p><p>GitHub verification: <strong>${data.metrics.githubVerified ? 'recorded' : 'not recorded'}</strong> · Master update: <strong>${data.metrics.masterUpdated ? 'recorded' : 'not recorded'}</strong>. Evidence last verified ${e(data.evidence.lastVerified)}.</p></article></div><div class="evidence-links">${external(links.branch, 'Verified Nayeon branch')}${external(links.final, `Sealed commit ${data.evidence.finalCommit.slice(0, 7)}`)}${external(links.product, `Product commit ${data.evidence.productCommit.slice(0, 7)}`)}<a href="./data/status.json">Public curated JSON</a></div></div><div class="boundary">${icon('lock')}<p><strong>Public information boundary.</strong> This static viewer exposes only the curated public snapshot. The private Drive master is named for provenance and is not linked or embedded. No provider calls, credentials, private workbook contents, cookies or public editing. Only repository collaborators can change source data.</p></div></section>
  <footer class="footer"><span>${e(data.title)} · Verified Programme Dashboard</span><span>Read-only snapshot · ${date} · Maintainer-curated evidence</span></footer></main></div>
  <dialog id="score-dialog" aria-labelledby="score-dialog-title"><div class="dialog-heading"><div><p class="eyebrow">Methodology note</p><h2 id="score-dialog-title">Why no 40%?</h2></div><button type="button" id="close-score" aria-label="Close explanation" autofocus>×</button></div><div class="dialog-copy"><p>The legacy headline and historical capability percentages were unaudited estimates. Their weights and denominator were not approved, so they have been retired.</p><p class="callout"><strong>Capability readiness: Not scored.</strong><br>The audited numerical measure here is architecture phase closure: ${s.counts.COMPLETE}/${s.total} = ${s.closure}%. It does not measure how much of the finished product is delivered.</p><p>Computer Control and Memory use their source stages, without historical percentage estimates. An offline desktop prototype does not close the installable-client phase.</p><a href="#methodology" id="score-methodology">Read the evidence & scoring method →</a></div></dialog>`;
}

export function bindControls(data, doc = document) {
  const byId = id => doc.getElementById(id);
  const refresh = () => {
    const results = selectCapabilities(data, { search: byId('cap-search').value, group: byId('cap-group').value, stage: byId('cap-stage').value, sort: byId('cap-sort').value });
    byId('capability-results').innerHTML = renderCapabilities(results);
    byId('cap-result-count').textContent = `Showing ${results.length} of ${data.capabilities.length} capabilities`;
  };
  byId('cap-search').addEventListener('input', refresh);
  for (const id of ['cap-group', 'cap-stage', 'cap-sort']) byId(id).addEventListener('change', refresh);
  byId('reset-filters').addEventListener('click', () => {
    for (const id of ['cap-search', 'cap-group', 'cap-stage']) byId(id).value = '';
    byId('cap-sort').value = 'source';
    refresh();
    byId('cap-search').focus();
  });
  doc.querySelectorAll('[data-phase-filter]').forEach(button => button.addEventListener('click', () => {
    const filter = button.dataset.phaseFilter;
    doc.querySelectorAll('[data-phase-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    byId('phase-results').innerHTML = renderPhases(data, filter);
    byId('phase-result-count').textContent = `Showing ${data.phases.filter(p => !filter || p.status === filter).length} of ${data.phases.length} phases`;
  }));
  const dialog = byId('score-dialog');
  byId('why-score').addEventListener('click', () => dialog.showModal());
  byId('close-score').addEventListener('click', () => dialog.close());
  byId('score-methodology').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
  if (typeof IntersectionObserver !== 'undefined') {
    const visible = new Map();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => visible.set(entry.target.id, entry.isIntersecting));
      const active = [...doc.querySelectorAll('main > section')].find(section => visible.get(section.id));
      if (active) doc.querySelectorAll('.nav-links a').forEach(a => a.getAttribute('href') === `#${active.id}` ? a.setAttribute('aria-current', 'location') : a.removeAttribute('aria-current'));
    }, { rootMargin: '-5% 0px -55% 0px', threshold: 0 });
    doc.querySelectorAll('main > section').forEach(section => observer.observe(section));
  }
}

async function start() {
  const app = document.getElementById('app');
  try {
    const response = await fetch('./data/status.json', { cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer' });
    if (!response.ok) throw new Error(`Snapshot request returned HTTP ${response.status}.`);
    const data = validateData(await response.json());
    app.innerHTML = renderDashboard(data);
    bindControls(data);
  } catch (error) {
    app.innerHTML = `<main id="main" class="error"><h1>Snapshot unavailable</h1><p>The verified data could not be loaded. No estimated or cached programme values are shown.</p><p>${e(error.message)}</p><p>Preview through a local HTTP server; see <a href="./README.md">README</a>. Correct the snapshot or connection and reload.</p></main>`;
  } finally { app.setAttribute('aria-busy', 'false'); }
}
if (typeof document !== 'undefined') start();
