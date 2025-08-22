import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import type { Task } from '../domain/types.js';

const DATA_DIR = process.env.DATA_DIR || '.data';
const FILE = join(DATA_DIR, 'tasks.json');

export function loadAll(): Task[] {
  if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
  if (!existsSync(FILE)) {
    writeFileSync(FILE, JSON.stringify([], null, 2));
    return [];
  }
  const raw = readFileSync(FILE, 'utf8');
  try {
    const data = JSON.parse(raw);
    if (Array.isArray(data)) return data as Task[];
    return [];
  } catch {
    return [];
  }
}

export function saveAll(tasks: Task[]) {
  if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
  writeFileSync(FILE, JSON.stringify(tasks, null, 2));
}

