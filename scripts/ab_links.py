#!/usr/bin/env python3
"""
ABリンク自動生成ツール

使い方:
  python scripts/ab_links.py --base https://<your-pages-url>/

出力:
  v1/v2 と embed=1 のリンク（UTM付き）を表示
"""
import argparse
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', required=True, help='PagesのベースURL（例: https://user.github.io/repo/）')
    p.add_argument('--campaign', default='launch', help='utm_campaign 値（既定: launch）')
    p.add_argument('--source', default='lp', help='utm_source 値（既定: lp）')
    p.add_argument('--medium', default='web', help='utm_medium 値（既定: web）')
    a = p.parse_args()

    base = a.base.rstrip('/')
    # Note: GitHub Pagesは 'lp/' をルートとして公開しているため、
    # 公開URLがそのままLPトップになります（/lp/は付けません）。
    common = f"utm_source={a.source}&utm_medium={a.medium}&utm_campaign={a.campaign}"
    v1 = f"{base}/?v=1&{common}"
    v2 = f"{base}/?v=2&{common}"
    v1e = v1 + "&embed=1"
    v2e = v2 + "&embed=1"
    print("# AB Links\n")
    print("- v1:", v1)
    print("- v2:", v2)
    print("- v1 (embed):", v1e)
    print("- v2 (embed):", v2e)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
