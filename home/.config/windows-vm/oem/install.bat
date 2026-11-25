@echo off
tzutil /s "Romance Standard Time"
powershell -NoProfile -ExecutionPolicy Bypass -File C:\OEM\ready.ps1
