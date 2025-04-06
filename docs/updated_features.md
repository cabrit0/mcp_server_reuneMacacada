# Funcionalidades Atualizadas do MCP Server

Este documento descreve as funcionalidades atualizadas do MCP Server, incluindo as melhorias recentes implementadas para torná-lo mais eficiente, flexível e adequado para uso no free tier do Render.

## 1. Suporte para Qualquer Tema

O MCP Server agora é capaz de gerar planos de aprendizagem para qualquer tema, não apenas tópicos de tecnologia.

### Implementação

- Remoção de restrições específicas de tecnologia no código
- Adaptação da geração de subtópicos para funcionar com qualquer assunto
- Melhoria na detecção de recursos relevantes para temas diversos

### Benefícios

- Maior versatilidade do servidor
- Capacidade de atender a uma gama mais ampla de necessidades de aprendizagem
- Melhor experiência do usuário com mais opções de temas

## 2. Parâmetros Opcionais

Foram adicionados novos parâmetros opcionais para personalizar a geração de MCPs:

### Parâmetros Disponíveis

- `topic` (obrigatório): O tópico para o qual gerar o plano de aprendizagem
- `max_resources` (opcional): Número máximo de recursos a incluir (padrão: 15, mín: 5, máx: 30)
- `num_nodes` (opcional): Número de nós a incluir no plano de aprendizagem (padrão: 15, mín: 10, máx: 30)
- `language` (opcional): Idioma preferido para os recursos (padrão: "pt")

### Implementação

- Adição de novos parâmetros na definição do endpoint
- Passagem dos parâmetros para as funções apropriadas
- Validação de valores para garantir que estejam dentro dos limites aceitáveis

### Benefícios

- Maior flexibilidade na geração de MCPs
- Personalização de acordo com as necessidades do usuário
- Controle sobre o tamanho e a complexidade do plano de aprendizagem

## 3. Validação de Tamanho Mínimo

O servidor agora valida se o plano de aprendizagem contém um número mínimo de nós:

### Implementação

- Verificação para garantir pelo menos 10 nós (ou o mínimo especificado)
- Mensagem de erro clara quando não for possível gerar nós suficientes
- Tratamento adequado de exceções HTTP

### Benefícios

- Garantia de qualidade dos planos de aprendizagem
- Feedback claro para o usuário quando um tópico não tem recursos suficientes
- Prevenção de árvores incompletas ou pouco úteis

## 4. Suporte para Português

O servidor agora tem suporte aprimorado para o idioma português:

### Implementação

- Definição de "pt" como idioma padrão
- Adição de termos de busca específicos em português
- Implementação de mapeamento de idioma para região nas buscas
- Adição de cabeçalhos de idioma nas requisições HTTP

### Benefícios

- Melhor experiência para usuários de língua portuguesa
- Resultados mais relevantes para o contexto brasileiro/português
- Maior precisão na busca de recursos em português

## 5. Sistema de Cache em Múltiplos Níveis

Foi implementado um sistema de cache em múltiplos níveis para melhorar a performance:

### Níveis de Cache

1. **Cache de Resultados de Busca**
   - Armazena resultados de buscas na web para evitar chamadas repetidas à API do DuckDuckGo
   - Chave de cache: `query_max_results_language`

2. **Cache de Scraping**
   - Armazena resultados de scraping com Puppeteer e BeautifulSoup
   - Chaves de cache: `puppeteer_url` e `basic_url_language`

3. **Cache de MCP**
   - Armazena MCPs completos gerados para tópicos específicos
   - Chave de cache: `topic_max_resources_num_nodes_language`

### Gerenciamento de Cache

- Limite máximo de entradas no cache (configurável via `MAX_CACHE_SIZE`)
- Remoção automática das entradas mais antigas quando o limite é atingido
- Estratégia de remoção: primeiros 10% das entradas mais antigas ou a entrada mais antiga

### Benefícios

- Redução significativa no tempo de resposta para tópicos já consultados
- Menor consumo de recursos do servidor
- Melhor experiência do usuário com respostas mais rápidas

## 6. Otimizações de Performance para o Render

Foram implementadas várias otimizações para melhorar a performance no free tier do Render:

### Otimizações de Puppeteer

- Redução do número máximo de instâncias concorrentes de Puppeteer (de 5 para 2)
- Timeouts mais agressivos (de 30s para 8s)
- Fechamento rápido de browsers

### Otimizações de Rede

- Redução de delays entre requisições (de 0.1s para 0.05s)
- Limitação do número de recursos processados
- Headers otimizados para melhorar a relevância dos resultados

### Benefícios

- Menor consumo de memória, especialmente importante no free tier do Render
- Maior estabilidade do servidor sob carga
- Respostas mais rápidas e confiáveis

## Exemplo de Uso

```
GET /generate_mcp?topic=história+do+brasil&num_nodes=20&language=pt
```

Este exemplo gerará um plano de aprendizagem sobre a história do Brasil, com aproximadamente 20 nós, em português.

## Configurações Recomendadas

Para o ambiente free tier do Render, recomendamos:

- `MAX_PUPPETEER_INSTANCES = 2`
- `MAX_CACHE_SIZE = 100`
- Timeout de Puppeteer: 8 segundos
- Delay entre requisições: 0.05 segundos
