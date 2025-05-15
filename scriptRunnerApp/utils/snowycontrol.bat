@echo off
powershell -Command "$args = '%*' -split ' '; $args | ForEach-Object { Write-Host ('success' + $_) }"