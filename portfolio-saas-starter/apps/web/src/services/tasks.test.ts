import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { Task } from '@pkg/types';

// Lazy import to get fresh module per test
const mod = () => import('./tasks.js');

const API = (path: string) => (import.meta.env.MODE === 'development' ? `/api${path}` : `http://localhost:3000${path}`);

describe('services/tasks', () => {
  const origFetch = global.fetch;

  beforeEach(() => {
    // @ts-expect-error mock fetch
    global.fetch = vi.fn();
  });
  afterEach(() => {
    global.fetch = origFetch as any;
    vi.restoreAllMocks();
  });

  it('fetchTasks() calls /tasks and returns JSON', async () => {
    const items: Task[] = [];
    (global.fetch as any).mockResolvedValue({ ok: true, json: () => items });
    const { fetchTasks } = await mod();
    const res = await fetchTasks();
    expect(global.fetch).toHaveBeenCalledWith(API('/tasks'));
    expect(res).toBe(items);
  });

  it('toggleTask() sends correct body', async () => {
    const server: Task = {
      id: '1',
      title: 'a',
      done: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    (global.fetch as any).mockResolvedValue({ ok: true, json: () => server });
    const { toggleTask } = await mod();
    const res = await toggleTask('1', true);
    expect(global.fetch).toHaveBeenCalledWith(API('/tasks/1'), expect.objectContaining({
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ done: true }),
    }));
    expect(res).toEqual(server);
  });
});

