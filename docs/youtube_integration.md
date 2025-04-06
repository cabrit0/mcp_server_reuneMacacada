# Integração com YouTube e Sistema de Categorias

Este documento descreve a implementação da integração com YouTube e do sistema de categorias no MCP Server.

## 1. Integração com YouTube

### Visão Geral

A integração com o YouTube permite que o MCP Server encontre e inclua vídeos relevantes nos planos de aprendizagem gerados. Isso enriquece a experiência do usuário, fornecendo conteúdo multimídia além dos recursos textuais.

### Implementação

A integração foi implementada usando a biblioteca `yt-dlp`, que permite buscar vídeos do YouTube sem depender da API oficial do YouTube. Isso evita limitações de cota e simplifica a implementação.

#### Principais Componentes

1. **Módulo `youtube_integration.py`**:

   - Função `search_youtube_videos`: Busca vídeos no YouTube relacionados a um tópico
   - Função `get_best_thumbnail`: Obtém a melhor thumbnail disponível para um vídeo
   - Função `parse_duration`: Converte a duração do vídeo para minutos

2. **Integração com o Sistema de Recursos**:
   - Os vídeos do YouTube são adicionados ao conjunto de recursos encontrados na web
   - Cada vídeo inclui informações como título, descrição, duração e thumbnail
   - Os vídeos são filtrados por relevância junto com os outros recursos

### Exemplo de Uso

```python
# Buscar vídeos do YouTube
youtube_resources = await search_youtube_videos("python programming", max_results=5, language="pt")

# Acessar informações do vídeo
for video in youtube_resources:
    print(f"Título: {video.title}")
    print(f"URL: {video.url}")
    print(f"Duração: {video.duration} minutos")
    print(f"Thumbnail: {video.thumbnail}")
```

## 2. Sistema de Categorias

### Visão Geral

O sistema de categorias permite que o MCP Server gere planos de aprendizagem mais relevantes e específicos para diferentes tipos de tópicos. Cada categoria tem suas próprias palavras-chave, subtópicos e consultas de busca.

### Categorias Implementadas

1. **Tecnologia e Programação**
2. **Finanças e Economia**
3. **Saúde e Bem-estar**
4. **Educação e Aprendizagem**
5. **Artes e Humanidades**
6. **Ciências**
7. **Negócios e Empreendedorismo**
8. **Estilo de Vida e Hobbies**
9. **Geral** (categoria padrão)

### Implementação

O sistema de categorias foi implementado no módulo `categories.py` e integrado aos processos de geração de planos de aprendizagem.

#### Principais Componentes

1. **Módulo `categories.py`**:

   - Definição das categorias com palavras-chave, subtópicos e consultas de busca
   - Função `detect_category`: Detecta a categoria mais provável para um tópico
   - Função `get_subtopics_for_category`: Obtém subtópicos específicos para uma categoria
   - Função `get_resource_queries_for_category`: Obtém consultas de busca específicas para uma categoria

2. **Integração com o Gerador de Planos**:
   - A categoria é detectada no início do processo de geração
   - Subtópicos específicos da categoria são usados para estruturar o plano
   - Consultas de busca específicas da categoria são usadas para encontrar recursos relevantes

### Especificação Manual de Categoria

O sistema agora permite que o usuário especifique manualmente a categoria desejada através do parâmetro `category` na API. Isso é útil quando:

- O usuário sabe exatamente qual categoria deseja usar
- A detecção automática não identifica corretamente a categoria
- O tópico é ambíguo e poderia pertencer a múltiplas categorias

### Exemplo de Uso da API

```
# Detecção automática de categoria
http://localhost:8000/generate_mcp?topic=python

# Especificação manual de categoria
http://localhost:8000/generate_mcp?topic=python&category=technology

# Forçar o uso da categoria geral
http://localhost:8000/generate_mcp?topic=python&category=general
```

### Exemplo de Uso em Código

```python
# Detectar categoria para um tópico
category = detect_category("literacia financeira")  # Retorna "finance"

# Obter subtópicos específicos da categoria
subtopics = get_subtopics_for_category("literacia financeira", count=10)

# Obter consultas de busca específicas da categoria
queries = get_resource_queries_for_category("literacia financeira")

# Gerar plano de aprendizagem com categoria específica
mcp = path_generator.generate_learning_path("python", resources, category="technology")
```

## 3. Benefícios das Novas Funcionalidades

1. **Conteúdo Mais Relevante**:

   - Recursos mais específicos para cada tipo de tópico
   - Vídeos do YouTube complementam os recursos textuais
   - Estrutura de aprendizagem adaptada ao tipo de conteúdo

2. **Experiência de Aprendizagem Enriquecida**:

   - Conteúdo multimídia para diferentes estilos de aprendizagem
   - Thumbnails fornecem contexto visual para os vídeos
   - Subtópicos mais relevantes para cada área de conhecimento

3. **Melhor Organização do Conteúdo**:
   - Planos de aprendizagem estruturados de acordo com a categoria do tópico
   - Terminologia específica para cada área de conhecimento
   - Consultas de busca otimizadas para cada tipo de conteúdo

## 4. Limitações e Considerações

1. **Detecção de Categoria**:

   - A detecção de categoria é baseada em palavras-chave e pode não ser perfeita
   - Tópicos muito específicos ou interdisciplinares podem ser classificados incorretamente

2. **Busca de Vídeos**:

   - A biblioteca `yt-dlp` depende da interface do YouTube e pode ser afetada por mudanças
   - A qualidade dos resultados depende dos termos de busca e do algoritmo do YouTube

3. **Desempenho**:
   - A busca de vídeos adiciona um tempo extra ao processo de geração
   - O processamento de thumbnails aumenta o tamanho da resposta JSON

## 5. Trabalhos Futuros

1. **Melhorias na Detecção de Categoria**:

   - Implementar um sistema de classificação mais avançado usando NLP
   - Adicionar mais categorias e subcategorias

2. **Aprimoramento da Busca de Vídeos**:

   - Implementar filtragem por duração e qualidade
   - Adicionar suporte para outros tipos de conteúdo multimídia

3. **Integração com a API Oficial do YouTube**:
   - Implementar como opção para casos que exigem recursos avançados
   - Adicionar sistema de fallback para quando a cota da API for atingida
