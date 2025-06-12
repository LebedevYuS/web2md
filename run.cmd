@echo off
setlocal

REM === Настройки ===
set "URLS_FILE="
set "OUTPUT_DIR="

REM === Путь к исполняемому файлу ===
set "EXE_PATH=web2md.exe"

REM === Проверяем наличие exe файла ===
if not exist "%EXE_PATH%" (
    echo Ошибка: Не найден файл "%EXE_PATH%"
    pause
    exit /b 1
)

REM === Проверяем наличие файла с URL ===
if not exist "%URLS_FILE%" (
    echo Ошибка: Не найден файл с URL: "%URLS_FILE%"
    pause
    exit /b 1
)

REM === Создаём папку вывода, если её нет ===
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
)

echo Запуск архивации...
"%EXE_PATH%" --urls-file "%URLS_FILE%" --output-dir "%OUTPUT_DIR%"

echo.
echo Готово!
pause