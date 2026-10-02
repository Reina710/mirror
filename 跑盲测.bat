@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ================================================
echo   盲测：拿 6 道题考镜像，看它像不像你
echo   （喂完聊天后跑这个，对比喂之前的分数）
echo ================================================
echo.
"C:\Users\11651\.workbuddy\binaries\python\versions\3.13.12\python.exe" blind_test.py
echo.
pause
