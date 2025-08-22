@echo off
REM 体験画面（やーびす）を開きます。Run_Server.cmd を起動しておくと安定します
cd /d %~dp0
cd ..
start "" "http://localhost:8000/yarvis-fe/index.html"

