"""
Módulo para detecção de conteúdo similar usando TF-IDF e similaridade do cosseno.

Este módulo implementa funções para detectar e remover recursos similares em uma lista
de recursos, usando TF-IDF (Term Frequency-Inverse Document Frequency) e similaridade
do cosseno. Suporta múltiplos idiomas e permite ajustar o limiar de similaridade.
"""

import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Dict, Any, Tuple

# Configurar logging
logger = logging.getLogger("mcp_server.similarity_detector")

# Dicionário de stopwords para diferentes idiomas
STOPWORDS = {}

# Baixar stopwords do NLTK (executar uma vez)
def download_nltk_resources():
    """
    Baixa os recursos necessários do NLTK (stopwords para vários idiomas).
    """
    try:
        nltk.download('stopwords', quiet=True)
        
        # Inicializar dicionário de stopwords
        global STOPWORDS
        STOPWORDS = {
            "en": nltk.corpus.stopwords.words('english'),
            "pt": nltk.corpus.stopwords.words('portuguese'),
            "es": nltk.corpus.stopwords.words('spanish'),
            "fr": nltk.corpus.stopwords.words('french'),
            "de": nltk.corpus.stopwords.words('german'),
            "it": nltk.corpus.stopwords.words('italian')
        }
        logger.info("NLTK resources downloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to download NLTK resources: {e}")

def detect_similar_resources(resources: List[Dict[str, Any]], language: str = "en", similarity_threshold: float = 0.75) -> List[Dict[str, Any]]:
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
    
    # Verificar se o dicionário de stopwords está inicializado
    if not STOPWORDS:
        download_nltk_resources()
    
    # Verificar se o idioma é suportado, caso contrário usar inglês
    if language not in STOPWORDS:
        language = "en"
        logger.warning(f"Language {language} not supported for stopwords, using English")
    
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
        stop_words=STOPWORDS.get(language, STOPWORDS.get("en")),
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
    
    # Identificar recursos similares
    similar_pairs = []
    for i in range(len(resources)):
        for j in range(i+1, len(resources)):
            if cosine_sim[i, j] > similarity_threshold:
                # Registrar par similar
                similar_pairs.append((i, j, cosine_sim[i, j]))
    
    # Ordenar pares por similaridade (decrescente)
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
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
            logger.info(f"Removing similar resource: {resource_j.get('title')} (similar to {resource_i.get('title')}, similarity: {sim:.2f})")
        else:
            to_remove.add(i)
            logger.info(f"Removing similar resource: {resource_i.get('title')} (similar to {resource_j.get('title')}, similarity: {sim:.2f})")
    
    # Criar lista de recursos filtrados
    filtered_resources = [r for i, r in enumerate(resources) if i not in to_remove]
    
    logger.info(f"Removed {len(to_remove)} similar resources out of {len(resources)}")
    return filtered_resources

def get_similarity_matrix(resources: List[Dict[str, Any]], language: str = "en") -> Tuple[np.ndarray, List[str]]:
    """
    Calcula a matriz de similaridade entre recursos.
    
    Args:
        resources: Lista de recursos a serem analisados
        language: Código do idioma (en, pt, es, fr, de, it)
        
    Returns:
        Tupla contendo a matriz de similaridade e a lista de títulos dos recursos
    """
    if not resources or len(resources) < 2:
        return np.array([]), []
    
    # Verificar se o dicionário de stopwords está inicializado
    if not STOPWORDS:
        download_nltk_resources()
    
    # Verificar se o idioma é suportado, caso contrário usar inglês
    if language not in STOPWORDS:
        language = "en"
    
    # Preparar textos para análise
    texts = []
    titles = []
    for resource in resources:
        # Combinar título e descrição para análise
        title = resource.get('title', '')
        description = resource.get('description', '')
        combined_text = f"{title} {description}"
        texts.append(combined_text)
        titles.append(title)
    
    # Criar vetorizador TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words=STOPWORDS.get(language, STOPWORDS.get("en")),
        min_df=1,
        max_df=0.9,
        ngram_range=(1, 2)  # Considerar unigramas e bigramas
    )
    
    # Calcular matriz TF-IDF
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        # Calcular similaridade do cosseno entre todos os pares
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        return cosine_sim, titles
    except Exception as e:
        logger.error(f"Error calculating similarity matrix: {e}")
        return np.array([]), titles

# Inicializar recursos do NLTK
download_nltk_resources()
