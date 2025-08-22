import React, { useEffect, useRef } from 'react';

function draw(el: HTMLCanvasElement, values: number[]) {
  const ctx = el.getContext('2d');
  if (!ctx) return;
  const w = (el.width = 320);
  const h = (el.height = 80);
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = '#2d6cdf';
  ctx.lineWidth = 2;
  ctx.beginPath();
  const max = Math.max(1, ...values);
  for (let i = 0; i < values.length; i++) {
    const x = (i / Math.max(1, values.length - 1)) * (w - 16) + 8;
    const y = h - (values[i] / max) * (h - 16) - 8;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function MiniChartBase({ values }: { values: number[] }) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = requestAnimationFrame(() => draw(el, values));
    return () => cancelAnimationFrame(raf);
  }, [values]);
  return <canvas ref={ref} />;
}

export const MiniChart = React.memo(MiniChartBase, (a, b) => {
  if (a.values.length !== b.values.length) return false;
  for (let i = 0; i < a.values.length; i++) if (a.values[i] !== b.values[i]) return false;
  return true;
});

