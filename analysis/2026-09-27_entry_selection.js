/* The full evidence table is present even with JavaScript disabled. */
(() => {
  const search = document.getElementById('trade-search');
  const view = document.getElementById('trade-view');
  const count = document.getElementById('trade-count');
  const rows = [...document.querySelectorAll('#skipped-table tbody tr')];
  function filterRows() {
    const query = search.value.trim().toUpperCase();
    let shown = 0;
    for (const row of rows) {
      const matchesSearch = row.dataset.search.toUpperCase().includes(query);
      const mode = view.value;
      const matchesView = mode === 'all'
        || (mode === 'band5' && row.dataset.band5 === 'taken')
        || (mode === 'band4' && row.dataset.band4 === 'taken')
        || (mode === 'positive' && row.dataset.positive === 'true')
        || (mode === 'negative' && row.dataset.positive === 'false');
      row.hidden = !(matchesSearch && matchesView);
      if (!row.hidden) shown++;
    }
    count.textContent = `${shown} of ${rows.length} skipped trades shown.`;
  }
  search.addEventListener('input', filterRows);
  view.addEventListener('change', filterRows);
})();
