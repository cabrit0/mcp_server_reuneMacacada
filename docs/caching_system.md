# Sistema de Cache do MCP Server

Este documento descreve o sistema de cache implementado no MCP Server para melhorar a performance e reduzir o tempo de resposta.

## Visão Geral

O MCP Server implementa um sistema de cache em múltiplos níveis para armazenar e recuperar dados frequentemente acessados, como resultados de buscas, conteúdo de páginas web e MCPs gerados. O sistema de cache é projetado para ser eficiente, escalável e resiliente a falhas.

## Implementação Atual

### Cache em Memória

A implementação atual usa um cache em memória simples e eficiente, implementado na classe `SimpleCache` no arquivo `simple_cache.py`. Este cache:

- Armazena dados em memória usando um dicionário Python
- Implementa políticas de expiração (TTL) para diferentes tipos de dados
- Usa uma estratégia LRU (Least Recently Used) para evitar crescimento excessivo da memória
- Fornece uma interface similar ao Redis para facilitar a migração futura

### Tipos de Dados Cacheados

O sistema de cache armazena os seguintes tipos de dados:

1. **Resultados de Busca**: Resultados de buscas no DuckDuckGo para tópicos específicos

   - TTL: 1 dia (86400 segundos)
   - Chave: `search:{topic}_{max_results}_{language}_{category}`

2. **Conteúdo de Páginas**: Conteúdo HTML e metadados de páginas web

   - TTL: 1 semana (604800 segundos)
   - Chave: `page:{url}` ou `resource:{url}`

3. **MCPs Gerados**: Planos de aprendizagem completos
   - TTL: 30 dias (2592000 segundos)
   - Chave: `mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}`

### Políticas de Expiração

O sistema de cache implementa diferentes políticas de expiração para diferentes tipos de dados:

- **Resultados de Busca**: Expiram após 1 dia, pois os resultados de busca podem mudar com frequência
- **Conteúdo de Páginas**: Expiram após 1 semana, pois o conteúdo das páginas muda com menos frequência
- **MCPs Gerados**: Expiram após 30 dias, pois os planos de aprendizagem são relativamente estáveis

### Estratégia LRU

Para evitar o crescimento excessivo da memória, o sistema de cache implementa uma estratégia LRU (Least Recently Used) que remove os itens menos recentemente acessados quando o cache atinge seu tamanho máximo.

## Implementação Futura: Cache Distribuído com Redis

No futuro, planejamos migrar o sistema de cache para uma solução distribuída usando Redis. Esta migração trará os seguintes benefícios:

- **Persistência**: O cache será preservado entre reinicializações do servidor
- **Escalabilidade**: O cache poderá ser compartilhado entre múltiplas instâncias do servidor
- **Eficiência**: Redis é otimizado para operações de cache e oferece melhor performance

### Arquitetura Planejada

A arquitetura planejada para o cache distribuído inclui:

1. **Redis como Armazenamento Principal**: Todos os dados serão armazenados no Redis
2. **Cache em Memória como Primeiro Nível**: Um cache em memória será mantido como primeiro nível para dados frequentemente acessados
3. **Fallback para Cache em Memória**: Se o Redis não estiver disponível, o sistema usará o cache em memória como fallback

### Migração

A migração para o Redis será feita de forma transparente, sem necessidade de modificar o código que usa o cache. Isso é possível porque a interface do `SimpleCache` foi projetada para ser similar à interface do Redis.

## Uso do Sistema de Cache

### Como Armazenar Dados no Cache

```python
from simple_cache import simple_cache

# Armazenar um valor no cache
simple_cache.setex("chave", 3600, "valor")  # TTL de 1 hora
```

### Como Recuperar Dados do Cache

```python
from simple_cache import simple_cache

# Recuperar um valor do cache
valor = simple_cache.get("chave")
if valor:
    # Usar o valor
    print(f"Valor recuperado do cache: {valor}")
else:
    # Valor não encontrado no cache
    print("Valor não encontrado no cache")
```

### Como Limpar o Cache

#### Via API

O MCP Server fornece um endpoint para limpar o cache:

```
POST /clear_cache?pattern={pattern}
```

Onde `pattern` é um padrão para correspondência de chaves. O padrão padrão é "\*" que limpa todo o cache.

Exemplos:

- `POST /clear_cache` - Limpa todo o cache
- `POST /clear_cache?pattern=mcp:*` - Limpa apenas o cache de MCPs
- `POST /clear_cache?pattern=search:*` - Limpa apenas o cache de resultados de busca

#### Via Código

```python
from simple_cache import simple_cache

# Limpar todo o cache
simple_cache.clear()

# Limpar cache com base em um padrão
simple_cache.clear("mcp:*")

# Remover um item específico
simple_cache.delete("chave")
```

## Monitoramento e Métricas

Para monitorar a eficiência do sistema de cache, planejamos implementar as seguintes métricas:

1. **Taxa de Cache Hit**: Porcentagem de requisições atendidas pelo cache
2. **Tamanho do Cache**: Número de itens no cache
3. **Tempo de Acesso**: Tempo médio para acessar dados no cache
4. **Economia de Tempo**: Tempo economizado usando o cache em vez de gerar os dados novamente

## Conclusão

O sistema de cache é uma parte fundamental do MCP Server, permitindo melhorar significativamente a performance e reduzir o tempo de resposta. A implementação atual em memória já traz benefícios significativos, e a migração futura para Redis trará ainda mais melhorias em termos de persistência, escalabilidade e eficiência.
