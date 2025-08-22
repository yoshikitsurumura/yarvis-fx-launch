import { saveAll } from '../src/storage/db.js';
import type { Task } from '../src/domain/types.js';

function rnd(n: number) { return Math.floor(Math.random() * n); }

const now = new Date();
const days = 7;
const tasks: Task[] = [] as any;
for (let d = 0; d < days; d++) {
  const count = rnd(3) + 1;
  for (let i = 0; i < count; i++) {
    const created = new Date(now.getTime() - d * 24 * 3600 * 1000);
    const iso = created.toISOString();
    tasks.push({
      id: `seed-${d}-${i}-${rnd(9999)}`,
      title: `Sample #${d}-${i}`,
      done: rnd(2) === 0,
      createdAt: iso,
      updatedAt: iso,
    } as Task);
  }
}

saveAll(tasks);
console.log(`Seeded ${tasks.length} tasks.`);

