# Tarefas de Implementação do Servidor MCP

Este ficheiro detalha as tarefas passo-a-passo para a implementação do servidor MCP, destinado a ser seguido por uma IA. Assume-se o uso de Python e FastAPI conforme definido no `planning.md`.

## Fase 1: Configuração do Projeto e API Básica

1.  **[ ] Criar Estrutura do Projeto:**
    *   Criar diretório raiz do projeto.
    *   Inicializar ambiente virtual Python: `python -m venv venv`
    *   Ativar ambiente virtual: `source venv/bin/activate` (Linux/macOS) ou `venv\Scripts\activate` (Windows).
2.  **[ ] Instalar Dependências Iniciais:**
    *   `pip install fastapi uvicorn[standard] python-dotenv`
    *   Criar `requirements.txt`: `pip freeze > requirements.txt`
3.  **[ ] Criar Ficheiro Principal da API (`main.py`):**
    *   Importar `FastAPI`.
    *   Instanciar a app: `app = FastAPI()`
    *   Criar um endpoint de health check `/health`:
        ```python
        @app.get("/health")
        async def health_check():
            return {"status": "ok"}
        ```
4.  **[ ] Definir Endpoint Principal (`/generate_mcp`):**
    *   Criar um endpoint `GET /generate_mcp`:
        ```python
        from fastapi import Query, HTTPException

        @app.get("/generate_mcp")
        async def generate_mcp_endpoint(topic: str = Query(..., min_length=3)):
            # Placeholder: Retornar dados estáticos por agora
            print(f"Received request for topic: {topic}")
            # TODO: Implementar lógica de geração
            # Temporariamente, retornar uma resposta simples ou o JSON exemplo (hardcoded)
            return {"message": "MCP generation in progress for topic", "topic": topic}
        ```
5.  **[ ] Configurar Uvicorn para Execução Local:**
    *   Executar o servidor localmente: `uvicorn main:app --reload`
    *   Testar os endpoints `/health` e `/generate_mcp?topic=teste` no browser ou com `curl`.
6.  **[ ] Definir Modelos Pydantic (Schema JSON):**
    *   Criar um ficheiro `schemas.py`.
    *   Definir modelos Pydantic que espelhem **exatamente** a estrutura JSON fornecida no pedido inicial (incluindo `MCP`, `Node`, `Resource`, `Metadata`, `Quiz`, `Question`, etc.). Aninhar os modelos conforme necessário.
    *   Atualizar o endpoint `/generate_mcp` para usar o modelo `MCP` como `response_model`.

## Fase 2: Implementação do Content Sourcing Module

1.  **[ ] Criar Módulo `content_sourcing.py`:**
    *   Criar um ficheiro `content_sourcing.py`.
    *   Definir uma função principal, e.g., `find_resources(topic: str) -> list[schemas.Resource]`.
2.  **[ ] Integrar API de Busca (Exemplo: DuckDuckGo):**
    *   Instalar biblioteca: `pip install -U duckduckgo_search`
    *   Implementar função para buscar diferentes tipos de conteúdo usando `ddg` ou similar. Exemplo:
        ```python
        from duckduckgo_search import DDGS

        def search_web(query: str, max_results: int = 5):
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({"title": r.get('title'), "url": r.get('href')}) # Simplificado
            return results
        ```
    *   Na função `find_resources`, chamar `search_web` com queries variadas (e.g., "`{topic}` tutorial", "`{topic}` documentation", "`{topic}` exercises", "`{topic}` video").
    *   Mapear os resultados para o modelo `schemas.Resource`, definindo o `type` com base na query ou análise simples da URL/título (e.g., se 'youtube.com' na URL, type='video'). Definir valores default para campos como `duration`, `readTime`, `difficulty`.
3.  **[ ] Implementar Web Scraping Básico (Opcional, mas Recomendado):**
    *   Instalar bibliotecas: `pip install requests beautifulsoup4 lxml`
    *   Identificar 1-2 sites *confiáveis* e *estáveis* relevantes para muitos tópicos de programação (e.g., `flutter.dev/docs`, `developer.mozilla.org`).
    *   Criar funções específicas de scraping para esses sites (e.g., `scrape_flutter_docs(topic)`).
    *   Usar `requests` para obter o HTML e `BeautifulSoup` para extrair títulos, links e talvez descrições de secções relevantes.
    *   **Importante:** Incluir `User-Agent` nos headers do `requests`. Respeitar `robots.txt` (requer biblioteca adicional ou verificação manual). Implementar tratamento de erros (timeouts, erros HTTP).
    *   Adicionar os resultados do scraping à lista de recursos encontrados.
4.  **[ ] Unificar e Limpar Recursos:**
    *   Na função `find_resources`, agregar resultados de todas as fontes (busca, scraping).
    *   Remover duplicados (baseado na URL).
    *   Limitar o número total de recursos para evitar sobrecarga.
    *   Retornar a lista final de `schemas.Resource`.
5.  **[ ] Integrar com API Principal:**
    *   No `main.py`, importar e chamar `content_sourcing.find_resources(topic)` dentro do endpoint `/generate_mcp`.
    *   Por agora, retornar a lista de recursos encontrados como parte da resposta JSON para teste.

## Fase 3: Implementação do Path Generation Module

1.  **[ ] Criar Módulo `path_generator.py`:**
    *   Criar um ficheiro `path_generator.py`.
    *   Definir uma função principal, e.g., `generate_learning_path(topic: str, resources: list[schemas.Resource]) -> schemas.MCP`.
2.  **[ ] Implementar Lógica de Estruturação (Heurística Simples V1):**
    *   Dentro de `generate_learning_path`:
        *   **Criar Metadados Globais:** Gerar `id` (e.g., `topic.lower().replace(' ', '_')`), `title` (e.g., `f"Fundamentos de {topic.title()}"`), `description`, `metadata` (com valores default/estimados para `difficulty`, `estimatedHours`, `tags`).
        *   **Agrupar Recursos:** Tentar agrupar recursos por palavras-chave no título/descrição (e.g., "introdução", "básico", "widgets", "avançado", "projeto", "exercício", "quiz"). Criar categorias simples.
        *   **Criar Nós (`nodes`):** Para cada categoria/grupo, criar um `schemas.Node`.
            *   Gerar `id` único para cada nó (e.g., `intro_{topic_id}`).
            *   Definir `title` e `description` para o nó.
            *   Atribuir os `resources` correspondentes a este nó.
            *   Definir o `type` do nó (e.g., 'lesson', 'exercise_set', 'project_idea'). Se encontrar recursos tipo 'exercise', pode criar um nó 'lesson' com esses exercícios, ou um nó 'quiz' placeholder.
            *   Definir `state` como 'available' por default.
            *   Definir `visualPosition` com valores placeholder (e.g., `{"x": 0, "y": level, "level": level}`).
        *   **Definir Pré-requisitos (`prerequisites`):** Estabelecer uma sequência linear simples. O nó 2 requer o nó 1, o nó 3 requer o nó 2, etc. O primeiro nó (root) tem `prerequisites` vazio. Atribuir o `id` do primeiro nó ao `rootNodeId` do MCP.
        *   **Gerar Quizzes Placeholder:** Se a lógica identificar um ponto adequado (e.g., após um conjunto de lições), criar um nó do tipo `quiz` com título, descrição, mas sem `questions` detalhadas (lista vazia ou com 1-2 perguntas placeholder). Definir `passingScore` default.
        *   **Gerar Projeto Placeholder:** Adicionar um nó final do tipo `project` se apropriado, com descrição do que se espera.
3.  **[ ] Construir Objeto MCP:**
    *   Montar o objeto `schemas.MCP` completo com todos os metadados, `rootNodeId`, e o dicionário `nodes`.
    *   Retornar o objeto `MCP`.
4.  **[ ] Integrar com API Principal:**
    *   No `main.py`, após obter os `resources`, chamar `path_generator.generate_learning_path(topic, resources)`.
    *   Retornar o objeto `MCP` resultante como resposta do endpoint `/generate_mcp`. Utilizar `response_model=schemas.MCP` para garantir a formatação correta.

## Fase 4: Refinamento, Tratamento de Erros e Logging

1.  **[ ] Implementar Tratamento de Erros:**
    *   No `content_sourcing`: Adicionar `try...except` blocos para falhas de rede, erros de parsing, limites de API. Retornar lista vazia ou levantar exceções customizadas.
    *   No `path_generator`: Lidar com o caso de não haver recursos suficientes para gerar um caminho significativo.
    *   No `main.py`: Usar `try...except` para capturar exceções dos módulos e retornar `HTTPException` do FastAPI com status codes apropriados (e.g., 404 se nenhum recurso encontrado, 500 para erros internos).
2.  **[ ] Adicionar Logging Básico:**
    *   Instalar `loguru` (opcional, mas bom): `pip install loguru`
    *   Configurar logging básico no `main.py` para registar pedidos recebidos, tópicos, número de recursos encontrados, e quaisquer erros.
3.  **[ ] Limpeza e Comentários:**
    *   Rever todo o código. Adicionar type hints em todas as funções.
    *   Adicionar comentários explicando a lógica complexa, especialmente nas heurísticas de sourcing e path generation.
    *   Garantir que os nomes das variáveis e funções são claros.
4.  **[ ] Testar Exaustivamente:**
    *   Testar com vários tópicos (comuns, específicos, obscuros).
    *   Verificar se o JSON de saída é sempre válido e corresponde ao schema.
    *   Testar casos de erro (e.g., tópico muito curto, falha na busca).

## Fase 5: Preparação para Deployment

1.  **[ ] Atualizar `requirements.txt`:**
    *   `pip freeze > requirements.txt`
2.  **[ ] Configurar Variáveis de Ambiente:**
    *   Se usar API keys, movê-las para um ficheiro `.env`. Usar `python-dotenv` para carregá-las localmente. `pip install python-dotenv`.
    *   No código, aceder às keys via `os.getenv("API_KEY_NAME")`.
    *   **NUNCA** commitar o ficheiro `.env` ou as keys diretamente no código. Adicionar `.env` ao `.gitignore`.
3.  **[ ] (Opcional, Recomendado para Fly.io) Criar `Dockerfile`:**
    *   Criar um `Dockerfile` básico para a aplicação Python/FastAPI. Exemplo:
      ```dockerfile
      FROM python:3.9-slim

      WORKDIR /app

      COPY requirements.txt .
      RUN pip install --no-cache-dir -r requirements.txt

      COPY . .

      # PORT é geralmente fornecido pelo ambiente de alojamento
      ENV PORT=8080
      EXPOSE 8080

      CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
      ```
4.  **[ ] Adicionar `Procfile` (Para Heroku/Render sem Docker):**
    *   Criar ficheiro `Procfile` (sem extensão) na raiz:
      ```
      web: uvicorn main:app --host 0.0.0.0 --port $PORT
      ```

## Fase 6: Deployment no Provedor Gratuito

1.  **[ ] Escolher Provedor:** Selecionar Render.com, Fly.io, ou outro.
2.  **[ ] Criar Conta e Configurar Aplicação:**
    *   Seguir a documentação do provedor escolhido para criar um novo "Web Service" (Render) ou "App" (Fly.io).
    *   Ligar ao repositório Git.
    *   Configurar o ambiente (Python, ou Docker se usar Dockerfile).
    *   Definir comandos de build e start (ver Fase 5).
    *   Configurar variáveis de ambiente necessárias (e.g., API keys) na interface do provedor.
3.  **[ ] Realizar o Deploy:** Iniciar o processo de build e deploy.
4.  **[ ] Testar Endpoint Público:** Aceder à URL fornecida pelo provedor (e.g., `https://<app-name>.onrender.com/generate_mcp?topic=flutter`) e verificar a resposta.
5.  **[ ] Monitorizar:** Observar logs e métricas de uso para garantir que se mantém dentro dos limites do free tier.