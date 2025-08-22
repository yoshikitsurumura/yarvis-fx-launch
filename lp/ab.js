(() => {
  const params = new URLSearchParams(location.search);
  // variant: クエリ優先 → localStorage → ランダム
  const saved = localStorage.getItem('lp_variant');
  const queryV = params.get('v');
  const variant = (queryV || saved || (Math.random() < 0.5 ? 'v1' : 'v2'));
  try { localStorage.setItem('lp_variant', variant); } catch (e) {}
  const utmSource = params.get('utm_source') || 'lp';
  const utmMedium = params.get('utm_medium') || 'web';
  const utmCampaign = params.get('utm_campaign') || 'launch';
  const embed = params.get('embed') === '1';

  // Variant text
  const variants = {
    v1: {
      title: '手作業を自動化し、工数を大幅削減',
      sub: '最短2週間で導入。要件整理から運用まで伴走します。',
      cta: '無料で相談する',
    },
    v2: {
      title: '売上に直結する自動化で、成長を加速',
      sub: '2週間で立ち上げ。KPIに連動した成果設計。',
      cta: '導入可否を2分で診断',
    }
  };

  const v = variants[variant] || variants.v1;
  const $ = (id) => document.getElementById(id);
  const heroTitle = $('hero-title');
  const heroSub = $('hero-sub');
  const ctaMain = $('cta-main');
  const ctaTop = $('cta-top');
  const ctaForm = $('cta-form');
  const yearSpan = $('year');
  const diagBtn = $('apply-diagnosis');
  const formEmbed = document.getElementById('form-embed');
  const q1 = document.getElementById('q1');
  const q2 = document.getElementById('q2');
  const q3 = document.getElementById('q3');

  if (heroTitle) heroTitle.textContent = v.title;
  if (heroSub) heroSub.textContent = v.sub;
  if (ctaMain) ctaMain.textContent = v.cta;
  if (ctaTop) ctaTop.textContent = v.cta;
  if (yearSpan) yearSpan.textContent = new Date().getFullYear();

  // Configure CTA URL for Google Form (replace FORM_URL)
  const FORM_URL = (typeof window !== 'undefined' && window.LP_FORM_URL) || 'https://example.com/form'; // TODO: 差し替えてください（GoogleフォームURL）
  const FORM_CONFIGURED = FORM_URL && !/example\.com\/form$/.test(FORM_URL);

  function buildFormUrl() {
    const u = new URL(FORM_URL);
    u.searchParams.set('utm_source', utmSource);
    u.searchParams.set('utm_medium', utmMedium);
    u.searchParams.set('utm_campaign', utmCampaign);
    u.searchParams.set('variant', variant);
    // append diagnosis note (if any)
    const ans = [q1?.value, q2?.value, q3?.value].filter(Boolean);
    if (ans.length) {
      u.searchParams.set('note', `診断:${ans.join('/')}`);
    }
    return u.toString();
  }

  function onClickCTA(e) {
    e.preventDefault();
    if (!FORM_CONFIGURED) {
      alert('フォームURLが未設定です。lp/config.js を作成し、URLを書き換えてください。');
      return;
    }
    const url = buildFormUrl();
    try { window.__lp_last_cta = url; } catch (_) {}
    // Open in same tab for mobile-friendliness
    location.href = url;
  }

  ctaMain?.addEventListener('click', onClickCTA);
  ctaTop?.addEventListener('click', onClickCTA);
  ctaForm?.addEventListener('click', onClickCTA);

  // Diagnosis apply
  diagBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    const url = buildFormUrl();
    location.href = url;
  });

  // Embed mode
  if (embed && formEmbed) {
    if (!FORM_CONFIGURED) {
      const warn = document.createElement('div');
      warn.style.margin = '8px 0';
      warn.style.color = '#f97316';
      warn.textContent = 'フォームURLが未設定のため、埋め込みを表示できません（lp/config.js を設定してください）';
      formEmbed.before(warn);
    }
    formEmbed.hidden = false;
    const iframe = document.createElement('iframe');
    const u = new URL(buildFormUrl());
    u.searchParams.set('embedded', 'true');
    iframe.src = u.toString();
    iframe.width = '100%';
    iframe.height = '900';
    iframe.frameBorder = '0';
    iframe.loading = 'lazy';
    formEmbed.appendChild(iframe);
  }
})();
