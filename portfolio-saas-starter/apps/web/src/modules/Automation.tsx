import React, { useEffect, useState } from 'react';
import { createPlan, executePlan, dryRun, fetchPolicy } from '../services/automation.js';
import type { AutomationPlan, AutomationResult } from '@pkg/types';

export function AutomationDemo() {
  const [text, setText] = useState('ニュースサイトでAIを検索してタイトルを集めて');
  const [plan, setPlan] = useState<AutomationPlan | null>(null);
  const [result, setResult] = useState<AutomationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validation, setValidation] = useState<{ valid: boolean; issues: { level: 'error' | 'warn'; message: string; index?: number }[] } | null>(null);
  const [policy, setPolicy] = useState<{ allowedDomains: string[]; allowedActions: string[]; maxSteps: number; maxRunMs: number; notes?: string[] } | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { policy } = await fetchPolicy();
        setPolicy(policy);
      } catch (e) {
        // noop; optional
      }
    })();
  }, []);

  async function onPlan() {
    setError(null);
    setResult(null);
    try {
      const p = await createPlan(text);
      setPlan(p.plan);
      // immediately run dry-run validation
      try {
        const v = await dryRun(p.plan);
        setValidation(v);
      } catch (e: any) {
        setValidation({ valid: false, issues: [{ level: 'warn', message: e?.message || 'dry-run failed' }] });
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  }

  async function onExecute() {
    if (!plan) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const r = await executePlan(plan);
      setResult(r);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setRunning(false);
    }
  }

  async function onDemo() {
    setError(null);
    setResult(null);
    setValidation(null);
    try {
      // Use server-side demo plan for reproducibility
      const p = await createPlan('ニュースサイトでAIを検索してタイトルを集めて');
      setPlan(p.plan);
      const v = await dryRun(p.plan);
      setValidation(v);
      if (v.valid) {
        const r = await executePlan(p.plan);
        setResult(r);
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  }

  return (
    <div style={{ border: '1px solid #ddd', padding: 16, borderRadius: 8 }}>
      <h2>自動操作デモ（MVP）</h2>
      <p style={{ color: '#666' }}>音声の代わりにテキストで操作意図を入力 → プラン生成 → 実行（シミュレーション）</p>
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} style={{ width: '100%', padding: 8 }} />
      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
        <button onClick={onPlan}>プラン作成</button>
        <button onClick={onExecute} disabled={!plan || running || (validation && !validation.valid)}>
          {running ? '実行中...' : '実行'}
        </button>
        <button onClick={onDemo} style={{ marginLeft: 'auto' }}>ワンクリックデモ</button>
      </div>
      {policy && (
        <div style={{ marginTop: 10, padding: 8, background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6 }}>
          <div style={{ fontWeight: 600 }}>安全ポリシー</div>
          <div>許可ドメイン: {policy.allowedDomains.join(', ') || '-'}</div>
          <div>許可アクション: {policy.allowedActions.join(', ') || '-'}</div>
          <div>最大ステップ数: {policy.maxSteps}</div>
        </div>
      )}
      {error && <p style={{ color: 'crimson' }}>エラー: {error}</p>}
      {plan && (
        <div style={{ marginTop: 12 }}>
          <strong>プラン:</strong>
          <pre style={{ background: '#f7f7f7', padding: 8 }}>{JSON.stringify(plan, null, 2)}</pre>
        </div>
      )}
      {validation && (
        <div style={{ marginTop: 12 }}>
          <strong>ドライラン検証:</strong>
          <div style={{ padding: 8, borderRadius: 6, background: validation.valid ? '#effaf0' : '#fff4f4', border: '1px solid', borderColor: validation.valid ? '#b7eb8f' : '#ffccc7' }}>
            <div>結果: {validation.valid ? 'OK' : 'NG'}</div>
            {validation.issues?.length > 0 && (
              <ul>
                {validation.issues.map((i, idx) => (
                  <li key={idx} style={{ color: i.level === 'error' ? 'crimson' : '#b36b00' }}>
                    [{i.level}] {typeof i.index === 'number' && i.index >= 0 ? `step#${i.index}: ` : ''}{i.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
      {result && (
        <div style={{ marginTop: 12 }}>
          <strong>結果:</strong>
          <pre style={{ background: '#f7f7f7', padding: 8 }}>{JSON.stringify(result, null, 2)}</pre>
          {result.artifacts && result.artifacts.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div><strong>成果物:</strong></div>
              <ul>
                {result.artifacts.map((a, i) => (
                  <li key={i}>
                    <a href={a.url} target="_blank" rel="noreferrer">{a.name}</a>
                  </li>
                ))}
              </ul>
              {result.artifacts.some((a) => a.name.endsWith('.svg')) && (
                <div style={{ marginTop: 8, border: '1px solid #ddd', padding: 8 }}>
                  <div style={{ marginBottom: 4, color: '#555' }}>擬似スクリーンショット:</div>
                  {/* embed the first svg */}
                  {(() => {
                    const svg = result.artifacts!.find((a) => a.name.endsWith('.svg'));
                    return svg ? <img src={svg.url} alt="simulation" style={{ maxWidth: '100%' }} /> : null;
                  })()}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
