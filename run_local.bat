@echo off
echo Configurando ambiente de desenvolvimento local...

:: Limpar arquivos temporários
echo Limpando arquivos temporários...
if exist "*.pyc" del /Q "*.pyc"
if exist "__pycache__" rmdir /S /Q "__pycache__"
if exist ".pytest_cache" rmdir /S /Q ".pytest_cache"
if exist "*.log" del /Q "*.log"

:: Definir variáveis de ambiente para desenvolvimento local
set MCP_BASE_URL=http://localhost:8000
set PORT=8000
set MCP_DEBUG=true

echo Iniciando MCP Server localmente...
echo.

:: Iniciar o servidor
python main.py
