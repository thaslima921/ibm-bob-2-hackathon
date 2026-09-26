#!/usr/bin/env pwsh
# Reset ChangeGuard demo state — removes all prior analysis results
Remove-Item -Path "backend\data\results\*" -Force -ErrorAction SilentlyContinue
Write-Host "Demo state reset. Run 'python -m uvicorn backend.main:app --reload' to start the backend."
