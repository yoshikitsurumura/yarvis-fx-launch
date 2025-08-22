import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { mkdtempSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

describe('/automation', () => {
  let dir = '';
  let server: any;
  beforeEach(async () => {
    dir = mkdtempSync(join(tmpdir(), 'api-test-'));
    process.env.DATA_DIR = dir;
    const { app } = await import('../src/app.js');
    server = app;
  });
  afterEach(() => rmSync(dir, { recursive: true, force: true }));

  it('returns a plan from text', async () => {
    const res = await request(server).post('/automation/plan').send({ text: 'test' });
    expect(res.statusCode).toBe(200);
    expect(res.body.plan.steps.length).toBeGreaterThan(0);
  });

  it('simulates execution and writes artifacts', async () => {
    const plan = { steps: [{ action: 'goto', url: 'https://example.com' }] };
    const res = await request(server).post('/automation/execute').send({ plan });
    expect(res.statusCode).toBe(200);
    const p = res.body.artifactsPath as string;
    expect(p).toBeTruthy();
    const planFile = join(p, 'plan.json');
    expect(existsSync(planFile)).toBe(true);
    const raw = readFileSync(planFile, 'utf8');
    expect(raw).toContain('example.com');
    // artifacts list and svg screenshot
    expect(Array.isArray(res.body.artifacts)).toBe(true);
    const names = (res.body.artifacts as any[]).map((x) => x.name);
    expect(names.some((n) => n.endsWith('.svg'))).toBe(true);
  });

  it('exposes policy via /automation/config', async () => {
    const res = await request(server).get('/automation/config');
    expect(res.statusCode).toBe(200);
    expect(Array.isArray(res.body?.policy?.allowedDomains)).toBe(true);
    expect(typeof res.body?.policy?.maxSteps).toBe('number');
  });
});
