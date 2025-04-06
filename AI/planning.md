# Planeamento do Servidor MCP Gratuito

## 1. Introdução

Este documento descreve o plano de alto nível para a criação de um servidor MCP (Master Content Planner). O objetivo principal é fornecer um endpoint de API que, ao receber um tópico como input (via prompt), gera dinamicamente uma estrutura JSON representando um plano de aprendizagem sobre esse tópico. Este plano agregará recursos gratuitos disponíveis publicamente na web, como vídeos, artigos, documentação e exercícios.

**Restrição Principal:** O servidor deve operar dentro dos limites de serviços **gratuitos** ou com tiers gratuitos generosos, tanto para alojamento como para quaisquer APIs externas utilizadas.

**Público-Alvo:** Uma Inteligência Artificial (IA) encarregada da implementação.

**Integração:** O servidor será consumido por uma aplicação Flutter, esperando uma resposta JSON no formato especificado.

## 2. Arquitetura Proposta

Propõe-se uma arquitetura baseada em microserviços ou um monólito simples, focada na funcionalidade principal e na restrição de custo.

+-------------------+ +---------------------+ +------------------------+ +-----------------+ +-------------------+
| Flutter App |----->| API Endpoint |----->| Content Sourcing Module|<---->| Web/Search APIs |----->| Internet Content |
| (Cliente) | | (FastAPI/Flask) | | (Scraping/API Clients)| | (Google, DDG, YT)| | (Docs, Videos...) |
+-------------------+ +---------------------+ +------------------------+ +-----------------+ +-------------------+
|
| Input: Topic
| Output: JSON MCP
V
+-------------------------+
| Path Generation Module |
| (Structuring Logic) |
+-------------------------+
|
V
+-------------------------+
| JSON Formatting |
| (Pydantic Models) |
+-------------------------+

**Componentes Chave:**

1.  **API Endpoint:** Recebe pedidos HTTP da app Flutter (GET request com o tópico como query parameter). Orquestra o fluxo de trabalho interno.
2.  **Content Sourcing Module:** Responsável por encontrar recursos relevantes na web com base no tópico. Utilizará uma combinação de:
    *   APIs de Motores de Busca (com limites de free tier, e.g., DuckDuckGo, ou Google Custom Search se o utilizador fornecer chave API).
    *   Web Scraping direcionado a fontes confiáveis (e.g., documentação oficial, sites de tutoriais conhecidos).
    *   APIs específicas de plataformas (e.g., YouTube Data API, com gestão de quota).
3.  **Path Generation Module:** Recebe a lista de recursos encontrados e organiza-os numa estrutura lógica de aprendizagem (nós, pré-requisitos, tipos de conteúdo). Implementará heurísticas para sequenciar o conteúdo (e.g., introdução -> básico -> avançado -> projeto).
4.  **JSON Formatting:** Garante que a estrutura de dados gerada corresponde exatamente ao formato JSON esperado pela app Flutter, incluindo metadados, nós, recursos, etc.

## 3. Stack Tecnológico Sugerido (Foco no Gratuito)

*   **Linguagem:** Python 3.x (Extensa biblioteca para web scraping, APIs, e fácil de hospedar gratuitamente).
*   **Framework Web API:** FastAPI (Moderno, rápido, com validação de dados via Pydantic, documentação automática OpenAPI - útil para a app Flutter). Alternativa: Flask (Mais simples, igualmente viável).
*   **Bibliotecas de Sourcing:**
    *   `requests` ou `httpx` (Para chamadas HTTP).
    *   `beautifulsoup4` + `lxml` (Para parsing HTML/Web Scraping).
    *   Bibliotecas de cliente para APIs de busca (e.g., `python-duckduckgo`, `google-api-python-client`).
*   **Validação/Serialização de Dados:** Pydantic (Integrado com FastAPI, excelente para garantir a estrutura JSON correta).
*   **Alojamento (Hosting):**
    *   **Render.com:** Oferece um free tier para Web Services (aplicações Python/FastAPI) com deploy via Git ou Docker. Limitações em CPU/RAM e inatividade.
    *   **Fly.io:** Oferece um free tier generoso para containers Docker. Mais flexível, mas pode requerer Dockerfile.
    *   **PythonAnywhere:** Focado em Python, free tier simples para aplicações web básicas (WSGI).
    *   **Alternativa Serverless:** AWS Lambda + API Gateway ou Google Cloud Functions + API Gateway (Podem ser gratuitos com baixo tráfego, mas a configuração pode ser mais complexa e o "cold start" pode ser um problema).
*   **Base de Dados (Opcional - Fase Futura):** Para caching ou persistência.
    *   **Neon / Supabase:** Free tiers para PostgreSQL.
    *   **MongoDB Atlas:** Free tier para NoSQL.
    *   *Inicialmente, não será utilizada base de dados para simplificar e manter o custo zero.*

## 4. Fluxo de Trabalho Principal

1.  A app Flutter envia um pedido GET para `/generate_mcp?topic=<nome_do_topico>` para o servidor MCP.
2.  O **API Endpoint** (FastAPI) recebe o pedido e extrai o `topic`.
3.  O endpoint invoca o **Content Sourcing Module**, passando o `topic`.
4.  O **Content Sourcing Module** executa várias estratégias para encontrar recursos:
    *   Formula queries para motores de busca (e.g., "`<topic>` tutorial", "`<topic>` documentation", "`<topic>` exercises", "`<topic>` video intro").
    *   Chama APIs de busca (respeitando limites).
    *   Realiza scraping direcionado em sites pré-definidos (se aplicável para o tópico).
    *   Filtra e recolhe URLs, títulos, e (se possível) metadados como tipo (vídeo, artigo), duração/tempo de leitura estimado.
5.  Os recursos encontrados são passados para o **Path Generation Module**.
6.  O **Path Generation Module** aplica heurísticas para:
    *   Agrupar recursos por subtemas ou níveis (intro, básico, avançado).
    *   Criar `nodes` (lições, quizzes placeholder, projetos placeholder) no formato JSON.
    *   Atribuir recursos aos `nodes` apropriados.
    *   Definir `prerequisites` sequencialmente entre os nós.
    *   Gerar metadados básicos para o MCP (título, descrição baseada no tópico, `rootNodeId`).
    *   Gerar metadados para os nós (títulos, descrições).
    *   Estimar dificuldade e tempo total (baseado na contagem/tipo de recursos).
7.  A estrutura de dados resultante é passada para o módulo de **JSON Formatting**.
8.  Utilizando modelos Pydantic, a estrutura é validada e serializada para o formato JSON exato especificado (semelhante ao exemplo fornecido). Campos como `visualPosition`, `rewards`, `state` podem ter valores default ou calculados de forma simples.
9.  O **API Endpoint** devolve a resposta JSON com status code 200 (OK) para a app Flutter.
10. Em caso de erro (e.g., nenhum recurso encontrado, erro interno), devolve uma resposta de erro JSON apropriada (e.g., status code 500 ou 404).

## 5. Estrutura de Dados (Output JSON)

O servidor DEVE produzir um JSON que adira estritamente à estrutura fornecida no pedido inicial. A validação via Pydantic é crucial aqui. Todos os campos definidos no exemplo devem estar presentes no output, mesmo que com valores placeholder ou default onde a geração dinâmica complexa não seja viável na V1 (e.g., `quiz.questions`, `rewards` específicos, `visualPosition` detalhado).

## 6. Estratégia de Deployment (Free Tier)

1.  Desenvolver a aplicação localmente.
2.  Criar um repositório Git (e.g., GitHub, GitLab).
3.  Escolher um provedor de alojamento com free tier (e.g., Render).
4.  Configurar o serviço no provedor:
    *   Ligar ao repositório Git.
    *   Definir o ambiente (Python).
    *   Especificar o comando de build (e.g., `pip install -r requirements.txt`).
    *   Especificar o comando de start (e.g., `uvicorn main:app --host 0.0.0.0 --port $PORT`).
    *   Configurar variáveis de ambiente (se houver API keys, NUNCA devem estar no código).
5.  Realizar o deploy e testar o endpoint público.
6.  Monitorizar o uso para garantir que permanece dentro dos limites do free tier.

## 7. Fases Futuras / Melhorias Potenciais

*   **Caching:** Implementar caching (in-memory ou com DB gratuito) para evitar refazer buscas/geração para tópicos populares, respeitando os limites das APIs externas.
*   **Fontes de Conteúdo:** Expandir para mais APIs e sites de scraping (com cuidado).
*   **Qualidade da Geração:** Melhorar as heurísticas de geração de caminhos, talvez usando NLP básico (e.g., análise de palavras-chave) se bibliotecas leves estiverem disponíveis.
*   **Geração de Quizzes:** Integrar com APIs de LLM (se o utilizador fornecer chave) ou usar um banco de perguntas simples para gerar quizzes mais realistas.
*   **Personalização:** Permitir parâmetros adicionais no pedido (e.g., nível de dificuldade desejado).
*   **Monitorização e Logging:** Implementar logging mais robusto para diagnóstico.