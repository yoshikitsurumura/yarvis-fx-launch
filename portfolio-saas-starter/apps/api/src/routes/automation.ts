import { Router } from 'express';
import { mkdirSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import type { AutomationPlan, AutomationResult } from '@pkg/types';
import { loadAutomationPolicy, saveAutomationPolicy } from '../config/automation.js';

export const automationRouter = Router();

type ValidationIssue = { level: 'error' | 'warn'; message: string; index?: number };

function validatePlan(plan: AutomationPlan | undefined): { valid: boolean; issues: ValidationIssue[] } {
  const issues: ValidationIssue[] = [];
  if (!plan) return { valid: false, issues: [{ level: 'error', message: 'plan is required' }] };
  if (!Array.isArray(plan.steps) || plan.steps.length === 0) {
    issues.push({ level: 'error', message: 'steps must be a non-empty array' });
  }
  const policy = loadAutomationPolicy();
  if (plan.steps && plan.steps.length > policy.maxSteps) {
    issues.push({ level: 'warn', message: `too many steps (>${policy.maxSteps}); consider reducing`, index: -1 });
  }

  for (let i = 0; i < (plan.steps?.length || 0); i++) {
    const s = (plan.steps as any)[i] || {};
    if (!s.action || typeof s.action !== 'string') {
      issues.push({ level: 'error', message: 'step.action must be string', index: i });
      continue;
    }
    if (!policy.allowedActions.includes(s.action)) {
      issues.push({ level: 'error', message: `action '${s.action}' is not allowed`, index: i });
    }
    if (s.action === 'goto') {
      const url = String(s.url || '');
      try {
        const u = new URL(url);
        if (u.protocol !== 'http:' && u.protocol !== 'https:') {
          issues.push({ level: 'error', message: 'goto url must be http(s)', index: i });
        }
        const host = u.hostname.toLowerCase();
        const allowed = policy.allowedDomains.some((d) => d && (host === d.toLowerCase() || host.endsWith('.' + d.toLowerCase())));
        if (!allowed) {
          issues.push({ level: 'error', message: `domain not allowed: ${host}`, index: i });
        }
      } catch {
        issues.push({ level: 'error', message: 'goto url is invalid', index: i });
      }
    }
    if (s.action === 'waitFor' || s.action === 'collect' || s.action === 'click' || s.action === 'type' || s.action === 'fill') {
      if (!s.selector || typeof s.selector !== 'string') {
        issues.push({ level: 'error', message: `${s.action} requires selector`, index: i });
      }
    }
    if (s.action === 'collect' && typeof s.as !== 'string') {
      issues.push({ level: 'error', message: 'collect requires as (string)', index: i });
    }
    if (s.action === 'fill' && typeof s.value !== 'string') {
      issues.push({ level: 'error', message: 'fill requires value (string)', index: i });
    }
    if (s.action === 'press' && typeof s.key !== 'string') {
      issues.push({ level: 'error', message: 'press requires key (string)', index: i });
    }
  }
  const valid = issues.every((x) => x.level !== 'error');
  return { valid, issues };
}

automationRouter.post('/plan', (req, res) => {
  const text = (req.body?.text ?? '').toString();
  if (!text || text.length < 2) return res.status(400).json({ error: 'text is required' });

  // For safety and determinism in MVP, return a minimal plan when AI is not allowed
  let plan: AutomationPlan;
  if (process.env.AI_ALLOW !== '1') {
    plan = {
      steps: [
        { action: 'goto', url: 'https://example.com' },
        { action: 'waitFor', selector: 'body' },
        { action: 'collect', selector: 'h1', as: 'titles' },
      ],
      artifacts: ['screenshot:loaded'],
      timeoutMs: 20000,
    };
  } else {
    // Placeholder for AI-generated plan (out of scope without network). Use the same for now.
    plan = {
      steps: [
        { action: 'goto', url: 'https://example.com' },
        { action: 'waitFor', selector: 'body' },
        { action: 'collect', selector: 'h1', as: 'titles' },
      ],
      artifacts: ['screenshot:loaded'],
      timeoutMs: 20000,
    };
  }
  res.json({ plan });
});

automationRouter.get('/config', (_req, res) => {
  const policy = loadAutomationPolicy();
  res.json({ policy });
});

automationRouter.post('/config', (req, res) => {
  const body = req.body || {};
  // basic shape validation
  if (body.allowedDomains && !Array.isArray(body.allowedDomains)) return res.status(400).json({ error: 'allowedDomains must be array' });
  if (body.allowedActions && !Array.isArray(body.allowedActions)) return res.status(400).json({ error: 'allowedActions must be array' });
  if (body.maxSteps && typeof body.maxSteps !== 'number') return res.status(400).json({ error: 'maxSteps must be number' });
  if (body.maxRunMs && typeof body.maxRunMs !== 'number') return res.status(400).json({ error: 'maxRunMs must be number' });
  const saved = saveAutomationPolicy(body);
  res.json({ policy: saved });
});

automationRouter.get('/artifacts', (_req, res) => {
  const base = process.env.DATA_DIR || '.data';
  const dir = join(base, 'automation');
  let list: { ts: number; path: string; files: string[] }[] = [];
  try {
    const entries = readdirSync(dir);
    for (const name of entries) {
      const p = join(dir, name);
      try {
        const st = statSync(p);
        if (st.isDirectory()) {
          const files = readdirSync(p);
          const ts = Number(name) || st.mtimeMs;
          list.push({ ts, path: `/files/automation/${name}`, files });
        }
      } catch {}
    }
  } catch {}
  list.sort((a, b) => b.ts - a.ts);
  res.json({ items: list.slice(0, 20) });
});

automationRouter.post('/execute', (req, res) => {
  const plan = req.body?.plan as AutomationPlan | undefined;
  if (!plan || !Array.isArray(plan.steps)) return res.status(400).json({ error: 'plan is required' });
  const check = validatePlan(plan);
  if (!check.valid) {
    return res.status(400).json({ error: 'invalid plan', issues: check.issues });
  }

  // Simulate execution: persist artifacts metadata under .data/automation
  const base = process.env.DATA_DIR || '.data';
  const dir = join(base, 'automation', String(Date.now()));
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'plan.json'), JSON.stringify(plan, null, 2));
  // generate pseudo screenshot SVG artifact
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450">
  <rect width="100%" height="100%" fill="#f7fafc" />
  <text x="24" y="48" font-size="24" fill="#2d3748">Automation Simulation</text>
  <text x="24" y="84" font-size="16" fill="#4a5568">Executed ${plan.steps.length} steps</text>
  <text x="24" y="114" font-size="14" fill="#718096">${new Date().toISOString()}</text>
  <rect x="24" y="140" width="752" height="260" fill="#edf2f7" stroke="#cbd5e0" />
  <text x="36" y="170" font-size="14" fill="#2d3748">First step: ${(plan.steps[0]?.action || 'n/a')}</text>
  <text x="36" y="195" font-size="12" fill="#4a5568">Hint: This is a placeholder preview (SVG)</text>
</svg>`;
  const svgName = 'screenshot_simulated.svg';
  writeFileSync(join(dir, svgName), svg);
  const result: AutomationResult = {
    ok: true,
    artifactsPath: dir,
    summary: `Executed ${plan.steps.length} steps (simulated).`,
    artifacts: [
      { name: 'plan.json', url: `/files/automation/${dir.split('automation/')[1]}/plan.json` },
      { name: 'result.json', url: `/files/automation/${dir.split('automation/')[1]}/result.json` },
      { name: svgName, url: `/files/automation/${dir.split('automation/')[1]}/${svgName}` },
    ],
  };
  writeFileSync(join(dir, 'result.json'), JSON.stringify(result, null, 2));
  res.json(result);
});

automationRouter.post('/dry-run', (req, res) => {
  const plan = req.body?.plan as AutomationPlan | undefined;
  const check = validatePlan(plan);
  res.json(check);
});
