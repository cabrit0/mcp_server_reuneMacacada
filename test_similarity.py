"""
Script para testar a detecção de similaridade usando TF-IDF e similaridade do cosseno.
"""

import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Dict, Any, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_similarity")

# Baixar stopwords do NLTK
def download_nltk_resources():
    try:
        nltk.download('stopwords', quiet=True)
        # Verificar se temos stopwords em português
        try:
            nltk.corpus.stopwords.words('portuguese')
            logger.info("Portuguese stopwords available")
        except:
            # Se não tiver, baixar novamente
            nltk.download('stopwords', quiet=True)
            logger.info("Downloaded stopwords again")
        logger.info("NLTK resources downloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to download NLTK resources: {e}")

# Exemplo de recursos
def create_test_resources():
    resources = [
        {
            "title": "Introdução ao Python para iniciantes",
            "description": "Um guia completo para começar a programar em Python, cobrindo os conceitos básicos e sintaxe."
        },
        {
            "title": "Python para iniciantes: primeiros passos",
            "description": "Um guia completo para começar a programar em Python, cobrindo conceitos básicos."
        },
        {
            "title": "Estruturas de dados em Python",
            "description": "Aprenda sobre listas, dicionários, tuplas e conjuntos em Python."
        },
        {
            "title": "Funções em Python",
            "description": "Como definir e usar funções em Python para organizar seu código."
        },
        {
            "title": "Programação orientada a objetos em Python",
            "description": "Aprenda os conceitos de classes, objetos, herança e polimorfismo em Python."
        },
        {
            "title": "Python OOP: Classes e Objetos",
            "description": "Aprenda os conceitos de classes, objetos, herança e polimorfismo em programação orientada a objetos com Python."
        }
    ]
    return resources

def detect_similar_resources(resources: List[Dict[str, Any]], language: str = "pt", similarity_threshold: float = 0.75) -> List[Dict[str, Any]]:
    """
    Detecta e remove recursos similares usando TF-IDF e similaridade do cosseno.

    Args:
        resources: Lista de recursos a serem analisados
        language: Código do idioma (en, pt, es, fr, de, it)
        similarity_threshold: Limiar de similaridade (0.0 a 1.0)

    Returns:
        Lista de recursos sem duplicações de conteúdo
    """
    if not resources or len(resources) < 2:
        return resources

    # Baixar recursos do NLTK
    download_nltk_resources()

    # Obter stopwords para o idioma
    try:
        stopwords = nltk.corpus.stopwords.words(language)
    except Exception as e:
        logger.warning(f"Error getting stopwords for language {language}: {e}")
        # Fallback para inglês
        stopwords = nltk.corpus.stopwords.words('english')

    # Preparar textos para análise
    texts = []
    for resource in resources:
        # Combinar título e descrição para análise
        title = resource.get('title', '')
        description = resource.get('description', '')
        combined_text = f"{title} {description}"
        texts.append(combined_text)

    # Criar vetorizador TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words=stopwords,
        min_df=1,
        max_df=0.9,
        ngram_range=(1, 2)  # Considerar unigramas e bigramas
    )

    # Calcular matriz TF-IDF
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except Exception as e:
        logger.error(f"Error calculating TF-IDF matrix: {e}")
        return resources

    # Calcular similaridade do cosseno entre todos os pares
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Mostrar matriz de similaridade
    logger.info("Similarity Matrix:")
    for i in range(len(resources)):
        logger.info(f"Resource {i+1}: {resources[i]['title']}")

    logger.info("\nSimilarity scores:")
    for i in range(len(resources)):
        for j in range(i+1, len(resources)):
            logger.info(f"Similarity between resource {i+1} and {j+1}: {cosine_sim[i, j]:.4f}")

    # Identificar recursos similares
    similar_pairs = []
    for i in range(len(resources)):
        for j in range(i+1, len(resources)):
            if cosine_sim[i, j] > similarity_threshold:
                # Registrar par similar
                similar_pairs.append((i, j, cosine_sim[i, j]))

    # Ordenar pares por similaridade (decrescente)
    similar_pairs.sort(key=lambda x: x[2], reverse=True)

    # Mostrar pares similares
    logger.info("\nSimilar pairs:")
    for i, j, sim in similar_pairs:
        logger.info(f"Resource {i+1} and {j+1} are similar (score: {sim:.4f}):")
        logger.info(f"  - {resources[i]['title']}")
        logger.info(f"  - {resources[j]['title']}")

    # Identificar recursos a serem removidos (manter o mais completo de cada par)
    to_remove = set()
    for i, j, sim in similar_pairs:
        # Se um dos recursos já está marcado para remoção, ignorar
        if i in to_remove or j in to_remove:
            continue

        # Decidir qual recurso manter com base na completude
        resource_i = resources[i]
        resource_j = resources[j]

        # Calcular "completude" de cada recurso
        completeness_i = len(resource_i.get('title', '')) + len(resource_i.get('description', ''))
        completeness_j = len(resource_j.get('title', '')) + len(resource_j.get('description', ''))

        # Remover o menos completo
        if completeness_i >= completeness_j:
            to_remove.add(j)
            logger.info(f"Removing resource {j+1}: {resource_j.get('title')} (keeping resource {i+1})")
        else:
            to_remove.add(i)
            logger.info(f"Removing resource {i+1}: {resource_i.get('title')} (keeping resource {j+1})")

    # Criar lista de recursos filtrados
    filtered_resources = [r for i, r in enumerate(resources) if i not in to_remove]

    logger.info(f"\nRemoved {len(to_remove)} similar resources out of {len(resources)}")
    logger.info(f"Remaining resources: {len(filtered_resources)}")

    return filtered_resources

def main():
    # Criar recursos de teste
    resources = create_test_resources()

    # Testar com diferentes limiares de similaridade
    thresholds = [0.65, 0.75, 0.85]

    for threshold in thresholds:
        logger.info(f"\n\n=== Testing with similarity threshold: {threshold} ===\n")
        filtered_resources = detect_similar_resources(resources, "pt", threshold)

        logger.info("\nRemaining resources:")
        for i, resource in enumerate(filtered_resources):
            logger.info(f"{i+1}. {resource['title']}")

if __name__ == "__main__":
    main()
