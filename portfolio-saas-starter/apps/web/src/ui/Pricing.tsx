import React from 'react';

async function createCheckout(priceId?: string) {
  const res = await fetch('/.netlify/functions/create-checkout-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      priceId: priceId || (import.meta as any)?.env?.VITE_STRIPE_PRICE_ID,
      success_url: window.location.origin + '/?status=success',
      cancel_url: window.location.origin + '/?status=cancel',
    }),
  });
  if (!res.ok) throw new Error('failed to create session');
  const data = await res.json();
  if (data?.url) {
    window.location.href = data.url;
  }
}

export function Pricing() {
  const price = (import.meta as any)?.env?.VITE_STRIPE_PRICE_ID || 'price_test';
  return (
    <div style={{ border: '1px solid #eee', padding: 16, borderRadius: 8 }}>
      <h2>購入</h2>
      <p style={{ color: '#555' }}>テスト決済のスタブです。公開前に必ず本番設定をご確認ください。</p>
      <button type="button" onClick={() => createCheckout(price)}>購入する</button>
    </div>
  );
}

