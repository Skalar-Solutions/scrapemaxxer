const els = {
  urls: document.getElementById('urls'),
  modeSegmented: document.getElementById('modeSegmented'),
  selectorField: document.getElementById('selectorField'),
  selectorLabel: document.getElementById('selectorLabel'),
  modeValue: document.getElementById('modeValue'),
  contains: document.getElementById('contains'),
  exclude: document.getElementById('exclude'),
  regex: document.getElementById('regex'),
  limit: document.getElementById('limit'),
  stealth: document.getElementById('stealth'),
  commandText: document.getElementById('commandText'),
  runBtn: document.getElementById('runBtn'),
  results: document.getElementById('results'),
  summaryLine: document.getElementById('summaryLine'),
};

let mode = 'auto';

function firstUrlOrPlaceholder() {
  const raw = els.urls.value.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
  if (raw.length === 0) return 'example.com';
  if (raw.length === 1) return raw[0];
  return `${raw[0]}  (+${raw.length - 1} more)`;
}

function buildCommand() {
  const parts = ['scrap', firstUrlOrPlaceholder()];

  if (mode === 'css' && els.modeValue.value.trim()) {
    parts.push('--css', `"${els.modeValue.value.trim()}"`);
  } else if (mode === 'xpath' && els.modeValue.value.trim()) {
    parts.push('--xpath', `"${els.modeValue.value.trim()}"`);
  } else if (mode !== 'auto') {
    parts.push(`--${mode}`);
  }

  if (els.contains.value.trim()) parts.push('--contains', els.contains.value.trim());
  if (els.exclude.value.trim()) parts.push('--exclude', els.exclude.value.trim());
  if (els.regex.value.trim()) parts.push('--regex', `"${els.regex.value.trim()}"`);
  if (els.limit.value && Number(els.limit.value) > 0) parts.push('--limit', els.limit.value);
  if (els.stealth.checked) parts.push('--stealth');

  els.commandText.textContent = parts.join(' ');
}

function setMode(newMode) {
  mode = newMode;
  [...els.modeSegmented.querySelectorAll('button')].forEach(b => {
    b.classList.toggle('active', b.dataset.mode === newMode);
  });
  const needsSelector = newMode === 'css' || newMode === 'xpath';
  els.selectorField.hidden = !needsSelector;
  if (needsSelector) {
    els.selectorLabel.textContent = newMode;
    els.modeValue.placeholder = newMode === 'css' ? 'h2.title::text' : '//h2[@class="title"]/text()';
  }
  buildCommand();
}

els.modeSegmented.addEventListener('click', e => {
  const btn = e.target.closest('button[data-mode]');
  if (btn) setMode(btn.dataset.mode);
});

['urls', 'modeValue', 'contains', 'exclude', 'regex', 'limit'].forEach(id => {
  document.getElementById(id).addEventListener('input', buildCommand);
});
els.stealth.addEventListener('change', buildCommand);

function statusClass(status, error) {
  if (error) return 'status-err';
  if (!status) return 'status-err';
  if (status < 300) return 'status-2xx';
  if (status < 500) return 'status-4xx';
  return 'status-5xx';
}

function renderJob(job) {
  const wrap = document.createElement('div');
  wrap.className = 'job';

  const head = document.createElement('div');
  head.className = 'job-head';

  const badge = document.createElement('span');
  badge.className = `status-badge ${statusClass(job.status, job.error)}`;
  badge.textContent = job.error ? 'ERR' : job.status;
  head.appendChild(badge);

  const urlSpan = document.createElement('span');
  urlSpan.className = 'job-url';
  urlSpan.textContent = job.url;
  head.appendChild(urlSpan);

  if (job.mode) {
    const modeSpan = document.createElement('span');
    modeSpan.className = 'job-mode';
    modeSpan.textContent = job.mode;
    head.appendChild(modeSpan);
  }

  wrap.appendChild(head);

  const body = document.createElement('div');
  body.className = 'job-body';

  if (job.error) {
    const errDiv = document.createElement('div');
    errDiv.className = 'job-error';
    errDiv.textContent = job.error;
    body.appendChild(errDiv);
  } else if (!job.results || job.results.length === 0) {
    const emptyDiv = document.createElement('div');
    emptyDiv.className = 'job-empty';
    emptyDiv.textContent = 'No results matched your filters.';
    body.appendChild(emptyDiv);
  } else {
    const table = document.createElement('table');
    job.results.forEach((r, i) => {
      const tr = document.createElement('tr');

      const idxTd = document.createElement('td');
      idxTd.className = 'idx';
      idxTd.textContent = i + 1;
      tr.appendChild(idxTd);

      const valTd = document.createElement('td');
      valTd.className = 'val';
      valTd.textContent = r.value || '—';
      tr.appendChild(valTd);

      if (r.href) {
        const linkTd = document.createElement('td');
        linkTd.className = 'link';
        const a = document.createElement('a');
        a.href = r.href;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = r.href;
        linkTd.appendChild(a);
        tr.appendChild(linkTd);
      }

      table.appendChild(tr);
    });
    body.appendChild(table);
  }

  wrap.appendChild(body);
  return wrap;
}

async function runScrape() {
  const urls = els.urls.value.trim();
  if (!urls) {
    els.urls.focus();
    return;
  }

  els.runBtn.disabled = true;
  els.runBtn.innerHTML = 'Running&hellip;';
  els.results.innerHTML = '<div class="empty-state">Fetching&hellip;</div>';
  els.summaryLine.textContent = '';

  const payload = {
    urls,
    mode,
    mode_value: els.modeValue.value.trim(),
    contains: els.contains.value.trim(),
    exclude: els.exclude.value.trim(),
    regex: els.regex.value.trim(),
    limit: els.limit.value,
    stealth: els.stealth.checked,
  };

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      els.results.innerHTML = `<div class="job-error" style="padding:12px;">${data.error || 'Request failed.'}</div>`;
      return;
    }

    els.results.innerHTML = '';
    data.jobs.forEach(job => els.results.appendChild(renderJob(job)));

    const totalResults = data.jobs.reduce((sum, j) => sum + (j.results ? j.results.length : 0), 0);
    els.summaryLine.textContent = `${data.jobs.length} url(s), ${totalResults} result(s)`;
  } catch (err) {
    els.results.innerHTML = `<div class="job-error" style="padding:12px;">${err}</div>`;
  } finally {
    els.runBtn.disabled = false;
    els.runBtn.innerHTML = 'Run <span class="key">&#9166;</span>';
  }
}

els.runBtn.addEventListener('click', runScrape);
els.urls.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') runScrape();
});

buildCommand();
