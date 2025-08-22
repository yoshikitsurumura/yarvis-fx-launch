import type { Task } from '@pkg/types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE as string | undefined;
const API = (path: string) => {
  if (API_BASE && API_BASE.length > 0) return `${API_BASE}${path}`;
  return import.meta.env.MODE === 'development' ? `/api${path}` : `http://localhost:3000${path}`;
};

function withTimeout<T>(ms: number, signal?: AbortSignal) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(new DOMException('timeout', 'AbortError')), ms);
  const combined = signal
    ? new AbortController()
    : ctrl;
  if (signal) {
    signal.addEventListener('abort', () => combined.abort(signal.reason), { once: true });
    ctrl.signal.addEventListener('abort', () => combined.abort(ctrl.signal.reason), { once: true });
  }
  return { signal: (signal ? combined : ctrl).signal, clear: () => clearTimeout(id) };
}

export async function fetchTasks(opts?: { signal?: AbortSignal }): Promise<Task[]> {
  const t = withTimeout<Response>(10_000, opts?.signal);
  const r = await fetch(API('/tasks'), { signal: t.signal }).finally(() => t.clear());
  if (!r.ok) throw new Error('failed to fetch');
  return r.json();
}

export async function createTask(input: { title: string }, opts?: { signal?: AbortSignal }): Promise<Task> {
  const t = withTimeout<Response>(10_000, opts?.signal);
  const r = await fetch(API('/tasks'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    signal: t.signal,
  }).finally(() => t.clear());
  if (!r.ok) throw new Error('failed to create');
  return r.json();
}

export async function toggleTask(id: string, done: boolean, opts?: { signal?: AbortSignal }): Promise<Task> {
  const t = withTimeout<Response>(10_000, opts?.signal);
  const r = await fetch(API(`/tasks/${id}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ done }),
    signal: t.signal,
  }).finally(() => t.clear());
  if (!r.ok) throw new Error('failed to update');
  return r.json();
}
