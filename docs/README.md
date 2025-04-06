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

### 6. [Relevância de Recursos e Distribuição de Quizzes](resource_relevance_and_quiz_distribution.md)

Implementação de filtragem de recursos baseada em TF-IDF para garantir que os recursos correspondam ao tópico solicitado e distribuição estratégica de quizzes para uma experiência de aprendizagem mais equilibrada.

### 7. [Integração com YouTube e Sistema de Categorias](youtube_integration.md)

Implementação da integração com YouTube para incluir vídeos relevantes nos planos de aprendizagem e do sistema de categorias para gerar conteúdo mais específico para diferentes tipos de tópicos.

### 8. [Sistema de Tarefas Assíncronas](async_tasks_system.md)

Implementação de um sistema de tarefas assíncronas com feedback de progresso em tempo real para melhorar a experiência do usuário e evitar timeouts em requisições longas.

### 9. [Controle de Estrutura da Árvore](tree_structure_control.md)

Implementação de parâmetros para controlar a estrutura da árvore de aprendizagem, incluindo largura e altura.

### 10. [Referência de Endpoints](endpoints_reference.md)

Referência completa de todos os endpoints disponíveis no MCP Server v1.1.0.

### 11. [Melhorias de Performance](performance_improvements.md)

Descrição das melhorias de performance implementadas e planejadas para o MCP Server.

### 12. [Sistema de Cache](caching_system.md)

Descrição do sistema de cache implementado no MCP Server para melhorar a performance.

### 13. [Otimização de Web Scraping](web_scraping_optimization.md)

Descrição das técnicas e estratégias de otimização de web scraping implementadas e planejadas.

## Endpoints da API

### Verificação de Saúde

```
GET /health
```

Retorna o status do servidor.

### Geração de MCP (Síncrona)

```
GET /generate_mcp?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}
```

Gera um plano de aprendizagem para o tópico especificado de forma síncrona (aguarda a conclusão).

**Parâmetros:**

- `topic` (obrigatório): O tópico para o qual gerar o plano de aprendizagem (mínimo 3 caracteres)
- `max_resources` (opcional): Número máximo de recursos a incluir (padrão: 15, mín: 5, máx: 30)
- `num_nodes` (opcional): Número de nós a incluir no plano de aprendizagem (padrão: 15, mín: 10, máx: 30)
- `min_width` (opcional): Largura mínima da árvore (nós no primeiro nível) (padrão: 3, mín: 2, máx: 10)
- `max_width` (opcional): Largura máxima em qualquer nível da árvore (padrão: 5, mín: 3, máx: 15)
- `min_height` (opcional): Altura mínima da árvore (profundidade) (padrão: 3, mín: 2, máx: 8)
- `max_height` (opcional): Altura máxima da árvore (profundidade) (padrão: 7, mín: 3, máx: 12)
- `language` (opcional): Idioma preferido para os recursos (padrão: "pt")
- `category` (opcional): Categoria para o tópico (ex: "technology", "finance", "health"). Se não fornecido, será detectado automaticamente.

### Geração de MCP (Assíncrona)

```
POST /generate_mcp_async?topic={topic}&max_resources={max_resources}&num_nodes={num_nodes}&min_width={min_width}&max_width={max_width}&min_height={min_height}&max_height={max_height}&language={language}&category={category}
```

Inicia a geração de um plano de aprendizagem em segundo plano e retorna imediatamente com um ID de tarefa.

**Parâmetros:**

- Mesmos parâmetros do endpoint síncrono

### Verificar Status da Tarefa

```
GET /status/{task_id}
```

Retorna informações detalhadas sobre o status de uma tarefa, incluindo progresso, mensagens e resultado (quando concluída).

### Listar Tarefas

```
GET /tasks
```

Retorna uma lista de todas as tarefas no servidor.

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

### Exemplo 5: Gerar um MCP com categoria específica

```
GET /generate_mcp?topic=design&category=technology
```

### Exemplo 6: Gerar um MCP de forma assíncrona

```
POST /generate_mcp_async?topic=inteligência+artificial&category=technology
```

### Exemplo 7: Verificar o status de uma tarefa

```
GET /status/550e8400-e29b-41d4-a716-446655440000
```
