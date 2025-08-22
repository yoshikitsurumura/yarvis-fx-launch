import React, { useEffect, useState } from 'react';
import { fetchArtifacts } from '../services/automation.js';

type Item = { ts: number; path: string; files: string[] };

export function ArtifactsGallery() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const { items } = await fetchArtifacts();
        setItems(items || []);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div style={{ border: '1px solid #eee', padding: 16, borderRadius: 8 }}>
      <h2>成果物ギャラリー（最新）</h2>
      {loading ? <p>読み込み中...</p> : items.length === 0 ? (
        <p style={{ color: '#666' }}>まだ成果物がありません。ワンクリックデモを実行すると生成されます。</p>
      ) : (
        <ul>
          {items.map((it, idx) => (
            <li key={idx} style={{ marginBottom: 8 }}>
              <div style={{ fontWeight: 600 }}>{new Date(it.ts).toLocaleString()}</div>
              <div style={{ color: '#555' }}>{it.path}</div>
              {it.files?.length > 0 && (
                <div style={{ marginTop: 4 }}>
                  {it.files.slice(0, 5).map((f, i) => (
                    <a key={i} href={`${it.path}/${f}`} target="_blank" rel="noreferrer" style={{ marginRight: 8 }}>
                      {f}
                    </a>
                  ))}
                  {it.files.length > 5 && <span>...他 {it.files.length - 5} 件</span>}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

