import React, { useMemo, useState } from 'react';

export function Cta() {
  const demoUrl = (import.meta as any)?.env?.VITE_DEMO_URL || '/demo.svg';
  const contactEmail = (import.meta as any)?.env?.VITE_CONTACT_EMAIL || 'example@example.com';
  const [msg, setMsg] = useState('');
  const mailto = useMemo(() => {
    const subject = encodeURIComponent('デモ/お問い合わせ');
    const body = encodeURIComponent(msg || 'デモの案内を希望します。');
    return `mailto:${contactEmail}?subject=${subject}&body=${body}`;
  }, [contactEmail, msg]);

  return (
    <div style={{ border: '1px solid #eee', padding: 16, borderRadius: 8 }}>
      <h2>まずはデモを見る</h2>
      <p style={{ color: '#555' }}>20秒のショートデモで雰囲気を確認できます。</p>
      <div style={{ display: 'flex', gap: 8 }}>
        <a href={demoUrl} target="_blank" rel="noreferrer">
          <button type="button">デモを見る</button>
        </a>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>お問い合わせ</h3>
        <p style={{ marginTop: 0, color: '#555' }}>ご質問やご相談はこちらへ。</p>
        <textarea
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          placeholder="お問い合わせ内容を簡潔にご記入ください"
          rows={3}
          style={{ width: '100%', padding: 8 }}
        />
        <div style={{ marginTop: 8 }}>
          <a href={mailto}>
            <button type="button">メールで送る</button>
          </a>
        </div>
      </div>
    </div>
  );
}
