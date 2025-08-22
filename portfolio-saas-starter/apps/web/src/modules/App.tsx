import React, { useEffect, useMemo, useState } from 'react';
import { Task } from '@pkg/types';
import { createTask, fetchTasks, toggleTask } from '../services/tasks.js';
import { MiniChart } from '../ui/MiniChart.js';
import { Cta } from '../ui/Cta.js';
import { Pricing } from '../ui/Pricing.js';
import { AutomationDemo } from './Automation.js';
import { PolicyEditor } from '../ui/PolicyEditor.js';
import { ArtifactsGallery } from '../ui/ArtifactsGallery.js';
import { isEnabled } from '@pkg/flags';
import { track } from '@pkg/telemetry';

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      setLoading(true);
      try {
        const data = await fetchTasks({ signal: ctrl.signal });
        setTasks(data);
      } catch (e) {
        if ((e as any)?.name !== 'AbortError') console.error(e);
      } finally {
        setLoading(false);
      }
    })();
    return () => ctrl.abort();
  }, []);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const optimistic: Task = {
      id: 'tmp-' + Math.random().toString(36).slice(2),
      title: title.trim(),
      done: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setTasks((prev) => [optimistic, ...prev]);
    setTitle('');
    try {
      const created = await createTask({ title: optimistic.title });
      setTasks((prev) => prev.map((t) => (t.id === optimistic.id ? created : t)));
      track('task_created', { source: 'ui' });
    } catch (e) {
      console.error(e);
    }
  }

  async function onToggle(id: string) {
    const prev = tasks;
    const current = tasks.find((t) => t.id === id);
    const nextDone = current ? !current.done : true;
    setTasks((cur) => cur.map((t) => (t.id === id ? { ...t, done: nextDone } : t)));
    try {
      await toggleTask(id, nextDone);
    } catch (e) {
      console.error(e);
      setTasks(prev);
    }
  }

  const chartData = useMemo(() => {
    const byDay = new Map<string, number>();
    for (const t of tasks) {
      const day = t.createdAt.slice(0, 10);
      byDay.set(day, (byDay.get(day) || 0) + 1);
    }
    return Array.from(byDay.entries())
      .sort((a, b) => (a[0] < b[0] ? -1 : 1))
      .map(([, v]) => v);
  }, [tasks]);

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', margin: 24 }}>
      <h1>Portfolio SaaS Starter</h1>
      <p style={{ color: '#555' }}>React + Vite + Vitest / Express API</p>

      <div style={{ marginTop: 16 }}>
        <Cta />
      </div>

      <div style={{ marginTop: 16 }}>
        <Pricing />
      </div>

      <form onSubmit={onAdd} style={{ display: 'flex', gap: 8 }}>
        <input
          placeholder="新しいタスク"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ padding: 8, flex: 1 }}
        />
        <button type="submit">追加</button>
      </form>

      {isEnabled('FEATURE_CHART', true) && (
      <div style={{ marginTop: 24 }}>
        <h2>自動操作（やーびす MVP）</h2>
        <AutomationDemo />
      </div>

      <div style={{ marginTop: 24 }}>
        <h2>作成数の推移</h2>
        <MiniChart values={chartData} />
      </div>
      )}

      <div style={{ marginTop: 24 }}>
        <PolicyEditor />
      </div>

      <div style={{ marginTop: 24 }}>
        <ArtifactsGallery />
      </div>

      <div style={{ marginTop: 24 }}>
        <h2>タスク</h2>
        {loading ? (
          <p>読み込み中...</p>
        ) : (
          <ul>
            {tasks.map((t) => (
              <li key={t.id}>
                <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input type="checkbox" checked={t.done} onChange={() => onToggle(t.id)} />
                  <span style={{ textDecoration: t.done ? 'line-through' : 'none' }}>{t.title}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
