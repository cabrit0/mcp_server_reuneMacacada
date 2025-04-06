from typing import Dict, List, Any

# Definição das categorias
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "technology": {
        "keywords": ["programação", "software", "hardware", "desenvolvimento", "código", "app", "aplicativo", 
                    "tecnologia", "computador", "internet", "web", "digital", "programador", "developer"],
        "subtopics": [
            "Fundamentos de {topic}",
            "Ferramentas para {topic}",
            "Frameworks de {topic}",
            "Boas práticas em {topic}",
            "Arquitetura de {topic}",
            "Testes em {topic}",
            "Segurança em {topic}",
            "Otimização de {topic}",
            "Tendências em {topic}",
            "Implementação de {topic}",
            "Configuração de {topic}",
            "Depuração de {topic}"
        ],
        "resource_queries": [
            "{topic} tutorial",
            "{topic} documentation",
            "{topic} best practices",
            "{topic} examples",
            "{topic} guide"
        ]
    },
    "finance": {
        "keywords": ["finanças", "dinheiro", "investimento", "economia", "mercado", "bolsa", "ações", 
                    "poupança", "orçamento", "financeiro", "banco", "crédito", "financeira", "monetário"],
        "subtopics": [
            "Princípios básicos de {topic}",
            "Planejamento de {topic}",
            "Estratégias de {topic}",
            "Gestão de riscos em {topic}",
            "Análise de {topic}",
            "Tendências em {topic}",
            "Regulamentação de {topic}",
            "Ferramentas para {topic}",
            "Estudos de caso em {topic}",
            "Orçamento para {topic}",
            "Investimentos em {topic}",
            "Tributação em {topic}"
        ],
        "resource_queries": [
            "{topic} guia",
            "{topic} tutorial",
            "{topic} explicado",
            "{topic} para iniciantes",
            "{topic} avançado"
        ]
    },
    "health": {
        "keywords": ["saúde", "bem-estar", "medicina", "fitness", "nutrição", "exercício", "dieta", 
                    "médico", "terapia", "mental", "corpo", "mente", "doença", "prevenção"],
        "subtopics": [
            "Fundamentos de {topic}",
            "Benefícios de {topic}",
            "Práticas recomendadas para {topic}",
            "Riscos associados a {topic}",
            "Pesquisas sobre {topic}",
            "Aplicações de {topic}",
            "Técnicas de {topic}",
            "Equipamentos para {topic}",
            "Profissionais de {topic}",
            "Prevenção através de {topic}",
            "Tratamentos com {topic}",
            "Histórico de {topic}"
        ],
        "resource_queries": [
            "{topic} guia completo",
            "{topic} benefícios",
            "{topic} como funciona",
            "{topic} dicas",
            "{topic} profissional"
        ]
    },
    "education": {
        "keywords": ["educação", "aprendizagem", "ensino", "escola", "faculdade", "universidade", 
                    "curso", "aula", "professor", "aluno", "estudante", "pedagogia", "didática"],
        "subtopics": [
            "Metodologias de {topic}",
            "Recursos para {topic}",
            "Avaliação em {topic}",
            "Tecnologias para {topic}",
            "Desafios em {topic}",
            "Tendências em {topic}",
            "Práticas de {topic}",
            "Teorias de {topic}",
            "Aplicações de {topic}",
            "Desenvolvimento de {topic}",
            "Estratégias de {topic}",
            "Inovação em {topic}"
        ],
        "resource_queries": [
            "{topic} metodologia",
            "{topic} recursos",
            "{topic} aplicações",
            "{topic} guia para professores",
            "{topic} para estudantes"
        ]
    },
    "arts": {
        "keywords": ["arte", "música", "pintura", "literatura", "cinema", "teatro", "dança", 
                    "escultura", "fotografia", "design", "criativo", "cultural", "artístico"],
        "subtopics": [
            "História de {topic}",
            "Técnicas de {topic}",
            "Estilos de {topic}",
            "Materiais para {topic}",
            "Artistas de {topic}",
            "Movimentos em {topic}",
            "Análise de {topic}",
            "Criação de {topic}",
            "Apreciação de {topic}",
            "Exposições de {topic}",
            "Tendências em {topic}",
            "Ensino de {topic}"
        ],
        "resource_queries": [
            "{topic} técnicas",
            "{topic} história",
            "{topic} como fazer",
            "{topic} exemplos",
            "{topic} para iniciantes"
        ]
    },
    "science": {
        "keywords": ["ciência", "física", "química", "biologia", "matemática", "astronomia", 
                    "geologia", "pesquisa", "laboratório", "experimento", "científico", "teoria"],
        "subtopics": [
            "Princípios de {topic}",
            "Experimentos em {topic}",
            "Teorias de {topic}",
            "Aplicações de {topic}",
            "História de {topic}",
            "Avanços em {topic}",
            "Metodologia de {topic}",
            "Equipamentos para {topic}",
            "Pesquisadores de {topic}",
            "Descobertas em {topic}",
            "Futuro de {topic}",
            "Impacto de {topic}"
        ],
        "resource_queries": [
            "{topic} explicado",
            "{topic} pesquisa",
            "{topic} teoria",
            "{topic} aplicações",
            "{topic} experimentos"
        ]
    },
    "business": {
        "keywords": ["negócios", "empreendedorismo", "empresa", "startup", "gestão", "marketing", 
                    "vendas", "administração", "liderança", "estratégia", "comercial", "mercado"],
        "subtopics": [
            "Fundamentos de {topic}",
            "Estratégias de {topic}",
            "Gestão de {topic}",
            "Análise de {topic}",
            "Tendências em {topic}",
            "Ferramentas para {topic}",
            "Casos de sucesso em {topic}",
            "Desafios em {topic}",
            "Inovação em {topic}",
            "Planejamento de {topic}",
            "Métricas para {topic}",
            "Liderança em {topic}"
        ],
        "resource_queries": [
            "{topic} estratégias",
            "{topic} guia",
            "{topic} cases",
            "{topic} ferramentas",
            "{topic} tendências"
        ]
    },
    "lifestyle": {
        "keywords": ["estilo de vida", "hobby", "lazer", "viagem", "culinária", "gastronomia", 
                    "decoração", "moda", "jardinagem", "pets", "animais", "casa", "família"],
        "subtopics": [
            "Introdução a {topic}",
            "Técnicas de {topic}",
            "Equipamentos para {topic}",
            "Tendências em {topic}",
            "Dicas para {topic}",
            "Benefícios de {topic}",
            "Comunidades de {topic}",
            "Eventos de {topic}",
            "História de {topic}",
            "Projetos de {topic}",
            "Inspirações para {topic}",
            "Personalização de {topic}"
        ],
        "resource_queries": [
            "{topic} dicas",
            "{topic} como começar",
            "{topic} ideias",
            "{topic} tutoriais",
            "{topic} inspiração"
        ]
    },
    "general": {
        "keywords": [],  # Categoria padrão, sem palavras-chave específicas
        "subtopics": [
            "Introdução a {topic}",
            "Fundamentos de {topic}",
            "Aplicações de {topic}",
            "História de {topic}",
            "Técnicas de {topic}",
            "Ferramentas para {topic}",
            "Tendências em {topic}",
            "Práticas recomendadas para {topic}",
            "Recursos para {topic}",
            "Comunidade de {topic}",
            "Futuro de {topic}",
            "Impacto de {topic}"
        ],
        "resource_queries": [
            "{topic} guia",
            "{topic} tutorial",
            "{topic} explicado",
            "{topic} exemplos",
            "{topic} recursos"
        ]
    }
}

def detect_category(topic: str) -> str:
    """
    Detecta a categoria mais provável para um tópico.
    
    Args:
        topic: O tópico a ser categorizado
        
    Returns:
        Nome da categoria detectada
    """
    topic_lower = topic.lower()
    
    # Pontuação para cada categoria
    scores = {}
    
    for category, data in CATEGORIES.items():
        if category == "general":
            continue  # Pular a categoria geral na pontuação
            
        score = 0
        for keyword in data["keywords"]:
            if keyword in topic_lower:
                score += 1
        scores[category] = score
    
    # Se nenhuma categoria tiver pontuação, use "general"
    if not scores or all(score == 0 for score in scores.values()):
        return "general"
    
    # Retorna a categoria com maior pontuação
    return max(scores.items(), key=lambda x: x[1])[0]

def get_subtopics_for_category(topic: str, num_subtopics: int = 10) -> List[str]:
    """
    Obtém subtópicos para um tópico com base em sua categoria.
    
    Args:
        topic: O tópico principal
        num_subtopics: Número de subtópicos desejados
        
    Returns:
        Lista de subtópicos formatados
    """
    import random
    
    # Detectar categoria
    category = detect_category(topic)
    
    # Obter templates de subtópicos para a categoria
    subtopic_templates = CATEGORIES.get(category, CATEGORIES["general"])["subtopics"]
    
    # Se não houver templates suficientes, repetir alguns
    while len(subtopic_templates) < num_subtopics:
        subtopic_templates.extend(subtopic_templates)
    
    # Selecionar aleatoriamente e formatar os templates
    selected_templates = random.sample(subtopic_templates, num_subtopics)
    subtopics = [template.format(topic=topic) for template in selected_templates]
    
    return subtopics

def get_resource_queries_for_category(topic: str, category: str = None) -> List[str]:
    """
    Obtém consultas de recursos para um tópico com base em sua categoria.
    
    Args:
        topic: O tópico principal
        category: Categoria (opcional, será detectada se não fornecida)
        
    Returns:
        Lista de consultas de recursos formatadas
    """
    # Detectar categoria se não fornecida
    if category is None:
        category = detect_category(topic)
    
    # Obter templates de consultas para a categoria
    query_templates = CATEGORIES.get(category, CATEGORIES["general"])["resource_queries"]
    
    # Formatar as consultas
    queries = [template.format(topic=topic) for template in query_templates]
    
    return queries
