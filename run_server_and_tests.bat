@echo off
echo Iniciando o MCP Server e executando testes...

echo.
echo === Iniciando o MCP Server ===
start cmd /k python main.py

echo Aguardando o servidor iniciar...
timeout /t 5 /nobreak

echo.
echo === Executando testes ===
call run_tests.bat

echo.
echo Testes concluidos!
echo O servidor continua em execucao. Pressione Ctrl+C para encerra-lo.
