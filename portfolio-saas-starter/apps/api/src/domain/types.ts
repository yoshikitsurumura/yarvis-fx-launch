export type ID = string;

export interface Task {
  id: ID;
  title: string;
  done: boolean;
  createdAt: string; // ISO
  updatedAt: string; // ISO
}

export interface CreateTaskInput {
  title: string;
}

export interface UpdateTaskInput {
  title?: string;
  done?: boolean;
}

