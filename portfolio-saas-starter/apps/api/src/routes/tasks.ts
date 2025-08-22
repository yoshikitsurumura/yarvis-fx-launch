import { Router } from 'express';
import { randomUUID } from 'node:crypto';
import { loadAll, saveAll } from '../storage/db.js';
import type { Task, CreateTaskInput, UpdateTaskInput } from '../domain/types.js';

export const tasksRouter = Router();

// List
tasksRouter.get('/', (_req, res) => {
  const items = loadAll();
  res.json(items);
});

// Create
tasksRouter.post('/', (req, res) => {
  const body = req.body as Partial<CreateTaskInput>;
  if (!body || typeof body.title !== 'string' || body.title.trim().length === 0) {
    return res.status(400).json({ error: 'title is required' });
  }
  const now = new Date().toISOString();
  const task: Task = {
    id: randomUUID(),
    title: body.title.trim(),
    done: false,
    createdAt: now,
    updatedAt: now,
  };
  const items = loadAll();
  items.push(task);
  saveAll(items);
  res.status(201).json(task);
});

// Update
tasksRouter.patch('/:id', (req, res) => {
  const { id } = req.params;
  const body = req.body as Partial<UpdateTaskInput>;
  const items = loadAll();
  const idx = items.findIndex((t) => t.id === id);
  if (idx === -1) return res.status(404).json({ error: 'not found' });
  const now = new Date().toISOString();
  const prev = items[idx];
  const next: Task = {
    ...prev,
    title: typeof body.title === 'string' ? body.title : prev.title,
    done: typeof body.done === 'boolean' ? body.done : prev.done,
    updatedAt: now,
  };
  items[idx] = next;
  saveAll(items);
  res.json(next);
});

// Delete
tasksRouter.delete('/:id', (req, res) => {
  const { id } = req.params;
  const items = loadAll();
  const next = items.filter((t) => t.id !== id);
  if (next.length === items.length) return res.status(404).json({ error: 'not found' });
  saveAll(next);
  res.status(204).end();
});

