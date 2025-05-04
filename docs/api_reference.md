# MCP Server API Reference v1.1.3

Esta documentação fornece uma referência completa para a API do MCP Server versão 1.1.3.

## URL Base

### Produção

```
https://reunemacacada.onrender.com
```

### Desenvolvimento Local

```
http://localhost:8000
```

> **Nota:** Todos os endpoints documentados estão disponíveis em ambos os URLs. Use o URL de produção para aplicações em produção e o URL local para desenvolvimento e testes.

## Endpoints

### Verificação de Saúde

#### GET /health

Verifica se o servidor está funcionando corretamente.

**Resposta de Sucesso (200 OK):**

```json
{
  "status": "ok"
}
```

### Geração de MCP

#### GET /generate_mcp

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

**Resposta de Sucesso (200 OK):**

A resposta é um objeto JSON com a estrutura MCP completa, incluindo:

```json
{
  "id": "mcp_abc123",
  "title": "Learning Path: Python",
  "description": "A comprehensive learning path to master Python.",
  "topic": "Python",
  "category": "technology",
  "language": "pt",
  "nodes": {
    "node_1": {
      "id": "node_1",
      "title": "Introduction to Python",
      "description": "Get started with Python and learn the basic concepts.",
      "type": "lesson",
      "resources": [
        {
          "id": "resource_1",
          "title": "Python for Beginners",
          "url": "https://example.com/python-beginners",
          "type": "article",
          "description": "A beginner's guide to Python programming.",
          "readTime": 10,
          "difficulty": "beginner"
        }
      ],
      "prerequisites": [],
      "visualPosition": {
        "x": 0,
        "y": 0,
        "level": 0
      }
    }
    // Mais nós...
  },
  "totalHours": 40,
  "tags": ["python", "programming", "technology"]
}
```

**Códigos de Status:**

| Código | Descrição                                 |
| ------ | ----------------------------------------- |
| 200    | Sucesso                                   |
| 400    | Parâmetros inválidos ou erro de validação |
| 404    | Recursos não encontrados para o tópico    |
| 500    | Erro interno do servidor                  |

#### POST /generate_mcp_async

Inicia a geração de um plano de aprendizagem em segundo plano e retorna imediatamente com um ID de tarefa.

**Parâmetros:**

Os mesmos parâmetros do endpoint síncrono.

**Resposta de Sucesso (200 OK):**

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

### Gerenciamento de Tarefas

#### GET /status/{task_id}

Retorna informações detalhadas sobre o status de uma tarefa, incluindo progresso, mensagens e resultado (quando concluída).

**Parâmetros:**

| Parâmetro | Tipo   | Obrigatório | Descrição                  |
| --------- | ------ | ----------- | -------------------------- |
| task_id   | string | Sim         | O ID da tarefa a verificar |

**Resposta de Sucesso (Tarefa em Execução) (200 OK):**

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

**Resposta de Sucesso (Tarefa Concluída) (200 OK):**

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
    "topic": "Python",
    "category": "technology",
    "language": "pt",
    "nodes": {
      // Estrutura de nós...
    },
    "totalHours": 40,
    "tags": ["python", "programming", "technology"]
  },
  "created_at": 1650123456.789,
  "updated_at": 1650123486.789,
  "completed_at": 1650123486.789,
  "messages": [
    // Mensagens...
  ]
}
```

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 404    | Tarefa não encontrada    |
| 500    | Erro interno do servidor |

#### GET /tasks

Retorna uma lista de todas as tarefas no servidor.

**Resposta de Sucesso (200 OK):**

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

### Gerenciamento de Cache

#### GET /cache_stats

Retorna estatísticas sobre o cache do servidor, incluindo informações sobre o cache principal e o cache de métodos por domínio.

**Resposta de Sucesso (200 OK):**

```json
{
  "status": "success",
  "cache": {
    "total_keys": 42,
    "info": {
      "used_memory": "1.2MB",
      "hits": 156,
      "misses": 89
    }
  },
  "domain_method_cache": {
    "totalDomains": 15,
    "simpleMethodCount": 10,
    "puppeteerMethodCount": 5,
    "domains": [
      {
        "domain": "example.com",
        "method": "simple",
        "successRate": 0.95,
        "usageCount": 12,
        "lastUpdated": "2023-05-15T14:30:45Z"
      }
    ]
  }
}
```

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 500    | Erro interno do servidor |

#### POST /clear_cache

Limpa o cache do servidor com base em um padrão de correspondência.

**Parâmetros:**

| Parâmetro          | Tipo    | Obrigatório | Padrão | Descrição                                                                                                                                               |
| ------------------ | ------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pattern            | string  | Não         | "\*"   | Padrão para correspondência de chaves. Padrão é "_" que limpa todo o cache. Exemplos: "mcp:_" para todos os MCPs, "search:\*" para resultados de busca. |
| clear_domain_cache | boolean | Não         | false  | Se deve limpar também o cache de métodos por domínio.                                                                                                   |

**Resposta de Sucesso (200 OK):**

```json
{
  "status": "success",
  "message": "Cleared 15 items from cache",
  "pattern": "mcp:*",
  "count": 15,
  "domain_cache_cleared": 0
}
```

**Códigos de Status:**

| Código | Descrição                |
| ------ | ------------------------ |
| 200    | Sucesso                  |
| 500    | Erro interno do servidor |

## Modelos de Dados

> **Nota:** Todos os modelos de dados estão definidos em `api/models.py` e seguem o padrão Pydantic para validação e serialização.

### MCP

| Campo       | Tipo   | Descrição                                  |
| ----------- | ------ | ------------------------------------------ |
| id          | string | Identificador único do MCP                 |
| title       | string | Título do plano de aprendizagem            |
| description | string | Descrição do plano de aprendizagem         |
| rootNodeId  | string | ID do nó raiz da árvore de aprendizagem    |
| nodes       | object | Dicionário de nós no plano de aprendizagem |
| metadata    | object | Metadados do plano de aprendizagem         |

### Node

| Campo          | Tipo   | Descrição                                                  |
| -------------- | ------ | ---------------------------------------------------------- |
| id             | string | Identificador único do nó                                  |
| title          | string | Título do nó                                               |
| description    | string | Descrição do nó                                            |
| type           | string | Tipo do nó (lesson, exercise_set, project, quiz)           |
| state          | string | Estado do nó (available, locked, completed, in_progress)   |
| resources      | array  | Lista de recursos para o nó                                |
| prerequisites  | array  | Lista de IDs de nós pré-requisitos                         |
| rewards        | array  | Lista de recompensas por completar o nó                    |
| hints          | array  | Lista de dicas para o nó                                   |
| visualPosition | object | Posição visual do nó no plano de aprendizagem              |
| quiz           | object | Quiz associado ao nó (opcional)                            |
| exerciseSet    | object | Conjunto de exercícios práticos associado ao nó (opcional) |

### Metadata

| Campo          | Tipo    | Descrição                                                      |
| -------------- | ------- | -------------------------------------------------------------- |
| difficulty     | string  | Nível de dificuldade do MCP (beginner, intermediate, advanced) |
| estimatedHours | integer | Tempo estimado para completar o MCP em horas                   |
| tags           | array   | Tags relacionadas ao MCP                                       |

### Resource

| Campo       | Tipo    | Descrição                                                                    |
| ----------- | ------- | ---------------------------------------------------------------------------- |
| id          | string  | Identificador único do recurso                                               |
| title       | string  | Título do recurso                                                            |
| url         | string  | URL do recurso                                                               |
| type        | string  | Tipo do recurso (article, video, documentation, tutorial, exercise, quiz)    |
| description | string  | Descrição do recurso (opcional)                                              |
| duration    | integer | Duração do recurso em minutos (para vídeos, opcional)                        |
| readTime    | integer | Tempo estimado de leitura em minutos (para artigos, opcional)                |
| difficulty  | string  | Nível de dificuldade do recurso (beginner, intermediate, advanced, opcional) |
| thumbnail   | string  | URL da miniatura do recurso (opcional)                                       |

### Quiz

| Campo        | Tipo    | Descrição                            |
| ------------ | ------- | ------------------------------------ |
| questions    | array   | Lista de perguntas no quiz           |
| passingScore | integer | Pontuação mínima para passar no quiz |

### Question

| Campo              | Tipo    | Descrição                       |
| ------------------ | ------- | ------------------------------- |
| id                 | string  | Identificador único da pergunta |
| text               | string  | Texto da pergunta               |
| options            | array   | Lista de opções para a pergunta |
| correctOptionIndex | integer | Índice da opção correta         |

### ExerciseSet

| Campo        | Tipo    | Descrição                                   |
| ------------ | ------- | ------------------------------------------- |
| exercises    | array   | Lista de exercícios no conjunto             |
| passingScore | integer | Pontuação mínima para passar nos exercícios |

### Exercise

| Campo              | Tipo   | Descrição                                                                   |
| ------------------ | ------ | --------------------------------------------------------------------------- |
| id                 | string | Identificador único do exercício                                            |
| title              | string | Título do exercício                                                         |
| description        | string | Descrição do exercício                                                      |
| difficulty         | string | Nível de dificuldade (beginner, intermediate, advanced)                     |
| instructions       | string | Instruções passo a passo para o exercício                                   |
| hints              | array  | Lista de dicas para o exercício (para revelação progressiva)                |
| solution           | string | Solução do exercício                                                        |
| verificationMethod | string | Método de verificação (multiple_choice, text_match, code_execution, manual) |
| options            | array  | Lista de opções para exercícios de múltipla escolha (opcional)              |
| correctAnswer      | string | Resposta correta para o exercício                                           |

### TaskInfo

| Campo        | Tipo    | Descrição                                                        |
| ------------ | ------- | ---------------------------------------------------------------- |
| id           | string  | Identificador único da tarefa                                    |
| description  | string  | Descrição da tarefa                                              |
| status       | string  | Status da tarefa (pending, running, completed, failed, canceled) |
| progress     | integer | Progresso da tarefa (0-100)                                      |
| result       | object  | Resultado da tarefa (se concluída)                               |
| error        | string  | Mensagem de erro (se falhou)                                     |
| created_at   | number  | Timestamp de criação da tarefa                                   |
| updated_at   | number  | Timestamp da última atualização da tarefa                        |
| completed_at | number  | Timestamp de conclusão da tarefa (opcional)                      |
| messages     | array   | Lista de mensagens sobre o progresso da tarefa                   |

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

## Considerações para Implantação no Render

O MCP Server está hospedado no Render (https://reunemacacada.onrender.com), e há algumas considerações importantes para garantir uma boa experiência do usuário:

1. **Cache Local**: Implemente cache local para reduzir o número de requisições ao servidor, já que o free tier do Render tem limitações de recursos.

2. **Tratamento de Timeout**: Configure timeouts adequados para as requisições, pois a geração de planos de aprendizagem pode levar mais tempo no free tier.

3. **Feedback Visual**: Sempre forneça feedback visual ao usuário enquanto o plano está sendo gerado.

4. **Tratamento de Erros**: Implemente tratamento de erros robusto para lidar com possíveis falhas na API.

5. **Modo Offline**: Considere implementar um modo offline que permita aos usuários acessar planos de aprendizagem previamente baixados.

6. **Uso do Sistema Assíncrono**: Utilize o sistema de tarefas assíncronas para evitar timeouts e proporcionar uma melhor experiência ao usuário, especialmente para tópicos complexos.
