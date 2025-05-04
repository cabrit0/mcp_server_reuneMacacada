#!/bin/bash
# Script para executar testes e verificar a qualidade do código

echo "Executando testes com pytest..."
python -m pytest

echo "Verificando estilo de código com flake8..."
python -m flake8

echo "Verificando tipos com mypy..."
python -m mypy .

echo "Testes e verificações concluídos!"
