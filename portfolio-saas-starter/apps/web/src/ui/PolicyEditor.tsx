import React, { useEffect, useMemo, useState } from 'react';
import { fetchPolicy, savePolicy } from '../services/automation.js';

type Policy = { allowedDomains: string[]; allowedActions: string[]; maxSteps: number; maxRunMs: number; notes?: string[] };

export function PolicyEditor() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  const domainsText = useMemo(() => (policy?.allowedDomains || []).join('\n'), [policy]);
  const actionsText = useMemo(() => (policy?.allowedActions || []).join('\n'), [policy]);

  useEffect(() => {
    (async () => {
      try {
        const { policy } = await fetchPolicy();
        setPolicy(policy);
      } catch (e) {
        // noop
      }
    })();
  }, []);

  async function onSave() {
    if (!policy) return;
    setSaving(true);
    setError(null);
    setOk(false);
    try {
      const input: Partial<Policy> = {
        allowedDomains: domainsText
          .split(/\n+/)
          .map((s) => s.trim())
          .filter(Boolean),
        allowedActions: actionsText
          .split(/\n+/)
          .map((s) => s.trim())
          .filter(Boolean),
        maxSteps: Number(policy.maxSteps) || 0,
        maxRunMs: Number(policy.maxRunMs) || 0,
      };
      const res = await savePolicy(input);
      setPolicy(res.policy);
      setOk(true);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setSaving(false);
      setTimeout(() => setOk(false), 2500);
    }
  }

  if (!policy) return <div style={{ border: '1px solid #eee', padding: 16, borderRadius: 8 }}>ポリシーを読み込み中...</div>;

  return (
    <div style={{ border: '1px solid #eee', padding: 16, borderRadius: 8 }}>
      <h2>ポリシー編集</h2>
      <p style={{ color: '#555' }}>許可ドメイン/アクション、上限値を編集して保存できます。</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <label style={{ fontWeight: 600 }}>許可ドメイン（1行1つ）</label>
          <textarea
            defaultValue={domainsText}
            onChange={(e) => setPolicy((p) => (p ? { ...p, allowedDomains: e.target.value.split(/\n+/).map((s) => s.trim()).filter(Boolean) } : p))}
            rows={6}
            style={{ width: '100%', padding: 8 }}
          />
        </div>
        <div>
          <label style={{ fontWeight: 600 }}>許可アクション（1行1つ）</label>
          <textarea
            defaultValue={actionsText}
            onChange={(e) => setPolicy((p) => (p ? { ...p, allowedActions: e.target.value.split(/\n+/).map((s) => s.trim()).filter(Boolean) } : p))}
            rows={6}
            style={{ width: '100%', padding: 8 }}
          />
        </div>
      </div>

      <div style={{ marginTop: 12, display: 'flex', gap: 16 }}>
        <label>
          最大ステップ数
          <input
            type="number"
            value={policy.maxSteps}
            onChange={(e) => setPolicy((p) => (p ? { ...p, maxSteps: Number(e.target.value) } : p))}
            style={{ marginLeft: 8, width: 120 }}
          />
        </label>
        <label>
          実行上限ミリ秒
          <input
            type="number"
            value={policy.maxRunMs}
            onChange={(e) => setPolicy((p) => (p ? { ...p, maxRunMs: Number(e.target.value) } : p))}
            style={{ marginLeft: 8, width: 160 }}
          />
        </label>
      </div>

      <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={onSave} disabled={saving}>{saving ? '保存中...' : '保存'}</button>
        {ok && <span style={{ color: '#389e0d' }}>保存しました</span>}
        {error && <span style={{ color: 'crimson' }}>保存に失敗しました: {error}</span>}
      </div>
    </div>
  );
}

