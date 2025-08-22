import type { AutomationPlan, AutomationResult } from '@pkg/types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE as string | undefined;
const API = (path: string) => {
  if (API_BASE && API_BASE.length > 0) return `${API_BASE}${path}`;
  return import.meta.env.MODE === 'development' ? `/api${path}` : `http://localhost:3000${path}`;
};

export async function createPlan(text: string): Promise<{ plan: AutomationPlan }> {
  const r = await fetch(API('/automation/plan'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!r.ok) throw new Error('failed to create plan');
  return r.json();
}

export async function executePlan(plan: AutomationPlan): Promise<AutomationResult> {
  const r = await fetch(API('/automation/execute'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan }),
  });
  if (!r.ok) throw new Error('failed to execute plan');
  return r.json();
}

export async function dryRun(plan: AutomationPlan): Promise<{ valid: boolean; issues: { level: 'error' | 'warn'; message: string; index?: number }[] }>
{
  const r = await fetch(API('/automation/dry-run'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan }),
  });
  if (!r.ok) throw new Error('failed to dry-run');
  return r.json();
}

export async function fetchPolicy(): Promise<{ policy: { allowedDomains: string[]; allowedActions: string[]; maxSteps: number; maxRunMs: number; notes?: string[] } }>{
  const r = await fetch(API('/automation/config'));
  if (!r.ok) throw new Error('failed to fetch policy');
  return r.json();
}

export async function savePolicy(input: Partial<{ allowedDomains: string[]; allowedActions: string[]; maxSteps: number; maxRunMs: number; notes?: string[] }>): Promise<{ policy: { allowedDomains: string[]; allowedActions: string[]; maxSteps: number; maxRunMs: number; notes?: string[] } }>{
  const r = await fetch(API('/automation/config'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!r.ok) throw new Error('failed to save policy');
  return r.json();
}

export async function fetchArtifacts(): Promise<{ items: { ts: number; path: string; files: string[] }[] }>{
  const r = await fetch(API('/automation/artifacts'));
  if (!r.ok) throw new Error('failed to fetch artifacts');
  return r.json();
}
