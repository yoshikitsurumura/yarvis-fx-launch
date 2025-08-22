function toBool(v: unknown, def = false): boolean {
  if (v == null) return def;
  const s = String(v).toLowerCase();
  return s === '1' || s === 'true' || s === 'on' || s === 'yes';
}

export function isEnabled(name: string, defaultValue = false): boolean {
  // Browser (Vite): VITE_*
  try {
    // @ts-ignore
    const v = (typeof import.meta !== 'undefined' && import.meta.env)
      ? (import.meta as any).env?.[`VITE_${name}`]
      : undefined;
    if (v !== undefined) return toBool(v, defaultValue);
  } catch {}
  // Node: process.env
  if (typeof process !== 'undefined' && process.env) {
    const v = process.env[name] ?? process.env[`VITE_${name}`];
    if (v !== undefined) return toBool(v, defaultValue);
  }
  return defaultValue;
}

export function getVar(name: string, defaultValue = ''): string {
  try {
    // @ts-ignore
    const v = (typeof import.meta !== 'undefined' && import.meta.env)
      ? (import.meta as any).env?.[name] ?? (import.meta as any).env?.[`VITE_${name}`]
      : undefined;
    if (v !== undefined) return String(v);
  } catch {}
  if (typeof process !== 'undefined' && process.env) {
    const v = process.env[name] ?? process.env[`VITE_${name}`];
    if (v !== undefined) return String(v);
  }
  return defaultValue;
}

