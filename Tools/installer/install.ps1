$ErrorActionPreference = "Stop"
Write-Host "=== JewAI Installer Bootstrap ===" -ForegroundColor Cyan

$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    Write-Host "Python не найден в системе." -ForegroundColor Yellow
    $ans = Read-Host "Скачать и установить Python 3.12 автоматически? (y/n)"
    if ($ans -match "^[yY]") {
        Write-Host "Скачивание Python 3.12..." -ForegroundColor Cyan
        $url = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
        $out = "$env:TEMP\python_installer.exe"
        Invoke-WebRequest -Uri $url -OutFile $out
        
        Write-Host "Установка Python (тихий режим)..." -ForegroundColor Cyan
        Start-Process -FilePath $out -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait
        
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "Python установлен." -ForegroundColor Green
    } else {
        Write-Host "Установка отменена. Python необходим для работы JewAI." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Запуск локального сервера установки..." -ForegroundColor Cyan
Start-Process pythonw -ArgumentList "server.py" -WorkingDirectory $PSScriptRoot

Start-Sleep -Seconds 2
Write-Host "Открытие интерфейса установки в браузере..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8671"