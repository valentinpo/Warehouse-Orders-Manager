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
echo    3. 🚀 Запустить бота локально
echo    4. ⏹ Остановить бота
echo    5. 🔄 Перезапустить бота
echo    6. 📦 Установить зависимости
echo    7. 🐍 Инициализация Git (первый запуск)
echo    8. ❌ Выход
echo.
echo ========================================
set /p choice="Выбери действие (1-8): "
if "%choice%"=="1" goto push
if "%choice%"=="2" goto pull
if "%choice%"=="3" goto start
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto restart
if "%choice%"=="6" goto install
if "%choice%"=="7" goto initgit
if "%choice%"=="8" goto end
goto menu

:push
cls
echo ========================================
echo    📤 ЗАГРУЗКА НА GITHUB
echo ========================================
if not exist ".git" (
    echo ⚠ Git не инициализирован!
    echo Выберите пункт 7 в главном меню для инициализации.
    pause
    goto menu
)
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
if not exist "venv\Scripts\python.exe" (
    echo ⚠ Виртуальное окружение не найдено!
    echo Создаю новое...
    python -m venv venv
)
echo Активация venv...
call venv\Scripts\activate.bat
echo Установка зависимостей...
pip install -q -r requirements.txt 2>nul
echo.
echo Запуск main.py...
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
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak >nul
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
echo Обновление pip...
python -m pip install --upgrade pip -q
echo Установка пакетов из requirements.txt...
pip install -r requirements.txt
echo.
echo ✓ Готово! Все зависимости установлены.
pause
goto menu

:initgit
cls
echo ========================================
echo    🐍 ИНИЦИАЛИЗАЦИЯ GIT
echo ========================================
echo.
if exist ".git" (
    echo ⚠ Git уже инициализирован в этой папке!
    echo.
    pause
    goto menu
)
echo Инициализация Git репозитория...
git init
echo.
echo Создание ветки main...
git branch -M main
echo.
echo Подключение к удалённому репозиторию...
git remote add origin git@github.com:valentinpo/Warehouse-Orders-Manager.git
echo.
echo Проверка подключения...
git remote -v
echo.
echo ========================================
echo ✓ Git успешно инициализирован!
echo ========================================
echo.
echo Теперь вы можете:
echo   1. Добавить файлы: git add .
echo   2. Сделать коммит: git commit -m "сообщение"
echo   3. Запушить: git push -u origin main
echo.
echo Или просто выберите пункт 1 в главном меню.
pause
goto menu

:end
cls
echo ========================================
echo    👋 До свидания!
echo ========================================
exit