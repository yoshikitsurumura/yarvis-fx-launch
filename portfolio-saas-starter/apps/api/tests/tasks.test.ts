import { describe, it, expect } from 'vitest';
import { loadAll, saveAll } from '../src/storage/db.js';

describe('storage layer', () => {
  it('saves and loads tasks', () => {
    const initial = loadAll();
    saveAll([]);
    expect(loadAll()).toEqual([]);
    saveAll(initial);
  });
});

