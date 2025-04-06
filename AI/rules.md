# Regras e Diretrizes para Implementação do Servidor MCP

Este documento define as regras, restrições e boas práticas que a IA deve seguir durante a implementação do servidor MCP.

## 0. Instruções Fundamentais para a IA

- **Referência Constante:** Deves ter sempre presentes e consultar continuamente o conteúdo destes três ficheiros: `planning.md`, `tasks.md` e `rules.md` durante todo o processo de desenvolvimento. Eles são a tua fonte de verdade.
- **Execução Sequencial e Focada:** Deves realizar as tarefas **uma de cada vez**, seguindo a ordem e os passos detalhados no ficheiro `tasks.md`. Conclui uma tarefa antes de iniciar a seguinte.
- **Monitorização do Progresso:** À medida que completas cada tarefa ou subtarefa definida no ficheiro `tasks.md`, deves **obrigatoriamente marcar a respetiva caixa de verificação** (alterando `[ ]` para `[x]`) nesse ficheiro.
- **Imutabilidade dos Planos:** **Não deves alterar, adicionar ou remover qualquer conteúdo** dos ficheiros `planning.md`, `tasks.md` ou `rules.md`, com a **única e exclusiva exceção** de marcar as caixas de verificação das tarefas como concluídas (`[x]`) no ficheiro `tasks.md`. O objetivo é manter um registo fiel do plano original e do progresso.
- **Linguagem:** Toda a implementação, comentários no código, mensagens de log e qualquer comunicação resultante devem ser estritamente em **Português de Portugal**.

## 1. Mandato Principal

- **Objetivo:** Criar um servidor API funcional que gera planos de aprendizagem (MCPs) em formato JSON com base num tópico, agregando recursos gratuitos da web.
- **Restrição Chave:** A solução final (código e infraestrutura de alojamento) DEVE operar dentro dos limites de serviços gratuitos. Qualquer custo recorrente é inaceitável.
- **Formato de Saída:** Aderir **estritamente** à estrutura JSON definida e exemplificada no pedido inicial. A validação do schema de saída é obrigatória (usar Pydantic).

## 2. Restrições Tecnológicas

- **Stack Preferencial:** Utilizar Python, FastAPI, e as bibliotecas sugeridas em `planning.md`, a menos que uma limitação intransponível seja encontrada.
- **Alojamento:** Utilizar exclusivamente plataformas com _free tiers_ viáveis para este tipo de aplicação (Render, Fly.io, PythonAnywhere, ou alternativas _serverless_ gratuitas). Evitar soluções que exijam cartão de crédito para o _free tier_, se possível.
- **APIs Externas:** Utilizar apenas APIs que ofereçam um _free tier_ suficiente para operação de baixo volume ou APIs que não exijam chave (como DuckDuckGo Search). Se APIs com chave forem usadas (e.g., Google Search, YouTube), a implementação deve assumir que a chave será fornecida via variável de ambiente e NUNCA _hardcoded_. O sistema deve funcionar de forma degradada (talvez com menos fontes) se uma chave não for fornecida.

## 3. Regras de Agregação de Conteúdo (_Content Sourcing_)

- **Prioridade:** Dar preferência a fontes oficiais e reputadas (e.g., documentação oficial do Flutter/Dart, MDN, sites de tutoriais conhecidos como freeCodeCamp, etc.).
- **Web Scraping:**
  - **Ética:** Sempre que fizer _scraping_, identificar o _bot_ com um `User-Agent` claro (e.g., `MCPBot/1.0 (+http://your-service-url/bot-info)`).
  - **robots.txt:** Respeitar as diretivas do `robots.txt` do site alvo. Se o _scraping_ for proibido para o agente ou para os caminhos necessários, não o fazer.
  - **_Rate Limiting_:** Implementar atrasos (`time.sleep`) entre pedidos ao mesmo domínio para evitar sobrecarga. Ser conservador.
  - **Robustez:** O _scraping_ é frágil. Implementar tratamento de erros robusto para lidar com alterações na estrutura do site, _timeouts_, ou bloqueios. Ter fontes alternativas (APIs de busca) como _fallback_.
- **Limites de API:** Implementar lógica para lidar com os limites de taxa e quotas das APIs gratuitas. Se um limite for atingido, o sistema deve falhar graciosamente ou continuar com menos dados, registando o evento.
- **Qualidade do Conteúdo:** A IA não é responsável pela _qualidade_ intrínseca do conteúdo encontrado, mas deve tentar priorizar fontes conhecidas pela sua qualidade. A relevância é determinada por heurísticas (palavras-chave, títulos).

## 4. Regras de Geração do Caminho de Aprendizagem (_Path Generation_)

- **Estrutura Lógica:** O caminho gerado deve ter uma sequência lógica mínima (e.g., introdução antes de tópicos avançados). Uma estrutura linear simples é aceitável para a V1.
- **Completude do JSON:** Todos os campos definidos no schema `schemas.MCP` (derivado do exemplo JSON) DEVEM ser preenchidos no output. Usar valores _default_, listas vazias, ou _placeholders_ onde a geração dinâmica for complexa ou fora do escopo da V1 (e.g., `quiz.questions`, `rewards`, `hints`, `visualPosition` detalhado, `estimatedHours` preciso).
- **IDs:** Gerar IDs únicos e consistentes para o MCP e para cada nó.
- **Pré-requisitos:** Garantir que os `prerequisites` em cada nó referenciam IDs de nós válidos que vêm antes na sequência lógica. O `rootNodeId` deve apontar para o primeiro nó.
- **Tipos de Recursos:** Mapear corretamente os recursos encontrados para os tipos esperados no JSON (`video`, `article`, `documentation`, `exercise`, `tutorial`, `code_example`, `tool`, `interactive`, `project`). Fazer a melhor estimativa possível com base na URL, título ou fonte.

## 5. Qualidade e Manutenção do Código

- **Clareza:** Escrever código limpo, bem comentado e modular. Usar nomes de variáveis e funções descritivos.
- **_Type Hints_:** Utilizar _type hints_ do Python em todas as definições de função e variáveis importantes.
- **Tratamento de Erros:** Implementar tratamento de erros abrangente em todas as operações de I/O (rede, ficheiros se houver) e em pontos críticos da lógica. Usar exceções apropriadas.
- **_Logging_:** Implementar _logging_ significativo para _debugging_ e monitorização (pedidos, erros, eventos importantes como limites de API atingidos).
- **Segurança:**
  - **NÃO** incluir segredos (API keys, passwords) diretamente no código. Usar variáveis de ambiente.
  - Validar e sanitizar _inputs_ (o `topic` do _query parameter_). FastAPI ajuda com a validação básica.
- **Dependências:** Manter o `requirements.txt` atualizado. Usar um ambiente virtual.

## 6. Deployment e Operação

- **Automatização:** O processo de _deployment_ deve ser o mais automatizado possível através da plataforma de alojamento (e.g., _deploy_ a partir de Git _push_).
- **Variáveis de Ambiente:** Configurar todas as variáveis de ambiente necessárias (API Keys, configurações de ambiente) na plataforma de alojamento.
- **Monitorização do _Free Tier_:** A implementação deve ser consciente dos limites do _free tier_ (tempo de CPU, memória, requisições, horas de atividade, inatividade/_sleep_). O _design_ deve ser leve para maximizar a permanência no _free tier_.
- **Documentação API:** Garantir que a documentação OpenAPI gerada pelo FastAPI (`/docs`) está funcional e reflete a API real.

Ao seguir estes planos (`planning.md`, `tasks.md`) e regras (`rules.md`), e especialmente as instruções na secção 0, a IA deve ser capaz de construir um servidor MCP funcional, gratuito, que cumpra os requisitos especificados, e cujo processo de desenvolvimento seja rastreável.
