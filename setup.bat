@echo off
echo Installing MediaMerger Bot...

:: Download Python 3.11 installer
echo Downloading Python 3.11...
curl -o python311_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

:: Install Python silently with PATH
echo Installing Python...
python311_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del python311_installer.exe

:: Wait for install to finish
timeout /t 10

:: Create venv and install packages
echo Setting up virtual environment...
py -3.11 -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install --prefer-binary -r requirements.txt

echo.
echo Done! Run start_bot.bat to start the bot.
pause
