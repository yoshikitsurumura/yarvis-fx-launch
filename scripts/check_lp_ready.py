#!/usr/bin/env python3
"""
LP準備チェック: フォームURL設定や主要ファイルの存在を確認します。

使い方:
  python scripts/check_lp_ready.py
終了コード:
  0: 問題なし / 1: 要対応あり
"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(__file__))

def main():
    ok = True
    # 1) config.js
    cfg_path = os.path.join(BASE, 'lp', 'config.js')
    if not os.path.exists(cfg_path):
        print('[WARN] lp/config.js が見つかりません。まず lp/config.example.js をコピーしてください。')
        ok = False
    else:
        txt = open(cfg_path, 'r', encoding='utf-8', errors='ignore').read()
        m = re.search(r"LP_FORM_URL\s*=\s*'([^']+)'", txt)
        url = m.group(1) if m else ''
        if not url or 'example.com/form' in url:
            print('[WARN] フォームURLが未設定です（exampleのまま）。Googleフォームの /viewform を設定してください。')
            ok = False
        elif not url.endswith('/viewform'):
            print('[WARN] フォームURLは /viewform で終わることを推奨します。現在: ', url)
    # 2) 必須ファイル
    for p in ['lp/index.html','lp/ab.js','yarvis-fe/index.html']:
        if not os.path.exists(os.path.join(BASE, p)):
            print(f'[WARN] ファイルが見つかりません: {p}')
            ok = False
    print('OK' if ok else 'NEEDS FIX')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()

