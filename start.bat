@echo off
chcp 65001 > nul
set PYTHONUTF8=1
python -X utf8 "%~dp0main.py" %*
