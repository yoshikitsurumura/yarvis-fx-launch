import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

describe('API routes /tasks', () => {
  let dir = '';
  let server: any;

  beforeEach(async () => {
    dir = mkdtempSync(join(tmpdir(), 'api-test-'));
    process.env.DATA_DIR = dir; // storage uses this at module init
    const { app } = await import('../src/app.js');
    server = app; // supertest can wrap express app directly
  });

  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  it('GET /health returns ok', async () => {
    const res = await request(server).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.ok).toBe(true);
  });

  it('CRUD happy path', async () => {
    const list1 = await request(server).get('/tasks');
    expect(list1.statusCode).toBe(200);
    expect(Array.isArray(list1.body)).toBe(true);

    const created = await request(server).post('/tasks').send({ title: 'hello' });
    expect(created.statusCode).toBe(201);
    expect(created.body.title).toBe('hello');
    const id = created.body.id;

    const patched = await request(server).patch(`/tasks/${id}`).send({ done: true });
    expect(patched.statusCode).toBe(200);
    expect(patched.body.done).toBe(true);

    const del = await request(server).delete(`/tasks/${id}`);
    expect(del.statusCode).toBe(204);
  });

  it('POST /tasks validates title', async () => {
    const bad = await request(server).post('/tasks').send({ title: '   ' });
    expect(bad.statusCode).toBe(400);
  });
});

