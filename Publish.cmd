@echo off
title Publish my site
cd /d "%~dp0"

echo.
echo   Publishing your site...
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo   This folder is not connected to GitHub yet.
  echo   Ask Claude to finish the GitHub setup first.
  echo.
  pause
  exit /b 1
)

echo   [1/3] Checking the site builds...
python build.py
if errorlevel 1 (
  echo.
  echo   The site did NOT build, so nothing was published.
  echo   Scroll up - the error message names the file with the problem.
  echo.
  pause
  exit /b 1
)

echo.
echo   [2/3] Saving your changes...
git add -A
git diff --cached --quiet
if not errorlevel 1 (
  echo   Nothing has changed since last time, so there is nothing to publish.
  echo.
  pause
  exit /b 0
)

git commit -m "Update site"
if errorlevel 1 (
  echo.
  echo   Could not save the changes.
  echo.
  pause
  exit /b 1
)

echo.
echo   [3/3] Sending to GitHub...
git push
if errorlevel 1 (
  echo.
  echo   The upload failed.
  echo   If a sign-in window appeared, sign in and run this again.
  echo   If you are offline, reconnect and run this again.
  echo.
  pause
  exit /b 1
)

echo.
echo   Done. Your site will be live in about a minute.
echo   You can watch it happen on the "Actions" tab of your GitHub repo.
echo.
pause
