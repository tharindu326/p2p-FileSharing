@echo off

IF "%~1"=="" (
    echo Usage: %0 config1.py [config2.py ...]
    goto :eof
)

:next
IF "%~1"=="" goto :eof
echo Starting Flask app with configuration: %1
start /b python app.py --config %1
timeout /t 5 /nobreak >nul
shift
goto next
