@echo off
REM このスクリプトはフォームURLの設定ファイルを開きます
cd /d %~dp0
cd ..
if not exist lp\config.js (
  echo 初回設定: lp\config.example.js から lp\config.js を作成します...
  copy lp\config.example.js lp\config.js >nul
)
echo メモ帳で lp\config.js を開きます。GoogleフォームURLに書き換えて保存してください。
start notepad "lp\config.js"

