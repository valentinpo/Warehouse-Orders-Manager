@echo off
chcp 65001 >nul
color 0A
title Warehouse Bot Manager - valentinpo

:menu
cls
echo ========================================
echo    📦 WAREHOUSE BOT MANAGER
echo    Проект: Warehouse-Orders-Manager
echo ========================================
echo.
echo    1. 📤 Запушить проект на GitHub
echo    2. 📥 Скачать проект с GitHub
echo    3. 🚀 Запустить бота
echo    4. ⏹ Остановить бота
echo    5. 🔄 Перезапустить бота
echo    6. 📦 Установить зависимости
echo    7. ❌ Выход
echo.
echo ========================================
set /p choice="Выбери действие (1-7): "
if "%choice%"=="1" goto push
if "%choice%"=="2" goto pull
if "%choice%"=="3" goto start
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto restart
if "%choice%"=="6" goto install
if "%choice%"=="7" goto end
goto menu

:push
cls
echo ========================================
echo    📤 ЗАГРУЗКА НА GITHUB
echo ========================================
git status
echo.
set /p msg="Введите сообщение для коммита: "
git add .
git commit -m "%msg%"
git push -u origin main
echo.
echo ✓ Готово! Проект загружен на GitHub.
pause
goto menu

:pull
cls
echo ========================================
echo    📥 СКАЧИВАНИЕ С GITHUB
echo ========================================
git pull origin main
echo.
echo ✓ Готово! Проект обновлён.
pause
goto menu

:start
cls
echo ========================================
echo    🚀 ЗАПУСК БОТА
echo ========================================
echo Проверка виртуального окружения...
if not exist "venv\Scripts\python.exe" (
    echo ⚠ Виртуальное окружение не найдено!
    echo Создаю новое...
    python -m venv venv
)
echo.
echo Активация виртуального окружения...
call venv\Scripts\activate.bat
echo.
echo Проверка зависимостей...
pip install -q -r requirements.txt 2>nul
echo.
echo ========================================
echo    Запуск main.py...
echo    Для остановки нажми Ctrl+C
echo ========================================
python main.py
echo.
echo ✓ Бот завершил работу.
pause
goto menu

:stop
cls
echo ========================================
echo    ⏹ ОСТАНОВКА БОТА
echo ========================================
echo Завершение процессов Python...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
echo ✓ Процесс остановлен!
pause
goto menu

:restart
cls
echo ========================================
echo    🔄 ПЕРЕЗАПУСК БОТА
echo ========================================
echo Остановка...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul
echo Запуск...
call venv\Scripts\activate.bat
start cmd /k "python main.py"
echo ✓ Бот перезапущен!
pause
goto menu

:install
cls
echo ========================================
echo    📦 УСТАНОВКА ЗАВИСИМОСТЕЙ
echo ========================================
if not exist "venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo.
echo Обновление pip...
python -m pip install --upgrade pip -q
echo.
echo Установка пакетов из requirements.txt...
pip install -r requirements.txt
echo.
echo ✓ Готово! Все зависимости установлены.
pause
goto menu

:end
cls
echo ========================================
echo    👋 До свидания!
echo    Удачи в разработке! 🚀
echo ========================================
exit