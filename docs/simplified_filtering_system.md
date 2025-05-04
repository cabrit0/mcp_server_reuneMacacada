# Simplificação do Sistema de Filtragem de Recursos

Este documento explica como o sistema de filtragem de recursos foi simplificado no MCP Server.

## Problema Identificado

A funcionalidade original de detecção de similaridade usando TF-IDF e similaridade do cosseno estava causando um problema crítico: o servidor não conseguia encontrar mais que 3 nós para a árvore de aprendizagem.

## Causa do Problema

A detecção de similaridade estava filtrando recursos de forma muito agressiva, resultando em:

1. Remoção excessiva de recursos que poderiam ser úteis
2. Número insuficiente de recursos para criar uma árvore de aprendizagem adequada
3. Falha na validação de tamanho mínimo da árvore (mínimo de 12 nós concretos)

## Mudanças Realizadas

Para resolver o problema, as seguintes mudanças foram implementadas:

1. **Simplificação do sistema de filtragem**:

   - Substituição do algoritmo TF-IDF por um sistema mais simples baseado em correspondência de palavras-chave
   - Renomeação de "similaridade" para "relevância" para melhor refletir a funcionalidade atual

2. **Melhoria na interface do usuário**:

   - Mantido o parâmetro `similarity_threshold` para compatibilidade com código existente
   - Atualização das mensagens de log para refletir a nova abordagem

3. **Otimização de desempenho**:
   - Remoção de código não utilizado
   - Simplificação do processo de filtragem para melhorar o desempenho

## Arquivos Afetados

- `core/content_sourcing/semantic_filter_service.py`: Simplificado para usar correspondência de palavras-chave
- `core/content_sourcing/default_content_source_service.py`: Atualizado para usar o novo sistema de filtragem
- `api/routers/mcp_router.py`: Atualização das mensagens de log

## Benefícios da Simplificação

A simplificação do sistema de filtragem traz os seguintes benefícios:

1. **Maior número de nós**: O servidor agora pode encontrar mais nós para a árvore de aprendizagem
2. **Maior diversidade de conteúdo**: Mais recursos são incluídos na árvore
3. **Melhor experiência do usuário**: Menos falhas na geração de MCPs
4. **Melhor desempenho**: O sistema simplificado é mais rápido e usa menos recursos

## Implementação Atual

O sistema atual de filtragem usa uma abordagem simples baseada em correspondência de palavras-chave:

1. Verifica se o tópico está presente no título ou descrição do recurso
2. Verifica se palavras individuais do tópico estão presentes no título ou descrição
3. Considera o tipo de recurso (tutorial, documentação, artigo, etc.)
4. Atribui uma pontuação de relevância com base nesses fatores

Esta abordagem é mais leve e menos agressiva na filtragem de recursos, permitindo a criação de árvores de aprendizagem mais completas e diversificadas.
