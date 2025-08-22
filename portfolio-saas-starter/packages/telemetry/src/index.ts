import { isEnabled } from '@pkg/flags';

export type TelemetryEvent = {
  name: string;
  props?: Record<string, unknown>;
};

function optedIn(): boolean {
  // Browser: VITE_TELEMETRY_OPT_IN, Node: TELEMETRY_OPT_IN
  return (
    isEnabled('TELEMETRY_OPT_IN', false) ||
    isEnabled('VITE_TELEMETRY_OPT_IN', false)
  );
}

export function track(event: TelemetryEvent | string, props?: Record<string, unknown>) {
  if (!optedIn()) return; // no cost/no send by default
  const payload: TelemetryEvent = typeof event === 'string' ? { name: event, props } : event;
  // ここでは送信しない。必要時に送信先を実装（Opt-inが前提）
  // eslint-disable-next-line no-console
  console.log('[telemetry]', payload.name, payload.props ?? {});
}

