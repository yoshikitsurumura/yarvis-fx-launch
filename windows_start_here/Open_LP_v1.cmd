@echo off
REM LP (v1) を開く前に、Run_Server.cmd を起動しておくと安定します
cd /d %~dp0
cd ..
start "" "http://localhost:8000/lp/index.html?v=1&utm_source=lp&utm_medium=web&utm_campaign=launch"

