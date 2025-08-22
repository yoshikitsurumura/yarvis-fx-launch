import express from 'express';
import cors from 'cors';
import compression from 'compression';
import { tasksRouter } from './routes/tasks.js';
import { automationRouter } from './routes/automation.js';
import path from 'node:path';

export function createApp() {
  const app = express();
  app.use(compression());
  app.use(cors());
  app.use(express.json());
  // Serve artifacts (.data or configured DATA_DIR) under /files for convenient access from web UI
  const dataDir = process.env.DATA_DIR || '.data';
  app.use('/files', express.static(path.resolve(dataDir)));

  app.get('/health', (_req, res) => {
    res.json({ ok: true, service: 'api', version: '0.1.0' });
  });

  app.use('/tasks', tasksRouter);
  app.use('/automation', automationRouter);
  return app;
}

export const app = createApp();
