# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-04-06

### Adicionado

- Integração com YouTube para incluir vídeos relevantes em cada nó da árvore de aprendizagem
- Sistema de categorias para gerar conteúdo mais específico para diferentes tipos de tópicos
- Parâmetro `category` na API para permitir especificação manual da categoria
- Thumbnails para vídeos do YouTube
- Documentação completa para todas as novas funcionalidades
- Filtragem de recursos baseada em TF-IDF para garantir relevância
- Distribuição estratégica de quizzes pela árvore de aprendizagem

### Modificado

- Melhorias na geração de subtópicos para diferentes categorias
- Otimizações de desempenho para o Render
- Atualização das dependências para versões mais recentes
- Melhoria na documentação da API

### Removido

- Funcionalidade de detecção de similaridade que limitava o número de nós
- Arquivos temporários e de teste desnecessários

## [0.1.0] - 2025-03-15

### Adicionado

- Versão inicial do servidor MCP
- Geração de planos de aprendizagem para qualquer tópico
- Busca de recursos na web
- Suporte a múltiplos idiomas
- Sistema de cache para melhorar o desempenho
