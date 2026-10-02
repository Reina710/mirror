@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ================================================
echo   镜像分身：直接跟我聊天，我边聊边记住你
echo   输入 q 退出；输入 /记忆 看我记住了什么
echo ================================================
echo.
"C:\Users\11651\.workbuddy\binaries\python\versions\3.13.12\python.exe" mirror.py
echo.
pause
