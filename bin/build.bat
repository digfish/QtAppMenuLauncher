rem @echo off
set VIRTUALENV=%1
echo %VIRTUALENV%
%VIRTUALENV%\Scripts\activate && pyinstaller --onefile --windowed --name QtAppMenuLauncher ^
    --paths . -i app-menu-launcher.ico ^
     --add-data "app-menu-launcher.ico;." ^
    --workpath build --distpath dist --specpath . qtlauncher.py 
