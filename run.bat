@echo off
REM Simple wrapper to call start.bat
REM This is for compatibility - users can run either start.bat or run.bat

cd /d "%~dp0"
call start.bat
