(() => {
  const $ = (id) => document.getElementById(id);
  const listEl = $('list');
  const detailEl = $('detail');
  const toastEl = $('toast');
  const searchEl = $('search');
  const ctaLP = $('cta-lp');

  // carry over query (variant/utm) to LP
  const params = new URLSearchParams(location.search);
  const q = params.toString();
  const lpHref = '../lp/index.html' + (q ? `?${q}` : '');
  if (ctaLP) ctaLP.href = lpHref;

  const dataDefault = [
    { id: 'task-001', title: 'レポート生成の自動化', desc: 'CSVから週次レポートを自動生成', value: '平均30分/週の削減' },
    { id: 'task-002', title: 'Slack通知の自動送信', desc: 'エラー検知で通知を即時配信', value: '検知〜対応までの遅延短縮' },
    { id: 'task-003', title: 'バックテスト一括実行', desc: '設定プリセットで一括実行', value: '属人作業の平準化' },
  ];
  let data = dataDefault;

  // Optional: fetch from static API when ?api=1
  if (params.get('api') === '1') {
    fetch('./api/items.json')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(json => { data = json.items || dataDefault; renderList(data); })
      .catch(() => { renderList(dataDefault); });
  }

  function renderList(items) {
    listEl.innerHTML = '';
    items.forEach((it) => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${it.title}</strong><br/><span style="color:#a5b1d8">${it.desc}</span>`;
      li.addEventListener('click', () => showDetail(it));
      listEl.appendChild(li);
    });
  }

  function showDetail(it) {
    detailEl.innerHTML = '';
    const h2 = document.createElement('h2');
    h2.textContent = it.title;
    const p = document.createElement('p');
    p.textContent = it.desc;
    const value = document.createElement('p');
    value.style.color = '#a5b1d8';
    value.textContent = `期待できる価値: ${it.value}`;
    const actions = document.createElement('div');
    actions.className = 'actions';
    const run = document.createElement('button');
    run.className = 'btn';
    run.textContent = '実行（モック）';
    run.addEventListener('click', () => simulateRun(it));
    const consult = document.createElement('a');
    consult.className = 'btn';
    consult.href = lpHref;
    consult.textContent = '無料相談';
    actions.append(run, consult);
    detailEl.append(h2, p, value, actions);
  }

  function simulateRun(it) {
    // simple success/failure mock
    const ok = Math.random() > 0.25;
    const msg = ok ? `${it.title}: 成功しました` : `${it.title}: 失敗しました（再試行してください）`;
    showToast(msg, ok);
    if (ok) showSuccessBanner();
  }

  let toastTimer;
  function showToast(text, success) {
    toastEl.textContent = text;
    toastEl.style.borderColor = success ? '#2dd4bf' : '#f87171';
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.hidden = true; }, 2500);
  }

  searchEl.addEventListener('input', () => {
    const s = searchEl.value.trim().toLowerCase();
    renderList(
      s ? data.filter(d => (d.title + d.desc).toLowerCase().includes(s)) : data
    );
  });

  renderList(data);

  function showSuccessBanner() {
    // add a lightweight banner under header once
    if (document.getElementById('success-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'success-banner';
    banner.style.background = '#0e1a3a';
    banner.style.borderBottom = '1px solid #1f2752';
    banner.style.padding = '8px 16px';
    banner.innerHTML = `✅ 体験に成功しました。導入可否の無料診断をご希望の場合は <a class="btn" href="${lpHref}">こちら</a>`;
    document.body.insertBefore(banner, document.body.firstChild.nextSibling);
  }
})();
