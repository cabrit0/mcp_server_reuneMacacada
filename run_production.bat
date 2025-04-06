@echo off
echo Iniciando MCP Server em modo de producao...

:: Limpar arquivos temporários
echo Limpando arquivos temporários...
if exist "*.pyc" del /Q "*.pyc"
if exist "__pycache__" rmdir /S /Q "__pycache__"
if exist ".pytest_cache" rmdir /S /Q ".pytest_cache"
if exist "*.log" del /Q "*.log"

:: Definir variáveis de ambiente para produção
set MCP_BASE_URL=https://reunemacacada.onrender.com
set MCP_DEBUG=false

echo.
echo O servidor estará disponível em:
echo   - Local: http://localhost:%PORT%
echo   - Produção: %MCP_BASE_URL%
echo.

:: Iniciar o servidor
:: O Render definirá a variável PORT automaticamente
python main.py
