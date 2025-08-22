@echo off
REM 体験画面（やーびす）をAPIモードで開きます（静的JSONを読み込み）
cd /d %~dp0
cd ..
start "" "http://localhost:8000/yarvis-fe/index.html?api=1"

