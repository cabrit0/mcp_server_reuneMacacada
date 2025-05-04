# Filtragem Semântica de Recursos

Este documento descreve a implementação da filtragem semântica de recursos no MCP Server.

## Visão Geral

A filtragem semântica é uma técnica que permite comparar a relevância entre o tópico solicitado pelo usuário e os recursos encontrados durante a busca. Isso garante que apenas recursos relevantes sejam incluídos na árvore de aprendizado.

## Implementação

A implementação da filtragem semântica no MCP Server utiliza uma abordagem baseada em correspondência de palavras-chave e heurísticas:

1. **Correspondência de Palavras-chave**: Verifica se o tópico ou suas palavras-chave estão presentes no título e na descrição do recurso.

2. **Sistema de Pontuação Ponderada**: Atribui pontuações diferentes com base na localização da correspondência:

   - Tópico completo no título: +0.5 pontos
   - Tópico completo na descrição: +0.3 pontos
   - Palavras individuais do tópico no título: +0.2 pontos por palavra
   - Palavras individuais do tópico na descrição: +0.1 pontos por palavra

3. **Boosting por Tipo de Recurso**: Recursos de tipos específicos (tutorial, documentação, artigo) recebem uma pontuação adicional de +0.2 pontos.

4. **Correspondência Exata**: Recursos cujo título corresponde exatamente ao tópico recebem uma pontuação mínima garantida de 0.8.

5. **Remoção de Stopwords**: Palavras comuns (como "o", "a", "de", etc.) são removidas para melhorar a qualidade da análise.

6. **Suporte a Múltiplos Idiomas**: A filtragem semântica suporta vários idiomas, incluindo português, inglês, espanhol, francês, alemão e italiano.

## Arquitetura

A filtragem semântica é implementada através do serviço `SemanticFilterService`, que é integrado ao `DefaultContentSourceService`. O fluxo de funcionamento é:

1. O usuário faz uma solicitação para gerar um MCP com um tópico específico.
2. O `DefaultContentSourceService` busca recursos relevantes usando serviços de busca e scraping.
3. Os recursos encontrados são passados para o `SemanticFilterService`, que calcula a relevância de cada recurso para o tópico.
4. Recursos com relevância abaixo do limiar configurado são removidos.
5. Os recursos restantes são ordenados por relevância e retornados para o gerador de árvore de aprendizado.

## Parâmetros de Configuração

A filtragem semântica pode ser configurada através do parâmetro `similarity_threshold` nos endpoints da API (mantido por compatibilidade):

- `GET /generate_mcp?similarity_threshold=0.15`: Define o limiar mínimo de relevância para inclusão de recursos (0-1).
- `POST /generate_mcp_async?similarity_threshold=0.15`: Versão assíncrona do endpoint acima.

O valor padrão é 0.15, o que significa que recursos com relevância abaixo de 15% serão removidos. Valores mais altos resultam em filtragem mais rigorosa, enquanto valores mais baixos são mais permissivos.

## Mecanismo de Fallback

Para evitar que a filtragem de relevância remova muitos recursos e prejudique a geração da árvore de aprendizado, um mecanismo de fallback foi implementado:

- Se a filtragem remover mais de 75% dos recursos e restarem menos de 5 recursos, o sistema volta a usar a lista original de recursos.
- Isso garante que sempre haja recursos suficientes para gerar uma árvore de aprendizado de qualidade.

## Impacto na Qualidade

A filtragem semântica melhora significativamente a qualidade das árvores de aprendizado geradas pelo MCP Server:

1. **Maior Relevância**: Os recursos incluídos na árvore são mais relevantes para o tópico solicitado.
2. **Menos Ruído**: Recursos não relacionados ou tangenciais são removidos.
3. **Melhor Experiência do Usuário**: A árvore de aprendizado é mais coerente e focada no tópico solicitado.

## Limitações e Trabalhos Futuros

A implementação atual tem algumas limitações:

1. **Abordagem Baseada em Palavras-chave**: A correspondência simples de palavras-chave não captura relações semânticas complexas.
2. **Sem Análise de Contexto**: A análise não considera o contexto em que as palavras aparecem.
3. **Sem Suporte a Sinônimos**: Palavras com significados semelhantes mas diferentes do tópico exato não são reconhecidas.
4. **Dependência de Descrições de Qualidade**: A eficácia da filtragem depende da qualidade das descrições dos recursos.

Trabalhos futuros podem incluir:

1. **Técnicas Avançadas de NLP**: Implementar técnicas mais sofisticadas como embeddings de palavras ou modelos de linguagem.
2. **Análise de Conteúdo Completo**: Analisar o conteúdo completo dos recursos, não apenas título e descrição.
3. **Aprendizado Adaptativo**: Ajustar o limiar de relevância com base no feedback do usuário e na qualidade dos resultados.
4. **Expansão de Consultas**: Expandir o tópico com sinônimos e termos relacionados para melhorar a correspondência.
5. **Suporte a Mais Idiomas**: Adicionar suporte para mais idiomas além dos já implementados.
