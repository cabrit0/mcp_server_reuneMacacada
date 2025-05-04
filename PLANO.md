# Plano de Refatoração do MCP Server

Este documento detalha o plano de refatoração do MCP Server para aplicar os princípios SOLID, melhorar a performance e resolver os bottlenecks identificados.

## Visão Geral

A refatoração será dividida em 5 fases principais, cada uma com tarefas específicas. O objetivo é transformar a arquitetura atual em uma estrutura modular, testável e extensível, mantendo a simplicidade.

## Estrutura de Pastas Alvo

```
mcp_server/
│
├── api/                    # Endpoints da API
│   ├── __init__.py
│   ├── endpoints.py        # Definição dos endpoints
│   ├── models.py           # Modelos de dados para a API
│   └── dependencies.py     # Dependências da API (validação, etc.)
│
├── core/                   # Lógica de negócio principal
│   ├── __init__.py
│   ├── path_generator.py   # Geração de árvores de aprendizagem
│   ├── content_manager.py  # Gerenciamento de conteúdo
│   └── task_manager.py     # Sistema de tarefas assíncronas
│
├── services/               # Serviços externos e integrações
│   ├── __init__.py
│   ├── search/             # Serviços de busca
│   ├── scraping/           # Serviços de scraping
│   ├── youtube/            # Integração com YouTube
│   └── categories/         # Sistema de categorias
│
├── infrastructure/         # Componentes de infraestrutura
│   ├── __init__.py
│   ├── cache/              # Sistema de cache
│   ├── logging/            # Sistema de logging
│   └── config/             # Configurações
│
├── utils/                  # Utilitários
│   ├── __init__.py
│   ├── concurrency.py      # Utilitários para concorrência
│   └── validators.py       # Validadores
│
├── docs/                   # Documentação
├── tests/                  # Testes
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências
└── README.md               # Documentação principal
```

## Fases e Tarefas

### Fase 1: Preparação e Estruturação ✅

#### Tarefa 1.1: Criar a nova estrutura de diretórios ✅

- **1.1.1**: Criar os diretórios principais (api, core, services, infrastructure, utils, tests) ✅
- **1.1.2**: Criar os subdiretórios em services (search, scraping, youtube, categories) ✅
- **1.1.3**: Criar os subdiretórios em infrastructure (cache, logging, config) ✅
- **1.1.4**: Criar os subdiretórios em tests (unit, integration) ✅
- **1.1.5**: Adicionar arquivos **init**.py em todos os diretórios ✅

#### Tarefa 1.2: Definir interfaces abstratas ✅

- **1.2.1**: Criar interface abstrata para o sistema de cache (CacheService) ✅
- **1.2.2**: Criar interface abstrata para o sistema de scraping (ScraperService) ✅
- **1.2.3**: Criar interface abstrata para o sistema de busca (SearchService) ✅
- **1.2.4**: Criar interface abstrata para a integração com YouTube (YouTubeService) ✅
- **1.2.5**: Criar interface abstrata para o sistema de categorias (CategoryService) ✅

#### Tarefa 1.3: Configurar ambiente de desenvolvimento ✅

- **1.3.1**: Atualizar requirements.txt com dependências necessárias ✅
- **1.3.2**: Configurar ambiente de testes ✅
- **1.3.3**: Criar scripts de utilidade para desenvolvimento ✅

### Fase 2: Refatoração dos Componentes de Infraestrutura ✅

#### Tarefa 2.1: Refatorar o Sistema de Cache ✅

- **2.1.1**: Implementar MemoryCache baseado no atual simple_cache.py ✅
- **2.1.2**: Adicionar funcionalidades de TTL (Time-To-Live) e LRU (Least Recently Used) ✅
- **2.1.3**: Preparar estrutura para futura implementação de RedisCache ✅
- **2.1.4**: Implementar mecanismos de serialização/deserialização eficientes ✅
- **2.1.5**: Adicionar métricas de uso do cache (hit rate, miss rate, etc.) ✅

#### Tarefa 2.2: Refatorar o Sistema de Logging ✅

- **2.2.1**: Criar um sistema de logging centralizado ✅
- **2.2.2**: Implementar diferentes níveis de log (DEBUG, INFO, WARNING, ERROR) ✅
- **2.2.3**: Adicionar formatação consistente para logs ✅
- **2.2.4**: Implementar rotação de logs para evitar arquivos muito grandes ✅
- **2.2.5**: Adicionar contexto aos logs para facilitar depuração ✅

#### Tarefa 2.3: Refatorar o Sistema de Configuração ✅

- **2.3.1**: Centralizar configurações em settings.py ✅
- **2.3.2**: Implementar carregamento de configurações de diferentes fontes (env, arquivo, etc.) ✅
- **2.3.3**: Adicionar validação de configurações ✅
- **2.3.4**: Implementar configurações específicas para diferentes ambientes (dev, test, prod) ✅
- **2.3.5**: Documentar todas as opções de configuração ✅

### Fase 3: Refatoração dos Serviços ✅

#### Tarefa 3.1: Refatorar o Sistema de Scraping (Prioridade Alta) ✅

- **3.1.1**: Implementar PuppeteerScraper baseado no atual adaptive_scraper.py ✅
- **3.1.2**: Melhorar o pool de instâncias Puppeteer para reutilização eficiente ✅
- **3.1.3**: Implementar RequestsScraper para sites mais simples ✅
- **3.1.4**: Adicionar sistema de fallback entre diferentes métodos de scraping ✅
- **3.1.5**: Implementar limites de concorrência e rate limiting por domínio ✅
- **3.1.6**: Adicionar cache de resultados de scraping ✅
- **3.1.7**: Implementar timeout adaptativo baseado no histórico do site ✅
- **3.1.8**: Adicionar sistema de retry com backoff exponencial ✅

#### Tarefa 3.2: Refatorar o Sistema de Busca ✅

- **3.2.1**: Implementar DuckDuckGoSearch baseado no código atual ✅
- **3.2.2**: Preparar para implementações alternativas (Brave Search) ✅
- **3.2.3**: Adicionar sistema de fallback entre diferentes engines de busca ✅
- **3.2.4**: Implementar cache de resultados de busca ✅
- **3.2.5**: Adicionar rate limiting para evitar bloqueios ✅
- **3.2.6**: Melhorar a qualidade dos resultados com parâmetros de busca otimizados ✅
- **3.2.7**: Implementar busca em paralelo em múltiplas engines ✅

#### Tarefa 3.3: Refatorar a Integração com YouTube (Prioridade Alta) ✅

- **3.3.1**: Implementar YtDlpService baseado no atual youtube_integration.py ✅
- **3.3.2**: Otimizar a busca de vídeos para reduzir o uso de recursos ✅
- **3.3.3**: Implementar cache de resultados de busca no YouTube ✅
- **3.3.4**: Adicionar fallback para a API oficial do YouTube quando disponível ✅
- **3.3.5**: Implementar busca em paralelo com limite de concorrência ✅
- **3.3.6**: Melhorar a relevância dos vídeos retornados ✅
- **3.3.7**: Adicionar extração de metadados adicionais (duração, visualizações, etc.) ✅

#### Tarefa 3.4: Refatorar o Sistema de Categorias ✅

- **3.4.1**: Implementar CategoryDetector baseado no atual categories.py ✅
- **3.4.2**: Melhorar a detecção automática de categorias ✅
- **3.4.3**: Adicionar suporte para categorias personalizadas ✅
- **3.4.4**: Implementar cache de categorias detectadas ✅
- **3.4.5**: Adicionar hierarquia de categorias (categorias e subcategorias) ✅

### Fase 4: Refatoração da Lógica de Negócio ✅

#### Tarefa 4.1: Refatorar o Gerador de Caminhos ✅

- **4.1.1**: Refatorar path_generator.py para seguir o princípio de responsabilidade única ✅
- **4.1.2**: Separar a lógica de geração de árvores da lógica de formatação ✅
- **4.1.3**: Implementar diferentes estratégias de geração de árvores ✅
- **4.1.4**: Melhorar o algoritmo de distribuição de nós ✅
- **4.1.5**: Adicionar validação de árvores geradas ✅
- **4.1.6**: Implementar cache de árvores geradas ✅
- **4.1.7**: Otimizar o algoritmo para reduzir o tempo de processamento ✅

#### Tarefa 4.2: Refatorar o Gerenciador de Conteúdo ✅

- **4.2.1**: Criar content_manager.py para encapsular a lógica de content_sourcing.py ✅
- **4.2.2**: Separar a busca, filtragem e processamento de recursos ✅
- **4.2.3**: Implementar sistema de priorização de recursos ✅
- **4.2.4**: Melhorar a relevância dos recursos retornados ✅
- **4.2.5**: Adicionar suporte para diferentes tipos de recursos ✅
- **4.2.6**: Implementar cache de recursos ✅
- **4.2.7**: Otimizar o processamento de recursos para reduzir o tempo de resposta ✅

#### Tarefa 4.3: Refatorar o Gerenciador de Tarefas ✅

- **4.3.1**: Melhorar o sistema de tarefas assíncronas em task_manager.py ✅
- **4.3.2**: Implementar melhor controle de concorrência ✅
- **4.3.3**: Adicionar sistema de priorização de tarefas ✅
- **4.3.4**: Implementar timeout e cancelamento de tarefas ✅
- **4.3.5**: Melhorar o feedback de progresso em tempo real ✅
- **4.3.6**: Adicionar persistência de tarefas para recuperação após reinicialização ✅
- **4.3.7**: Implementar limpeza automática de tarefas antigas ✅

### Fase 5: Refatoração da API e Finalização

#### Tarefa 5.1: Refatorar os Endpoints ✅

- **5.1.1**: Mover a definição de endpoints para api/endpoints.py ✅
- **5.1.2**: Separar a lógica de roteamento da lógica de negócio ✅
- **5.1.3**: Implementar versionamento de API ✅
- **5.1.4**: Melhorar a documentação dos endpoints ✅
- **5.1.5**: Adicionar validação de parâmetros ✅
- **5.1.6**: Implementar tratamento de erros consistente ✅
- **5.1.7**: Adicionar rate limiting para endpoints públicos ✅

#### Tarefa 5.2: Refatorar os Modelos de Dados ✅

- **5.2.1**: Mover os modelos de dados para api/models.py ✅
- **5.2.2**: Melhorar a validação de dados ✅
- **5.2.3**: Implementar serialização/deserialização eficiente ✅
- **5.2.4**: Adicionar documentação para cada modelo ✅
- **5.2.5**: Implementar conversão entre diferentes formatos (JSON, dict, etc.) ✅

#### Tarefa 5.3: Implementar Testes ✅

- **5.3.1**: Criar testes unitários para cada componente ✅
- **5.3.2**: Criar testes de integração para verificar a interação entre componentes ✅
- **5.3.3**: Implementar testes de performance ✅
- **5.3.4**: Configurar CI/CD para execução automática de testes ✅
- **5.3.5**: Adicionar cobertura de código ✅

#### Tarefa 5.4: Atualizar Documentação ✅

- **5.4.1**: Atualizar README.md com a nova estrutura ✅
- **5.4.2**: Criar documentação para cada componente ✅
- **5.4.3**: Atualizar a documentação da API ✅
- **5.4.4**: Criar guias de contribuição ✅
- **5.4.5**: Documentar o processo de desenvolvimento ✅

## Priorização

Baseado nos bottlenecks identificados, a priorização da refatoração será:

1. **Sistema de Scraping** (Tarefa 3.1) - Maior bottleneck
2. **Sistema de Cache** (Tarefa 2.1) - Crítico para performance
3. **Integração com YouTube** (Tarefa 3.3) - Intensivo em recursos
4. **Sistema de Busca** (Tarefa 3.2) - Alto volume de requisições
5. **Gerador de Caminhos** (Tarefa 4.1) - Complexidade algorítmica
6. **Gerenciador de Tarefas** (Tarefa 4.3) - Concorrência e assincronicidade
7. **API e Modelos** (Tarefas 5.1 e 5.2) - Interface com o usuário

## Estimativa de Tempo

- **Fase 1**: 1-2 dias
- **Fase 2**: 3-5 dias
- **Fase 3**: 5-7 dias
- **Fase 4**: 4-6 dias
- **Fase 5**: 3-5 dias

**Total estimado**: 16-25 dias de trabalho

## Métricas de Sucesso

- Redução do tempo médio de resposta em pelo menos 30%
- Aumento da taxa de sucesso na geração de MCPs para pelo menos 95%
- Redução do uso de memória em pelo menos 20%
- Cobertura de testes de pelo menos 80%
- Código mais modular e fácil de manter (medido por métricas de complexidade)

## Riscos e Mitigações

### Riscos

1. **Regressões funcionais**: A refatoração pode introduzir bugs ou alterar o comportamento existente
2. **Complexidade excessiva**: A aplicação dos princípios SOLID pode levar a uma estrutura muito complexa
3. **Tempo de desenvolvimento**: A refatoração pode levar mais tempo que o estimado
4. **Dependências externas**: Mudanças em APIs externas podem afetar a refatoração

### Mitigações

1. **Testes abrangentes**: Implementar testes antes e durante a refatoração
2. **Refatoração incremental**: Refatorar um componente por vez e validar antes de prosseguir
3. **Revisões de código**: Realizar revisões frequentes para garantir a qualidade
4. **Documentação detalhada**: Documentar todas as mudanças e decisões de design

## Conclusão

Este plano de refatoração visa transformar o MCP Server em uma aplicação mais robusta, performática e fácil de manter, aplicando os princípios SOLID de forma pragmática. A abordagem incremental permitirá entregar valor continuamente enquanto reduz os riscos associados a grandes refatorações.
