rem @echo off
set VIRTUALENV=%1
echo %VIRTUALENV%
%VIRTUALENV%\Scripts\activate && pyinstaller --clean qtlauncher.py 

