@echo off
REM This script was derived from PythonQwt project
REM ======================================================
REM Upgrade environment
REM ======================================================
REM Licensed under the terms of the MIT License
REM Copyright (c) 2020 Pierre Raybaut
REM (see PythonQwt LICENSE file for more details)
REM ======================================================
setlocal
call %~dp0utils GetScriptPath SCRIPTPATH
cd %SCRIPTPATH%\..

:: Iterate over all directories in the grandparent directory
:: (WinPython base directories)
call %FUNC% GetPythonExeGrandParentDir DIR0
for /D %%d in ("%DIR0%*") do (
    set WINPYDIRBASE=%%d
    call !WINPYDIRBASE!\scripts\env.bat
    echo Upgrading environment for "%%d":
    python -m pip install --upgrade -r dev\requirements.txt
    echo ----
)

%PYTHON% -m pip list > dev\pip_list.txt
call %FUNC% EndOfScript