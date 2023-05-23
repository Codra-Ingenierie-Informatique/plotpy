@echo off
REM This script was derived from PythonQwt project
REM ======================================================
REM Test launcher script
REM ======================================================
REM Licensed under the terms of the MIT License
REM Copyright (c) 2020 Pierre Raybaut
REM (see PythonQwt LICENSE file for more details)
REM ======================================================
setlocal
call %~dp0utils GetScriptPath SCRIPTPATH
call %FUNC% SetPythonPath
call %FUNC% UsePython

set COVERAGE_PROCESS_START=%SCRIPTPATH%\..\.coveragerc
pytest -v --cov --cov-report=html --mode=unattended plotpy
start .\htmlcov\index.html
call %FUNC% EndOfScript
