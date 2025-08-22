import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

describe('/automation dry-run', () => {
  let dir = '';
  let server: any;
  beforeEach(async () => {
    dir = mkdtempSync(join(tmpdir(), 'api-test-'));
    process.env.DATA_DIR = dir;
    const { app } = await import('../src/app.js');
    server = app;
  });
  afterEach(() => rmSync(dir, { recursive: true, force: true }));

  it('validates a good plan', async () => {
    const plan = { steps: [{ action: 'goto', url: 'https://example.com' }, { action: 'waitFor', selector: 'body' }] };
    const res = await request(server).post('/automation/dry-run').send({ plan });
    expect(res.statusCode).toBe(200);
    expect(res.body.valid).toBe(true);
    expect(Array.isArray(res.body.issues)).toBe(true);
  });

  it('flags invalid action and bad url', async () => {
    const plan = { steps: [{ action: 'goto', url: 'file:///etc/passwd' }, { action: 'boom' }] } as any;
    const res = await request(server).post('/automation/dry-run').send({ plan });
    expect(res.statusCode).toBe(200);
    expect(res.body.valid).toBe(false);
    const msgs = res.body.issues.map((x: any) => x.message).join('\n');
    expect(msgs).toContain('goto url must be http(s)');
    expect(msgs).toContain("action 'boom' is not allowed");
  });
});

