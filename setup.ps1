# SRM Setup Script
# Quick setup for Windows PowerShell

Write-Host "🚀 Setting up SRM AI Assistant..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python found" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
Write-Host "✅ Virtual environment created" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Check for .env file
if (!(Test-Path ".env")) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env file created. Please edit it with your Azure credentials." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Edit .env file with your Azure credentials" -ForegroundColor White
    Write-Host "2. Run: streamlit run app.py" -ForegroundColor White
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    Write-Host ""
    Write-Host "Setup complete! 🎉" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the application:" -ForegroundColor Cyan
    Write-Host "  streamlit run app.py" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 For more information, see README.md" -ForegroundColor Cyan
