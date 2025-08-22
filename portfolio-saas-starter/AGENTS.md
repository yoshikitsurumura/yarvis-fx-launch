# Repository Guidelines

## Project Structure & Module Organization
- Root workspace uses npm workspaces: code lives in `apps/*` and `packages/*`.
- `apps/api`: Express + TypeScript API (`src/` routes, storage, domain; tests in `tests/`).
- `apps/web`: React + Vite frontend (`src/modules`, `src/ui`, `src/services`).
- `packages/types`: Shared TypeScript definitions consumed by apps.
- Supporting directories: `docs/`, `.github/`, and Docker config in `docker-compose.yml`.

## Build, Test, and Development Commands
- Root
  - `npm run build`: Build all workspaces.
  - `npm test`: Run Vitest across workspaces.
  - `npm run typecheck`: TypeScript checks (no emit) across workspaces.
- API (`@app/api`)
  - `npm run dev -w @app/api`: Start API with watch.
  - `npm start -w @app/api`: Run built server on `PORT` (default 3000).
  - `npm test -w @app/api`: Run API tests.
- Web (`@app/web`)
  - `npm run dev -w @app/web`: Start Vite dev server.
  - `npm run preview -w @app/web`: Preview production build.
- Docker
  - `docker-compose up --build`: Launch API and Web together.

## Coding Style & Naming Conventions
- Language: TypeScript with ES modules; strict types where practical.
- Indentation: 2 spaces; keep files small and focused.
- Filenames: `*.ts` / `*.tsx`; React components in `src/modules/*`.
- Packages: `@app/*` for apps, `@pkg/*` for shared packages.

## Testing Guidelines
- Framework: Vitest. Locations: `apps/api/tests/*.test.ts`, `apps/web/src/**/*.test.tsx`.
- Run: `npm test` (all), or `npm test -w @app/{api,web}` for a single app.
- Expectations: Cover core logic and components; include edge cases. Use Testing Library in Web.

## Commit & Pull Request Guidelines
- Commits: Imperative, scoped messages (e.g., `api: add tasks route`, `web: fix toggle state`).
- PRs: Clear description, linked issues, screenshots/GIFs for UI changes, and a brief test plan (commands run, results). Note breaking changes or migrations.

## Security & Configuration Tips
- API stores data under `.data/tasks.json` (Docker volume). Do not commit `.data/`.
- Config: `PORT` and `DATA_DIR` for API; avoid secrets in code or VCS.

