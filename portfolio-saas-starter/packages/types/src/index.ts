export type ID = string;

export interface Task {
  id: ID;
  title: string;
  done: boolean;
  createdAt: string; // ISO
  updatedAt: string; // ISO
}

export interface CreateTaskInput { title: string }
export interface UpdateTaskInput { title?: string; done?: boolean }

// --- Automation (Yarbis MVP) ---
export type AutomationAction = 'goto' | 'fill' | 'press' | 'waitFor' | 'collect';

export interface AutomationStep {
  action: AutomationAction;
  // optional fields depending on action
  url?: string;
  selector?: string;
  value?: string;
  key?: string;
  as?: string;
}

export interface AutomationPlan {
  steps: AutomationStep[];
  artifacts?: string[];
  timeoutMs?: number;
}

export interface AutomationResult {
  ok: boolean;
  summary?: string;
  artifactsPath?: string;
  artifacts?: { name: string; url: string }[];
}
