@echo off
REM 簡易サーバを起動して http://localhost:8000/ で見られるようにします
cd /d %~dp0
cd ..
echo サーバを起動します。閉じるには Ctrl + C。
where py >nul 2>nul
if %errorlevel%==0 (
  py -m http.server 8000
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python -m http.server 8000
  ) else (
    echo Python が見つかりませんでした。Microsoft Store から Python をインストールしてください。
    pause
  )
)
