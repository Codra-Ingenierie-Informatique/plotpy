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
call %FUNC% GetModName MODNAME
call %FUNC% SetPythonPath
set PYLINT_ARG=%*
if "%PYLINT_ARG%"=="" set PYLINT_ARG=%MODNAME% --disable=fixme
%PYTHON% -m pylint --rcfile=%SCRIPTPATH%\..\.pylintrc %PYLINT_ARG% 1> C:\_projets\plotpy\temp_pylint.txt
call %FUNC% EndOfScript