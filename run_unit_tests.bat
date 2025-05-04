@echo off
echo Executando testes unitarios e verificando a qualidade do codigo...

echo.
echo === Executando testes com pytest ===
python -m pytest

echo.
echo === Verificando estilo de codigo com flake8 ===
python -m flake8

echo.
echo === Verificando tipos com mypy ===
python -m mypy .

echo.
echo Testes e verificacoes concluidos!
