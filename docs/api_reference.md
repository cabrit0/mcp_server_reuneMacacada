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

### Geração de MCP (Síncrona)

```
GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&language={language}&category={category}
```

Gera um plano de aprendizagem para o tópico especificado de forma síncrona (aguarda a conclusão).

**Parâmetros:**

| Parâmetro     | Tipo    | Obrigatório | Padrão | Descrição                                                                                                          |
| ------------- | ------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| topic         | string  | Sim         | -      | O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres)                                           |
| max_resources | integer | Não         | 15     | Número máximo de recursos a incluir (mín: 5, máx: 30)                                                              |
| num_nodes     | integer | Não         | 15     | Número de nós a incluir no plano de aprendizagem (mín: 10, máx: 30)                                                |
| language      | string  | Não         | "pt"   | Idioma preferido para os recursos (ex: "pt", "en", "es")                                                           |
| category      | string  | Não         | null   | Categoria para o tópico (ex: "technology", "finance", "health"). Se não fornecido, será detectado automaticamente. |

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
      "visualPosition": { "x": 0, "y": 0, "level": 0 }
    }
    // Outros nós...
  }
}
```

**Códigos de Erro:**

| Código | Descrição                               |
| ------ | --------------------------------------- |
| 400    | Parâmetros inválidos ou faltando        |
| 404    | Nenhum recurso encontrado para o tópico |
| 422    | Não foi possível gerar nós suficientes  |
| 500    | Erro interno do servidor                |

### Geração de MCP (Assíncrona)

```
POST /generate_mcp_async?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&language={language}&category={category}
```

Inicia a geração de um plano de aprendizagem em segundo plano e retorna imediatamente com um ID de tarefa.

**Parâmetros:**

| Parâmetro     | Tipo    | Obrigatório | Padrão | Descrição                                                                                                          |
| ------------- | ------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| topic         | string  | Sim         | -      | O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres)                                           |
| max_resources | integer | Não         | 15     | Número máximo de recursos a incluir (mín: 5, máx: 30)                                                              |
| num_nodes     | integer | Não         | 15     | Número de nós a incluir no plano de aprendizagem (mín: 10, máx: 30)                                                |
| language      | string  | Não         | "pt"   | Idioma preferido para os recursos (ex: "pt", "en", "es")                                                           |
| category      | string  | Não         | null   | Categoria para o tópico (ex: "technology", "finance", "health"). Se não fornecido, será detectado automaticamente. |

**Resposta de Sucesso:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Task created successfully"
}
```

### Verificar Status da Tarefa

```
GET /status/{task_id}
```

Retorna informações detalhadas sobre o status de uma tarefa, incluindo progresso, mensagens e resultado (quando concluída).

**Parâmetros:**

| Parâmetro | Tipo   | Obrigatório | Descrição                  |
| --------- | ------ | ----------- | -------------------------- |
| task_id   | string | Sim         | O ID da tarefa a verificar |

**Resposta de Sucesso (Tarefa em Execução):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Generate MCP for topic: python",
  "status": "running",
  "progress": 40,
  "created_at": 1650123456.789,
  "updated_at": 1650123466.789,
  "completed_at": null,
  "messages": [
    {
      "time": 1650123456.789,
      "message": "Tarefa iniciada"
    },
    {
      "time": 1650123460.123,
      "message": "Iniciando busca de recursos"
    },
    {
      "time": 1650123466.789,
      "message": "Encontrados 12 recursos para o tópico: python"
    }
  ]
}
```

**Resposta de Sucesso (Tarefa Concluída):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Generate MCP for topic: python",
  "status": "completed",
  "progress": 100,
  "result": {
    "id": "python_abc123",
    "title": "Learning Path: Python",
    "description": "A comprehensive learning path to master Python.",
    "rootNodeId": "introduction_xyz789",
    "nodes": { ... },
    "metadata": { ... }
  },
  "created_at": 1650123456.789,
  "updated_at": 1650123486.789,
  "completed_at": 1650123486.789,
  "messages": [ ... ]
}
```

### Listar Tarefas

```
GET /tasks
```

Retorna uma lista de todas as tarefas no servidor.

**Resposta de Sucesso:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Generate MCP for topic: python",
    "status": "completed",
    "progress": 100,
    "created_at": 1650123456.789,
    "updated_at": 1650123486.789,
    "completed_at": 1650123486.789
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440111",
    "description": "Generate MCP for topic: javascript",
    "status": "running",
    "progress": 50,
    "created_at": 1650123556.789,
    "updated_at": 1650123566.789,
    "completed_at": null
  }
]
```

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

### Exemplo 5: Gerar um MCP de forma assíncrona

```
POST /generate_mcp_async?topic=inteligência+artificial&category=technology
```

### Exemplo 6: Verificar o status de uma tarefa

```
GET /status/550e8400-e29b-41d4-a716-446655440000
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

5. **Sistema de Tarefas Assíncronas**: Para evitar timeouts em requisições longas, especialmente no free tier do Render, recomenda-se utilizar o endpoint assíncrono `/generate_mcp_async` em vez do endpoint síncrono `/generate_mcp`. O endpoint assíncrono retorna imediatamente com um ID de tarefa, permitindo que o cliente verifique o progresso periodicamente e recupere o resultado quando estiver pronto.

6. **Feedback Visual**: Ao utilizar o sistema de tarefas assíncronas, é possível fornecer feedback visual ao usuário sobre o progresso da geração do MCP, melhorando significativamente a experiência do usuário.
