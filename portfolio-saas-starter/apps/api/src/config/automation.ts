import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

export type AutomationPolicy = {
  allowedDomains: string[];
  allowedActions: string[];
  maxSteps: number;
  maxRunMs: number;
  notes?: string[];
};

const DEFAULT_POLICY: AutomationPolicy = {
  allowedDomains: ['example.com'],
  allowedActions: ['goto', 'waitFor', 'collect'],
  maxSteps: 20,
  maxRunMs: 30_000,
  notes: [
    'Safety-first: Only whitelisted domains and actions are allowed.',
    'Dry-run validation is required before execution.',
  ],
};

export function loadAutomationPolicy(): AutomationPolicy {
  const dataDir = process.env.DATA_DIR || '.data';
  const envPath = process.env.AUTOMATION_CONFIG;
  const p = envPath || join(dataDir, 'automation.config.json');
  if (existsSync(p)) {
    try {
      const raw = JSON.parse(readFileSync(p, 'utf8'));
      return {
        ...DEFAULT_POLICY,
        ...raw,
        allowedDomains: Array.isArray(raw?.allowedDomains) && raw.allowedDomains.length
          ? raw.allowedDomains
          : DEFAULT_POLICY.allowedDomains,
        allowedActions: Array.isArray(raw?.allowedActions) && raw.allowedActions.length
          ? raw.allowedActions
          : DEFAULT_POLICY.allowedActions,
      };
    } catch {
      return DEFAULT_POLICY;
    }
  }
  // Env override for domains (comma-separated)
  const envDomains = (process.env.AUTOMATION_ALLOWED_DOMAINS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  return {
    ...DEFAULT_POLICY,
    allowedDomains: envDomains.length ? envDomains : DEFAULT_POLICY.allowedDomains,
  };
}

export function saveAutomationPolicy(next: Partial<AutomationPolicy>): AutomationPolicy {
  const cur = loadAutomationPolicy();
  const merged: AutomationPolicy = {
    ...cur,
    ...next,
    allowedDomains: Array.isArray(next.allowedDomains) ? next.allowedDomains : cur.allowedDomains,
    allowedActions: Array.isArray(next.allowedActions) ? next.allowedActions : cur.allowedActions,
    maxSteps: typeof next.maxSteps === 'number' ? next.maxSteps : cur.maxSteps,
    maxRunMs: typeof next.maxRunMs === 'number' ? next.maxRunMs : cur.maxRunMs,
    notes: Array.isArray(next.notes) ? next.notes : cur.notes,
  };
  const dataDir = process.env.DATA_DIR || '.data';
  const envPath = process.env.AUTOMATION_CONFIG;
  const p = envPath || join(dataDir, 'automation.config.json');
  mkdirSync(join(p, '..'), { recursive: true });
  writeFileSync(p, JSON.stringify(merged, null, 2));
  return merged;
}
