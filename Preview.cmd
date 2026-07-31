@echo off
title Preview my site
cd /d "%~dp0"

echo.
echo   Building your site and opening it in your browser.
echo   Leave this window open while you work - every time you save a file,
echo   the site rebuilds and you can just refresh the page.
echo.
echo   Close this window when you are done.
echo.

python build.py --serve --open

echo.
echo   Preview stopped.
pause
