# Remoção da Detecção de Similaridade

Este documento explica por que a funcionalidade de detecção de similaridade foi removida do MCP Server.

## Problema Identificado

A funcionalidade de detecção de similaridade usando TF-IDF e similaridade do cosseno estava causando um problema crítico: o servidor não conseguia encontrar mais que 3 nós para a árvore de aprendizagem.

## Causa do Problema

A detecção de similaridade estava filtrando recursos de forma muito agressiva, resultando em:

1. Remoção excessiva de recursos que poderiam ser úteis
2. Número insuficiente de recursos para criar uma árvore de aprendizagem adequada
3. Falha na validação de tamanho mínimo da árvore (mínimo de 12 nós concretos)

## Mudanças Realizadas

Para resolver o problema, as seguintes mudanças foram implementadas:

1. **Remoção da integração com o detector de similaridade**:
   - Removido o import e a inicialização do `similarity_detector` em `content_sourcing.py`
   - Removido o bloco de código que aplicava a detecção de similaridade aos recursos

2. **Remoção dos parâmetros de similaridade**:
   - Removido o parâmetro `similarity_threshold` dos endpoints `/generate_mcp` e `/generate_mcp_v2`
   - Removido o parâmetro `similarity_threshold` da função `find_resources`

3. **Atualização dos logs**:
   - Removidas as referências ao `similarity_threshold` nas mensagens de log

## Arquivos Afetados

- `content_sourcing.py`: Removida a integração com o detector de similaridade
- `main.py`: Removidos os parâmetros de similaridade dos endpoints

## Benefícios da Remoção

A remoção da detecção de similaridade traz os seguintes benefícios:

1. **Maior número de nós**: O servidor agora pode encontrar mais nós para a árvore de aprendizagem
2. **Maior diversidade de conteúdo**: Mais recursos são incluídos na árvore
3. **Melhor experiência do usuário**: Menos falhas na geração de MCPs

## Alternativas Consideradas

Antes de remover completamente a funcionalidade, foram consideradas as seguintes alternativas:

1. **Ajustar o limiar de similaridade**: Aumentar o valor padrão para ser mais permissivo
2. **Tornar a detecção opcional**: Adicionar um parâmetro para ativar/desativar a detecção
3. **Implementar uma versão mais leve**: Usar uma abordagem mais simples para detecção de similaridade

No entanto, a remoção completa foi a solução mais eficaz para garantir o funcionamento adequado do servidor.

## Possível Reimplementação Futura

No futuro, a detecção de similaridade pode ser reimplementada com as seguintes melhorias:

1. **Algoritmo mais preciso**: Usar embeddings ou outras técnicas mais sofisticadas
2. **Abordagem mais conservadora**: Remover apenas recursos muito similares (>0.9)
3. **Integração com feedback do usuário**: Aprender com o feedback para melhorar a detecção
4. **Testes mais abrangentes**: Garantir que a detecção não afete negativamente a qualidade das árvores
