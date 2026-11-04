# Launch Quantum Estate X Development Environment
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "       QUANTUM ESTATE X - DEV ENVIRONMENT        " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Start Backend FastAPI server in background job
Write-Host "[1/2] Starting Backend FastAPI server on http://localhost:8000..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --reload --port 8000" -PassThru

# 2. Start Frontend Vite server
Write-Host "[2/2] Starting Frontend Vite dev server on http://localhost:5173..." -ForegroundColor Green
Set-Location frontend
npm run dev
