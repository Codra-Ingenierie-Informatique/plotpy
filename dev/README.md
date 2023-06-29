Setting up plotpy development environment
=========================================

Python distribution
-------------------

Plotpy requires the following :

* Python 3.8.10 (e.g. WinPython)

* Additional Python packages

Installing all required packages :

    pip install --upgrade -r dev\requirements.txt

Test data
---------

CodraFT test data are located in different folders, depending on their nature or origin.

Required data for unit tests are located in "codraft\data\tests" (public data).

A second folder %DATA_CODRAFT% (optional) may be defined for additional tests which are
still under development (or for confidential data).

Specific environment variables
------------------------------

Visual Studio Code configuration used in `launch.json` and `tasks.json`
(examples) :

    set GUIDATA_PYTHONEXE=path\to\python.exe
