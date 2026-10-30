/* Stonegrove Hub explorer. Static; reads data/manifest.json and renders a
   SharePoint-style document estate with downloads at estate, site, library
   and folder level, a preview drawer, search, and a hints overlay. */

(function () {
  'use strict';

  const state = {
    manifest: null,
    filesByFolder: new Map(),
    foldersByParent: new Map(),
    fileByPath: new Map(),
    downloads: null,
    hints: false,
    route: { site: null, library: null, folder: '', file: null, q: '' },
  };

  const $ = (sel, el = document) => el.querySelector(sel);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const encPath = (p) => p.split('/').map(encodeURIComponent).join('/');
  const fmtSize = (n) => n == null ? '' : n < 1024 ? n + ' B' : n < 1048576 ? (n / 1024).toFixed(n < 10240 ? 1 : 0) + ' KB' : (n / 1048576).toFixed(1) + ' MB';

  // ------------------------------------------------------------ data
  async function load() {
    const res = await fetch('data/manifest.json', { cache: 'no-cache' });
    state.manifest = await res.json();
    try {
      const d = await fetch('downloads/index.json', { cache: 'no-cache' });
      if (d.ok) state.downloads = await d.json();
    } catch (e) { /* no zips yet */ }
    index();
    try { state.hints = localStorage.getItem('hub-hints') === '1'; } catch (e) { /* ignore */ }
    $('#hints').checked = state.hints;
    document.body.classList.toggle('hints-on', state.hints);
    renderNav();
    window.addEventListener('hashchange', route);
    route();
  }

  function index() {
    const m = state.manifest;
    for (const f of m.files) {
      state.fileByPath.set(f.path, f);
      const folder = f.folder || '';
      if (!state.filesByFolder.has(folder)) state.filesByFolder.set(folder, []);
      state.filesByFolder.get(folder).push(f);
    }
    for (const fo of m.folders) {
      const parent = fo.path.includes('/') ? fo.path.slice(0, fo.path.lastIndexOf('/')) : '';
      if (!state.foldersByParent.has(parent)) state.foldersByParent.set(parent, []);
      state.foldersByParent.get(parent).push(fo);
    }
    for (const arr of state.filesByFolder.values()) arr.sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));
    for (const arr of state.foldersByParent.values()) arr.sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));
  }

  const siteById = (id) => state.manifest.sites.find((s) => s.id === id);
  const libById = (site, id) => site && site.libraries.find((l) => l.id === id);
  const siteByFolder = (name) => state.manifest.sites.find((s) => s.folder === name);

  function countUnder(prefix) {
    let n = 0, bytes = 0;
    for (const f of state.manifest.files) {
      if (prefix === '' || f.path === prefix || f.path.startsWith(prefix + '/')) { n++; bytes += f.size || 0; }
    }
    return { n, bytes };
  }

  // ------------------------------------------------------------ routing
  function parseHash() {
    const h = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
    const r = { site: null, library: null, folder: '', file: null, q: '' };
    if (!h) return r;
    if (h.startsWith('search=')) { r.q = h.slice(7); return r; }
    if (h.startsWith('file=')) { r.file = h.slice(5); const f = state.fileByPath.get(r.file); if (f) { r.site = f.site; r.library = f.library; r.folder = f.folder; } return r; }
    const parts = h.split('/');
    r.site = parts[0] || null;
    r.library = parts[1] || null;
    const site = siteById(r.site), lib = libById(site, r.library);
    if (site && lib) r.folder = [site.folder, lib.folder].concat(parts.slice(2)).join('/');
    else if (site) r.folder = site.folder;
    return r;
  }

  function go(site, library, sub) {
    let h = '#/' + (site || '');
    if (library) h += '/' + library;
    if (sub) h += '/' + sub.split('/').map(encodeURIComponent).join('/');
    location.hash = h;
  }

  function route() {
    state.route = parseHash();
    renderNav();
    if (state.route.q) renderSearch(state.route.q);
    else if (!state.route.site) renderOverview();
    else renderFolder();
    if (state.route.file) openPreview(state.route.file); else closePreview();
    $('#nav').classList.remove('open');
  }

  // ------------------------------------------------------------ nav
  function renderNav() {
    const m = state.manifest, r = state.route;
    let html = '<h2>Sites</h2>';
    html += `<a href="#/" class="${!r.site && !r.q ? 'active' : ''}">Hub home</a>`;
    for (const s of m.sites) {
      const active = r.site === s.id;
      html += `<a href="#/${s.id}" class="${active && !r.library ? 'active' : ''}">${esc(s.name)}</a>`;
      if (active) {
        html += '<div class="libs">';
        for (const l of s.libraries) html += `<a href="#/${s.id}/${l.id}" class="${r.library === l.id ? 'active' : ''}">${esc(l.name)}</a>`;
        html += '</div>';
      }
    }
    html += `<div class="nav-foot">Snapshot ${esc(m.snapshot_display)}. ${m.counts.files} files. Everything here is synthetic. <a href="guide.html">Learner Guide</a></div>`;
    $('#nav').innerHTML = html;
  }

  // ------------------------------------------------------------ views
  function crumbs(parts) {
    return '<div class="crumbs">' + parts.map((p, i) => (i ? '<span class="sep">›</span>' : '') + (p.href ? `<a href="${p.href}">${esc(p.text)}</a>` : `<span>${esc(p.text)}</span>`)).join('') + '</div>';
  }

  function downloadButtons(opts) {
    const b = [];
    if (opts.estate && state.downloads) b.push(`<a class="btn primary" href="downloads/${esc(state.downloads.estate)}" download>Download everything</a>`);
    if (opts.siteId && state.downloads && state.downloads.sites[opts.siteId]) b.push(`<a class="btn" href="downloads/${esc(state.downloads.sites[opts.siteId])}" download>Download this site</a>`);
    if (opts.folder != null) b.push(`<button class="btn" data-zip="${esc(opts.folder)}" title="Built in your browser from the files in this folder">Download this ${esc(opts.folderKind || 'folder')}</button>`);
    return `<div class="actions">${b.join('')}</div>`;
  }

  function hintBlock(text, skills) {
    if (!text) return '';
    const sk = skills && skills.length ? `<div class="skills">Skills: ${skills.map((n) => `<a href="guide.html#skill-${n}">${n}</a>`).join(', ')}</div>` : '';
    return `<div class="hint"><strong>Hint.</strong> ${esc(text)}${sk}</div>`;
  }

  function renderOverview() {
    const m = state.manifest;
    const c = countUnder('');
    let html = crumbs([{ text: 'Stonegrove Hub' }]);
    html += `<div class="head"><div><h1>Stonegrove Hub</h1><p class="desc">${esc(m.institution.name)} staff intranet. Snapshot taken ${esc(m.snapshot_display)}. ${c.n} documents in ${m.sites.length} sites.</p></div>${downloadButtons({ estate: true })}</div>`;
    html += `<div class="hint"><strong>Hints are on.</strong> Yellow boxes like this one appear on sites and libraries to say what the team there is wrestling with and what you might try. Turn them off in the top bar for the plain intranet. Nothing inside the downloads carries these notes. The <a href="guide.html">Learner Guide</a> has the exercises.</div>`;
    html += '<div class="sites-grid">';
    for (const s of m.sites) {
      const sc = countUnder(s.folder);
      html += `<a class="site-card" href="#/${s.id}"><h3>${esc(s.name)}</h3><p>${esc(s.description)}</p><div class="count">${sc.n} files · ${s.libraries.length} libraries · ${esc(s.owner_name)}</div></a>`;
    }
    html += '</div>';
    $('#main').innerHTML = html;
  }

  function renderFolder() {
    const r = state.route;
    const site = siteById(r.site);
    if (!site) { $('#main').innerHTML = '<div class="empty">No such site.</div>'; return; }
    const lib = libById(site, r.library);
    const folder = r.folder;
    const parts = folder.split('/');
    const sub = lib ? parts.slice(2) : [];

    const crumbParts = [{ text: 'Stonegrove Hub', href: '#/' }, { text: site.name, href: lib ? `#/${site.id}` : null }];
    if (lib) {
      crumbParts.push({ text: lib.name, href: sub.length ? `#/${site.id}/${lib.id}` : null });
      sub.forEach((p, i) => crumbParts.push({ text: p, href: i < sub.length - 1 ? `#/${site.id}/${lib.id}/` + sub.slice(0, i + 1).map(encodeURIComponent).join('/') : null }));
    }
    let html = crumbs(crumbParts);

    const title = sub.length ? sub[sub.length - 1] : lib ? lib.name : site.name;
    const desc = lib ? '' : site.description;
    const c = countUnder(folder);
    html += `<div class="head"><div><h1>${esc(title)}</h1>${desc ? `<p class="desc">${esc(desc)}</p>` : ''}<div class="owner">${lib ? `Library in ${esc(site.name)}. Default label: ${esc(lib.default_label || 'none')}. ` : `Site owner: ${esc(site.owner_name)}, ${esc(site.owner_title)}. `}${c.n} files, ${fmtSize(c.bytes)}.</div></div>${downloadButtons({ siteId: !lib ? site.id : null, folder: folder, folderKind: lib ? (sub.length ? 'folder' : 'library') : null })}</div>`;
    if (!lib) html += hintBlock(site.hint, site.skills);
    else if (!sub.length && lib.hint) html += hintBlock(lib.hint, []);

    // libraries as folders at site level; subfolders and files otherwise
    const rows = [];
    if (!lib) {
      for (const l of site.libraries) {
        const lc = countUnder(site.folder + '/' + l.folder);
        rows.push(rowFolder(l.name, `#/${site.id}/${l.id}`, lc.n, l.default_label));
      }
    } else {
      for (const fo of state.foldersByParent.get(folder) || []) {
        const fc = countUnder(fo.path);
        rows.push(rowFolder(fo.name, `#/${site.id}/${lib.id}/` + fo.path.split('/').slice(2).map(encodeURIComponent).join('/'), fc.n, null));
      }
      for (const f of state.filesByFolder.get(folder) || []) rows.push(rowFile(f));
    }
    html += `<div class="library"><div class="table-wrap"><table class="files"><thead><tr><th>Name</th><th>Modified</th><th>Modified by</th><th>Label</th><th style="text-align:right">Size</th></tr></thead><tbody>${rows.join('') || '<tr><td colspan="5" class="empty">This folder is empty.</td></tr>'}</tbody></table></div></div>`;
    $('#main').innerHTML = html;
    bindRows();
  }

  function rowFolder(name, href, count, label) {
    return `<tr class="row" data-href="${esc(href)}"><td class="name"><div class="n"><span class="icon folder">▸</span><span class="t">${esc(name)}</span></div></td><td class="muted nowrap"></td><td class="muted">${count} item${count === 1 ? '' : 's'}</td><td>${label ? `<span class="label ${esc(label)}">${esc(label)}</span>` : ''}</td><td class="num"></td></tr>`;
  }

  function rowFile(f) {
    const sel = state.route.file === f.path ? ' selected' : '';
    return `<tr class="row${sel}" data-file="${esc(f.path)}"><td class="name"><div class="n"><span class="icon ${esc(f.ext)}">${esc(f.ext.slice(0, 4))}</span><span class="t" title="${esc(f.name)}">${esc(f.name)}</span></div></td><td class="nowrap">${esc(f.modified_display)}</td><td>${esc(f.modified_by)}</td><td>${labelPill(f.label)}</td><td class="num">${fmtSize(f.size)}</td></tr>`;
  }

  const labelPill = (l) => l ? `<span class="label ${esc(l)}">${esc(l)}</span>` : '<span class="label none">No label</span>';

  function bindRows() {
    for (const tr of document.querySelectorAll('tr.row')) {
      tr.addEventListener('click', () => {
        if (tr.dataset.href) location.hash = tr.dataset.href;
        else if (tr.dataset.file) location.hash = '#/file=' + encodeURIComponent(tr.dataset.file);
      });
    }
    for (const b of document.querySelectorAll('button[data-zip]')) b.addEventListener('click', () => zipFolder(b.dataset.zip, b));
  }

  function renderSearch(q) {
    const needle = q.toLowerCase();
    const hits = state.manifest.files.filter((f) => f.name.toLowerCase().includes(needle) || (f.title || '').toLowerCase().includes(needle)).slice(0, 200);
    let html = crumbs([{ text: 'Stonegrove Hub', href: '#/' }, { text: `Search: ${q}` }]);
    html += `<div class="results"><h1>${hits.length} result${hits.length === 1 ? '' : 's'} for "${esc(q)}"</h1></div>`;
    html += `<div class="library"><div class="table-wrap"><table class="files"><thead><tr><th>Name</th><th>Modified</th><th>Modified by</th><th>Label</th><th style="text-align:right">Size</th></tr></thead><tbody>`;
    for (const f of hits) {
      html += rowFile(f).replace('</span></div></td>', `</span></div><div class="path">${esc(f.folder)}</div></td>`);
    }
    html += `${hits.length ? '' : '<tr><td colspan="5" class="empty">Nothing matched. Search looks at file names only, as the real thing mostly does.</td></tr>'}</tbody></table></div></div>`;
    $('#main').innerHTML = html;
    bindRows();
  }

  // ------------------------------------------------------------ preview
  async function openPreview(path) {
    const f = state.fileByPath.get(path);
    const d = $('#drawer');
    if (!f) { closePreview(); return; }
    $('#drawer-title').textContent = f.name;
    $('#drawer-meta').innerHTML = [
      ['Title', f.title], ['Author', f.author], ['Modified', f.modified_display + (f.modified_by && f.modified_by !== f.author ? ` by ${f.modified_by}` : '')],
      ['Created', f.created], ['Label', f.label || 'No label'], ['Location', f.folder], ['Size', fmtSize(f.size)],
    ].map(([k, v]) => `<dt>${esc(k)}</dt><dd>${k === 'Label' ? labelPill(f.label) : esc(v)}</dd>`).join('');
    $('#drawer-dl').innerHTML = `<a class="btn primary" href="estate/${encPath(f.path)}" download="${esc(f.name)}">Download file</a><a class="btn" href="estate/${encPath(f.path)}" target="_blank" rel="noopener">Open</a>`;
    const body = $('#drawer-body');
    body.innerHTML = '<p class="muted">Loading preview…</p>';
    d.classList.add('open');
    if (f.ext === 'png' || f.ext === 'jpg') {
      body.innerHTML = `<img src="estate/${encPath(f.path)}" alt="${esc(f.name)}">`;
      return;
    }
    if (!f.preview) { body.innerHTML = `<p class="nopreview">No preview for this file type. Download it to open in the usual application.</p>`; return; }
    try {
      const res = await fetch(f.preview);
      const text = await res.text();
      body.innerHTML = (f.ext === 'vtt' || f.ext === 'eml' || f.ext === 'csv' || f.ext === 'txt') ? `<pre>${esc(text)}</pre>` : miniMarkdown(text);
      body.insertAdjacentHTML('afterbegin', `<p class="muted" style="font-size:12.5px;margin:0 0 10px">Text preview. The downloaded ${esc(f.ext)} is the real document.</p>`);
    } catch (e) { body.innerHTML = '<p class="nopreview">Preview unavailable.</p>'; }
    for (const tr of document.querySelectorAll('tr.row')) tr.classList.toggle('selected', tr.dataset.file === path);
  }

  function closePreview() { $('#drawer').classList.remove('open'); }

  function miniMarkdown(src) {
    const lines = src.replace(/^---[\s\S]*?\n---\n/, '').split('\n');
    let out = '', i = 0;
    const inline = (s) => esc(s).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/`([^`]+)`/g, '<code>$1</code>');
    while (i < lines.length) {
      const l = lines[i];
      if (/^:::/.test(l) || !l.trim()) { i++; continue; }
      if (/^```/.test(l)) { let j = i + 1, code = []; while (j < lines.length && !/^```/.test(lines[j])) code.push(lines[j++]); out += `<pre>${esc(code.join('\n'))}</pre>`; i = j + 1; continue; }
      const h = /^(#{1,6})\s+(.*)/.exec(l);
      if (h) { out += `<h${Math.min(h[1].length, 3)}>${inline(h[2])}</h${Math.min(h[1].length, 3)}>`; i++; continue; }
      if (/^\|/.test(l)) {
        const rows = [];
        while (i < lines.length && /^\|/.test(lines[i])) { const cells = lines[i].trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim()); if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells); i++; }
        out += '<table>' + rows.map((r, ri) => '<tr>' + r.map((c) => `<${ri ? 'td' : 'th'}>${inline(c)}</${ri ? 'td' : 'th'}>`).join('') + '</tr>').join('') + '</table>';
        continue;
      }
      if (/^\s*[-*]\s+/.test(l)) { let items = []; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*[-*]\s+/, '')); out += '<ul>' + items.map((x) => `<li>${inline(x)}</li>`).join('') + '</ul>'; continue; }
      if (/^\s*\d+[.)]\s+/.test(l)) { let items = []; while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*\d+[.)]\s+/, '')); out += '<ol>' + items.map((x) => `<li>${inline(x)}</li>`).join('') + '</ol>'; continue; }
      if (/^(-{3,}|\*{3,})$/.test(l.trim())) { out += '<hr>'; i++; continue; }
      let para = [l]; i++;
      while (i < lines.length && lines[i].trim() && !/^(#|\||```|:::|\s*[-*]\s|\s*\d+[.)]\s)/.test(lines[i])) para.push(lines[i++]);
      out += `<p>${inline(para.join(' '))}</p>`;
    }
    return out;
  }

  // ------------------------------------------------------------ client-side folder zips
  async function zipFolder(folder, btn) {
    if (!window.JSZip) { alert('Zip library did not load. Use the site download instead.'); return; }
    const files = state.manifest.files.filter((f) => folder === '' || f.path === folder || f.path.startsWith(folder + '/'));
    const folders = state.manifest.folders.filter((fo) => folder === '' || fo.path === folder || fo.path.startsWith(folder + '/'));
    if (!files.length && !folders.length) return;
    const label = btn.textContent;
    btn.disabled = true;
    const zip = new JSZip();
    const root = 'stonegrove-hub/' + folder + (folder ? '/' : '');
    zip.file('stonegrove-hub/README.txt', `Stonegrove Hub, partial download: ${folder || 'everything'}.\r\nSnapshot ${state.manifest.snapshot_display}. Everything in this archive is synthetic. See the Stonegrove University project site for licence and guide.\r\n`);
    for (const fo of folders) zip.folder(root + fo.path.slice(folder ? folder.length + 1 : 0));
    let done = 0;
    for (const f of files) {
      btn.textContent = `Preparing… ${++done}/${files.length}`;
      const res = await fetch('estate/' + encPath(f.path));
      const blob = await res.blob();
      const rel = f.path.slice(folder ? folder.length + 1 : 0);
      const d = new Date(f.modified.replace(/^(\d{4})/, (y) => String(+y + 973)));
      zip.file(root + rel, blob, { date: isNaN(d) ? undefined : d });
    }
    const out = await zip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
    const name = 'stonegrove-hub-' + (folder ? folder.split('/').pop() : 'all').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '.zip';
    const a = document.createElement('a');
    a.href = URL.createObjectURL(out); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
    btn.disabled = false; btn.textContent = label;
  }

  // ------------------------------------------------------------ wiring
  document.addEventListener('DOMContentLoaded', () => {
    $('#hints').addEventListener('change', (e) => {
      state.hints = e.target.checked;
      document.body.classList.toggle('hints-on', state.hints);
      try { localStorage.setItem('hub-hints', state.hints ? '1' : '0'); } catch (err) { /* ignore */ }
    });
    $('#q').addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.value.trim()) location.hash = '#/search=' + encodeURIComponent(e.target.value.trim()); });
    $('#drawer-close').addEventListener('click', () => { const r = state.route; if (r.site) go(r.site, r.library, r.folder.split('/').slice(2).join('/')); else location.hash = '#/'; });
    $('#menu').addEventListener('click', () => $('#nav').classList.toggle('open'));
    load().catch((e) => { $('#main').innerHTML = `<div class="empty">Could not load the Hub manifest. ${esc(e.message)}</div>`; });
  });
})();
