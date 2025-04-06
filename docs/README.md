# Documentação do MCP Server

Este diretório contém a documentação das funcionalidades do MCP Server (Master Content Plan Server).

## Funcionalidades Documentadas

### 1. [Funcionalidades Atualizadas](updated_features.md)

Descrição detalhada das funcionalidades atualizadas do MCP Server, incluindo suporte para qualquer tema, parâmetros opcionais, validação de tamanho mínimo, suporte para português e otimizações de performance.

### 2. [Referência da API](api_reference.md)

Documentação detalhada dos endpoints da API, parâmetros, respostas e exemplos de uso.

### 3. [Integração com Flutter](flutter_integration.md)

Guia completo para integrar o MCP Server com aplicações Flutter, incluindo exemplos de código, modelos de dados e dicas de performance.

### 4. [Remoção da Detecção de Similaridade](removed_similarity_detection.md)

Remoção da funcionalidade de detecção de conteúdo similar que estava impedindo o servidor de encontrar mais que 3 nós.

### 5. [Otimizações de Performance](performance_optimization.md)

Implementação de otimizações para melhorar a performance do servidor no free tier do Render, incluindo sistema de cache em múltiplos níveis e otimizações de Puppeteer.

## Endpoints da API

### Verificação de Saúde

```
GET /health
```

Retorna o status do servidor.

### Geração de MCP

```
GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&language={language}
```

Gera um plano de aprendizagem para o tópico especificado.

**Parâmetros:**

- `topic` (obrigatório): O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres)
- `max_resources` (opcional): Número máximo de recursos a incluir (padrão: 15, mín: 5, máx: 30)
- `num_nodes` (opcional): Número de nós a incluir no plano de aprendizagem (padrão: 15, mín: 10, máx: 30)
- `language` (opcional): Idioma preferido para os recursos (padrão: "pt")

## Exemplos de Uso

### Exemplo 1: Gerar um MCP em português (padrão)

```
GET /generate_mcp?topic=python
```

### Exemplo 2: Gerar um MCP com número personalizado de nós

```
GET /generate_mcp?topic=machine+learning&num_nodes=20
```

### Exemplo 3: Gerar um MCP em inglês

```
GET /generate_mcp?topic=javascript&language=en
```

### Exemplo 4: Gerar um MCP com limite de recursos

```
GET /generate_mcp?topic=história+do+brasil&max_resources=20&num_nodes=25
```
