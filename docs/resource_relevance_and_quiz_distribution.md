# Melhorias na Relevância de Recursos e Distribuição de Quizzes

Este documento descreve as melhorias feitas no MCP Server para garantir que os recursos correspondam ao tópico solicitado e que os quizzes sejam distribuídos de forma equilibrada pela árvore de aprendizagem.

## 1. Relevância de Recursos

### Problema

Anteriormente, o MCP Server dependia apenas de consultas de busca para encontrar recursos relevantes. Não havia verificação se o conteúdo dos recursos realmente correspondia ao tópico. Por exemplo, quando um usuário pesquisava por um tópico como "culinária", ele poderia receber recursos de programação se os resultados da busca estivessem contaminados.

### Solução

Implementamos um sistema de pontuação de relevância baseado em TF-IDF (Term Frequency-Inverse Document Frequency) para filtrar recursos irrelevantes:

1. **Pontuação de Relevância**: Cada recurso é pontuado com base em sua relevância para o tópico usando TF-IDF e similaridade de cosseno.

   - Palavras do título recebem peso 3x (mais importantes)
   - Palavras da descrição recebem peso 2x (importantes, mas menos que os títulos)
   - Stopwords específicas do idioma são removidas

2. **Filtragem**: Recursos abaixo de um limite mínimo de relevância (0,3) são filtrados.

3. **Mecanismo de Fallback**: Se a filtragem remover muitos recursos, os 3 recursos mais relevantes são mantidos independentemente do limite.

### Benefícios

- Os recursos agora têm muito mais probabilidade de corresponder ao tópico solicitado
- Recursos irrelevantes são filtrados
- A árvore de aprendizagem contém conteúdo mais coerente e específico ao tópico

## 2. Distribuição de Quizzes

### Problema

Anteriormente, os quizzes eram atribuídos aleatoriamente aos nós de lição com uma probabilidade de 30%. Não havia garantia de uma distribuição uniforme pela árvore de aprendizagem, e as perguntas dos quizzes eram placeholders genéricos não baseados nos recursos reais.

### Solução

Implementamos um algoritmo de distribuição estratégica de quizzes:

1. **Análise da Árvore**: O algoritmo analisa a estrutura da árvore para identificar ramos e níveis.

2. **Distribuição Estratégica**: Os quizzes são distribuídos para garantir:

   - Pelo menos um quiz em cada ramo principal (quando possível)
   - Distribuição entre diferentes níveis (iniciante, intermediário, avançado)
   - Espaçamento entre nós de quiz para evitar quizzes adjacentes
   - Porcentagem alvo de nós com quizzes (25%)

3. **Geração Aprimorada de Quizzes**:
   - Palavras-chave são extraídas dos recursos em cada nó
   - Perguntas são geradas com base nessas palavras-chave
   - Diferentes tipos de perguntas são usados com base na posição (definição, propósito, relacionamento, etc.)
   - Perguntas genéricas são usadas como fallback quando palavras-chave não estão disponíveis

### Benefícios

- Os quizzes agora estão distribuídos uniformemente pela árvore de aprendizagem
- As perguntas dos quizzes são mais relevantes para o conteúdo do nó
- Há um melhor equilíbrio de tipos e níveis de dificuldade de quizzes
- A experiência de aprendizagem é mais coerente e estruturada

## Detalhes de Implementação

A implementação envolveu a adição de novas funções em:

1. `content_sourcing.py`:

   - `score_resource_relevance()`: Pontua recursos com base na relevância para o tópico
   - `filter_resources_by_relevance()`: Filtra recursos com base nas pontuações de relevância

2. `path_generator.py`:
   - `map_tree_structure()`: Mapeia a estrutura da árvore com relacionamentos pai-filho
   - `identify_branches()`: Identifica todos os ramos (caminhos da raiz até as folhas)
   - `categorize_nodes_by_level()`: Categoriza nós por seu nível na árvore
   - `select_quiz_nodes()`: Seleciona nós para quizzes garantindo distribuição uniforme
   - `distribute_quizzes()`: Distribui quizzes estrategicamente pela árvore de aprendizagem
   - `generate_quiz()` aprimorado: Gera perguntas de quiz mais relevantes

Essas melhorias garantem que o MCP Server forneça caminhos de aprendizagem mais relevantes e melhor estruturados para qualquer tópico.
