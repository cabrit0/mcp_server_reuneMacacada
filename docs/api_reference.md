# API Reference

Este documento fornece uma referência detalhada da API do MCP Server.

## Endpoints

### Verificação de Saúde

```
GET /health
```

Retorna o status do servidor.

**Resposta de Sucesso:**
```json
{
  "status": "ok"
}
```

### Geração de MCP

```
GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&language={language}
```

Gera um plano de aprendizagem para o tópico especificado.

**Parâmetros:**

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| topic | string | Sim | - | O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres) |
| max_resources | integer | Não | 15 | Número máximo de recursos a incluir (mín: 5, máx: 30) |
| num_nodes | integer | Não | 15 | Número de nós a incluir no plano de aprendizagem (mín: 10, máx: 30) |
| language | string | Não | "pt" | Idioma preferido para os recursos (ex: "pt", "en", "es") |

**Resposta de Sucesso:**

A resposta é um objeto JSON com a estrutura MCP completa, incluindo:

- Metadados do plano de aprendizagem
- Nós da árvore de aprendizagem
- Recursos para cada nó
- Relações de pré-requisitos entre os nós

Exemplo simplificado:

```json
{
  "id": "python_basics_abc123",
  "title": "Learning Path: Python",
  "description": "A comprehensive learning path to master Python.",
  "rootNodeId": "introduction_xyz789",
  "metadata": {
    "difficulty": "intermediate",
    "estimatedHours": 40,
    "tags": ["python", "programming", "tutorial", "article", "video"]
  },
  "nodes": {
    "introduction_xyz789": {
      "id": "introduction_xyz789",
      "title": "Introduction to Python",
      "description": "Get started with Python and learn the basic concepts.",
      "type": "lesson",
      "prerequisites": [],
      "resources": [
        {
          "id": "resource_123",
          "title": "Python for Beginners",
          "url": "https://example.com/python-beginners",
          "type": "article",
          "description": "A beginner's guide to Python programming."
        }
      ],
      "visualPosition": {"x": 0, "y": 0, "level": 0}
    },
    // Outros nós...
  }
}
```

**Códigos de Erro:**

| Código | Descrição |
|--------|-----------|
| 400 | Parâmetros inválidos ou faltando |
| 404 | Nenhum recurso encontrado para o tópico |
| 422 | Não foi possível gerar nós suficientes |
| 500 | Erro interno do servidor |

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

## Formato de Resposta Detalhado

O formato de resposta segue a estrutura JSON abaixo:

```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "rootNodeId": "string",
  "metadata": {
    "difficulty": "string",
    "estimatedHours": "integer",
    "tags": ["string"]
  },
  "nodes": {
    "node_id": {
      "id": "string",
      "title": "string",
      "description": "string",
      "type": "string",
      "state": "string",
      "prerequisites": ["string"],
      "resources": [
        {
          "id": "string",
          "title": "string",
          "url": "string",
          "type": "string",
          "description": "string",
          "duration": "integer",
          "readTime": "integer",
          "difficulty": "string"
        }
      ],
      "visualPosition": {
        "x": "number",
        "y": "number",
        "level": "integer"
      },
      "quiz": {
        "questions": [
          {
            "id": "string",
            "text": "string",
            "options": ["string"],
            "correctOptionIndex": "integer"
          }
        ],
        "passingScore": "integer"
      }
    }
  }
}
```

## Notas de Uso

1. **Otimização de Performance**: O servidor utiliza cache para melhorar a performance. Requisições repetidas para o mesmo tópico com os mesmos parâmetros serão servidas do cache.

2. **Limitações do Free Tier**: O servidor foi otimizado para funcionar no free tier do Render, mas pode haver limitações de performance em casos de uso intensivo.

3. **Suporte a Idiomas**: O servidor tem suporte especial para português, mas também funciona com outros idiomas.

4. **Validação de Tamanho Mínimo**: O servidor garante que a árvore de aprendizagem tenha pelo menos 10 nós concretos e úteis. Se não for possível gerar nós suficientes, um erro será retornado.
