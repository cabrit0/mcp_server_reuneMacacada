# MCP Server API Endpoints Reference

Este documento contém uma referência completa de todos os endpoints disponíveis no MCP Server v1.0.7.

## URL Base

### Produção

```
https://reunemacacada.onrender.com
```

### Desenvolvimento Local

```
http://localhost:8000
```

> **Nota:** Todos os endpoints documentados neste documento estão disponíveis em ambos os URLs. Use o URL de produção para aplicações em produção e o URL local para desenvolvimento e testes.

## Endpoints Disponíveis

### 1. Verificação de Saúde

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

### 2. Geração de MCP (Síncrona)

```
GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}
```

Gera um plano de aprendizagem para o tópico especificado de forma síncrona (aguarda a conclusão).

**Parâmetros:**

| Parâmetro     | Tipo    | Obrigatório | Padrão | Descrição                                                                                                          |
| ------------- | ------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| topic         | string  | Sim         | -      | O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres)                                           |
| max_resources | integer | Não         | 15     | Número máximo de recursos a incluir (mín: 5, máx: 30)                                                              |
| num_nodes     | integer | Não         | 15     | Número de nós a incluir no plano de aprendizagem (mín: 10, máx: 30)                                                |
| min_width     | integer | Não         | 3      | Largura mínima da árvore (nós no primeiro nível) (mín: 2, máx: 10)                                                 |
| max_width     | integer | Não         | 5      | Largura máxima em qualquer nível da árvore (mín: 3, máx: 15)                                                       |
| min_height    | integer | Não         | 3      | Altura mínima da árvore (profundidade) (mín: 2, máx: 8)                                                            |
| max_height    | integer | Não         | 7      | Altura máxima da árvore (profundidade) (mín: 3, máx: 12)                                                           |
| language      | string  | Não         | "pt"   | Idioma preferido para os recursos (ex: "pt", "en", "es")                                                           |
| category      | string  | Não         | null   | Categoria para o tópico (ex: "technology", "finance", "health"). Se não fornecido, será detectado automaticamente. |

**Resposta de Sucesso:**

A resposta é um objeto JSON com a estrutura MCP completa, incluindo:

- ID único
- Título e descrição
- ID do nó raiz
- Dicionário de nós
- Metadados

**Códigos de Status:**

| Código | Descrição                                 |
| ------ | ----------------------------------------- |
| 200    | Sucesso                                   |
| 400    | Parâmetros inválidos ou erro de validação |
| 404    | Recursos não encontrados para o tópico    |
| 500    | Erro interno do servidor                  |

### 3. Geração de MCP (Assíncrona)

```
POST /generate_mcp_async?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}
```

Inicia a geração de um plano de aprendizagem em segundo plano e retorna imediatamente com um ID de tarefa.

**Parâmetros:**

Os mesmos parâmetros do endpoint síncrono.

**Resposta de Sucesso:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Task created successfully"
}
```

**Códigos de Status:**

| Código | Descrição                                 |
| ------ | ----------------------------------------- |
| 200    | Sucesso                                   |
| 400    | Parâmetros inválidos ou erro de validação |
| 500    | Erro interno do servidor                  |

### 4. Verificar Status da Tarefa

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

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 404    | Tarefa não encontrada    |
| 500    | Erro interno do servidor |

### 5. Listar Tarefas

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

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 500    | Erro interno do servidor |

### 6. Limpar Cache

```
POST /clear_cache?pattern={pattern}
```

Limpa o cache do servidor com base em um padrão de correspondência.

**Parâmetros:**

| Parâmetro | Tipo   | Obrigatório | Descrição                                                                                                                                               |
| --------- | ------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pattern   | string | Não         | Padrão para correspondência de chaves. Padrão é "_" que limpa todo o cache. Exemplos: "mcp:_" para todos os MCPs, "search:\*" para resultados de busca. |

**Resposta de Sucesso:**

```json
{
  "status": "success",
  "message": "Cleared 15 items from cache",
  "pattern": "mcp:*",
  "count": 15
}
```

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 500    | Erro interno do servidor |

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

### Exemplo 4: Gerar um MCP com categoria específica

```
GET /generate_mcp?topic=design&category=technology
```

### Exemplo 5: Gerar um MCP com estrutura personalizada

```
GET /generate_mcp?topic=história+do+brasil&min_width=4&max_width=8&min_height=4&max_height=8
```

### Exemplo 6: Gerar um MCP de forma assíncrona

```
POST /generate_mcp_async?topic=inteligência+artificial&category=technology
```

### Exemplo 7: Limpar todo o cache

```
POST /clear_cache
```

### Exemplo 8: Limpar apenas o cache de MCPs

```
POST /clear_cache?pattern=mcp:*
```

### Exemplo 9: Verificar o status de uma tarefa

```
GET /status/550e8400-e29b-41d4-a716-446655440000
```

## Recomendações de Uso

1. **Use o endpoint assíncrono**: Para evitar timeouts, especialmente no plano gratuito do Render, recomendamos usar o endpoint `/generate_mcp_async` em vez do `/generate_mcp`.

2. **Implemente cache local**: Armazene MCPs gerados anteriormente para reduzir a carga no servidor.

3. **Forneça feedback visual**: Durante o processo de geração assíncrona, use o endpoint `/status/{task_id}` para fornecer feedback visual ao usuário.

4. **Controle a estrutura da árvore**: Use os parâmetros `min_width`, `max_width`, `min_height` e `max_height` para controlar a estrutura da árvore de aprendizagem.

5. **Tratamento de erros**: Implemente tratamento de erros robusto para lidar com falhas na API.
