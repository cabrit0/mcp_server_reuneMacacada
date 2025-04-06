# Sistema de Tarefas Assíncronas

Este documento descreve o sistema de tarefas assíncronas implementado no MCP Server, que permite a geração de planos de aprendizagem em segundo plano com feedback de progresso em tempo real.

## Visão Geral

O sistema de tarefas assíncronas foi projetado para resolver o problema de timeouts em requisições longas, especialmente no plano gratuito do Render, onde os recursos são limitados. Ele permite que o servidor responda imediatamente ao cliente com um ID de tarefa, enquanto continua processando a solicitação em segundo plano.

## Componentes Principais

### 1. Gerenciador de Tarefas (`task_manager.py`)

O gerenciador de tarefas é responsável por:
- Criar novas tarefas
- Rastrear o progresso das tarefas
- Armazenar os resultados das tarefas
- Limpar tarefas antigas para evitar consumo excessivo de memória

### 2. Modelos de Dados (`schemas.py`)

Os seguintes modelos foram adicionados para suportar o sistema de tarefas:
- `TaskStatus`: Enum que define os possíveis estados de uma tarefa (pendente, em execução, concluída, falha)
- `TaskMessage`: Modelo para mensagens de progresso
- `TaskInfo`: Modelo completo com informações sobre uma tarefa
- `TaskCreationResponse`: Resposta para a criação de uma tarefa

### 3. Endpoints da API (`main.py`)

Foram adicionados os seguintes endpoints:
- `POST /generate_mcp_async`: Cria uma tarefa assíncrona para gerar um MCP
- `GET /status/{task_id}`: Obtém o status de uma tarefa específica
- `GET /tasks`: Lista todas as tarefas no servidor

## Fluxo de Trabalho

1. **Criação da Tarefa**:
   - O cliente faz uma requisição para `https://reunemacacada.onrender.com/generate_mcp_async` com os parâmetros desejados
   - O servidor cria uma nova tarefa e retorna imediatamente o ID da tarefa
   - O processamento continua em segundo plano

2. **Monitoramento do Progresso**:
   - O cliente faz requisições periódicas para `https://reunemacacada.onrender.com/status/{task_id}` para verificar o progresso
   - O servidor retorna informações detalhadas sobre o status da tarefa, incluindo:
     - Status atual (pendente, em execução, concluída, falha)
     - Porcentagem de progresso (0-100)
     - Mensagens de progresso
     - Resultado (quando concluída)
     - Erro (quando falha)

3. **Conclusão da Tarefa**:
   - Quando a tarefa é concluída, o resultado (MCP) é armazenado no objeto da tarefa
   - O cliente pode recuperar o resultado através do endpoint `/status/{task_id}`
   - O resultado também é armazenado no cache do servidor para futuras requisições

## Exemplo de Uso

### Criação de uma Tarefa

```http
POST https://reunemacacada.onrender.com/generate_mcp_async?topic=python&num_nodes=20&language=pt
```

Resposta:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Task created successfully"
}
```

### Verificação do Status

```http
GET https://reunemacacada.onrender.com/status/550e8400-e29b-41d4-a716-446655440000
```

Resposta (em execução):
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

Resposta (concluída):
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

## Benefícios

1. **Melhor Experiência do Usuário**:
   - Feedback imediato para o usuário
   - Atualizações de progresso em tempo real
   - Evita timeouts em requisições longas

2. **Melhor Desempenho do Servidor**:
   - Distribuição mais eficiente da carga de trabalho
   - Capacidade de processar mais requisições simultaneamente
   - Melhor utilização dos recursos limitados do plano gratuito do Render

3. **Maior Robustez**:
   - Recuperação mais fácil de falhas
   - Melhor rastreamento de erros
   - Capacidade de retomar tarefas interrompidas (futura implementação)

## Limitações Atuais

1. **Persistência**: As tarefas são armazenadas apenas em memória e são perdidas quando o servidor é reiniciado.
2. **Escalabilidade**: O sistema atual não é adequado para ambientes com múltiplas instâncias do servidor.
3. **Limpeza**: As tarefas antigas são removidas apenas quando o limite de tarefas é atingido.

## Trabalhos Futuros

1. **Persistência de Tarefas**: Implementar armazenamento persistente para tarefas (banco de dados).
2. **Retomada de Tarefas**: Permitir que tarefas interrompidas sejam retomadas.
3. **Cancelamento de Tarefas**: Adicionar a capacidade de cancelar tarefas em execução.
4. **Priorização de Tarefas**: Implementar um sistema de prioridades para tarefas.
5. **Limites por Usuário**: Implementar limites de tarefas por usuário para evitar abuso.

## Integração com Flutter

Para integrar o sistema de tarefas assíncronas com aplicativos Flutter, consulte o documento [Flutter Integration](flutter_integration.md#sistema-de-tarefas-assíncronas).
