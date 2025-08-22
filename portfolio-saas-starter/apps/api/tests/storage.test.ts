import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// ESM: dynamic import with cache-busting query so env takes effect
async function freshDb(DATA_DIR: string) {
  process.env.DATA_DIR = DATA_DIR;
  const mod = await import(`../src/storage/db.ts?cache=${Math.random()}`);
  return mod as typeof import('../src/storage/db');
}

describe('storage/db with temp DATA_DIR', () => {
  let dir = '';
  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), 'api-test-'));
  });
  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  it('initializes file and saves/loads tasks', async () => {
    const { loadAll, saveAll } = await freshDb(dir);
    const a = loadAll();
    expect(Array.isArray(a)).toBe(true);
    const sample = [{ id: '1', title: 'x', done: false, createdAt: '2020-01-01', updatedAt: '2020-01-01' }];
    saveAll(sample as any);
    const b = loadAll();
    expect(b).toEqual(sample);
    const file = join(dir, 'tasks.json');
    expect(existsSync(file)).toBe(true);
    const raw = readFileSync(file, 'utf8');
    expect(raw).toContain('"title": "x"');
  });
});

