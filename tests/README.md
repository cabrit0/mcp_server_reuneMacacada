# Testes do MCP Server

Este diretório contém os testes para o MCP Server, organizados em diferentes categorias.

## Estrutura de Diretórios

```
tests/
│
├── unit/                  # Testes unitários
│   ├── test_api_models.py # Testes para os modelos de dados
│   ├── test_mcp_router.py # Testes para o router MCP
│   ├── test_task_router.py # Testes para o router Task
│   ├── test_cache_router.py # Testes para o router Cache
│   └── test_health_router.py # Testes para o router Health
│
├── integration/           # Testes de integração
│   └── test_api_integration.py # Testes de integração da API
│
└── performance/           # Testes de performance
    └── test_api_performance.py # Testes de performance da API
```

## Executando os Testes

### Todos os Testes

Para executar todos os testes:

```bash
python -m pytest
```

### Testes Unitários

Para executar apenas os testes unitários:

```bash
python -m pytest tests/unit/
```

### Testes de Integração

Para executar apenas os testes de integração:

```bash
python -m pytest tests/integration/
```

### Testes de Performance

Para executar apenas os testes de performance:

```bash
python -m pytest tests/performance/
```

### Cobertura de Código

Para executar os testes com cobertura de código:

```bash
python -m pytest --cov=. --cov-report=term --cov-report=html
```

Isso gerará um relatório de cobertura no terminal e um relatório HTML detalhado no diretório `htmlcov/`.

## Configuração de CI/CD

Os testes são executados automaticamente pelo GitHub Actions em cada push para a branch `main` e em cada pull request. A configuração está definida no arquivo `.github/workflows/ci.yml`.

## Adicionando Novos Testes

### Testes Unitários

Os testes unitários devem ser adicionados no diretório `tests/unit/` e seguir a convenção de nomenclatura `test_*.py`. Cada arquivo deve conter testes para um componente específico do sistema.

### Testes de Integração

Os testes de integração devem ser adicionados no diretório `tests/integration/` e seguir a convenção de nomenclatura `test_*.py`. Estes testes verificam a interação entre diferentes componentes do sistema.

### Testes de Performance

Os testes de performance devem ser adicionados no diretório `tests/performance/` e seguir a convenção de nomenclatura `test_*.py`. Estes testes verificam o desempenho do sistema em diferentes cenários.
