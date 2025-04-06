@echo off
echo Executando testes para o MCP Server...

set BASE_URL=http://localhost:8000
set TOPIC=inteligencia artificial
set CATEGORY=technology

echo.
echo === Testando endpoint de verificacao de saude ===
python test_health.py %BASE_URL%

echo.
echo === Testando endpoint de limpeza de cache ===
python test_clear_cache.py %BASE_URL%

echo.
echo === Testando endpoint assincrono ===
python test_async_simple.py %BASE_URL% "%TOPIC%" %CATEGORY%

echo.
echo === Testando endpoint de listagem de tarefas ===
python test_list_tasks.py %BASE_URL%

echo.
echo Testes concluidos!
