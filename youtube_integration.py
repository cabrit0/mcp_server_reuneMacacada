import yt_dlp
import asyncio
import uuid
import re
import random
from typing import List, Dict, Any, Optional

from schemas import Resource

async def search_youtube_videos(topic: str, max_results: int = 5, language: str = "pt", is_subtopic: bool = False) -> List[Resource]:
    """
    Busca vídeos no YouTube relacionados ao tópico usando yt-dlp.

    Args:
        topic: O tópico de busca
        max_results: Número máximo de resultados
        language: Código do idioma preferido
        is_subtopic: Indica se o tópico é um subtópico (para ajustar a busca)

    Returns:
        Lista de objetos Resource contendo vídeos do YouTube
    """
    # Configurar opções do yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': 'in_playlist',  # Extrair informações básicas
        'skip_download': True,
        'format': 'best',
    }

    # Construir consulta de busca
    # Adicionar preferência de idioma na consulta
    lang_prefix = ""
    if language == "pt":
        lang_prefix = "português "
    elif language == "en":
        lang_prefix = "english "
    elif language == "es":
        lang_prefix = "español "

    # Ajustar a consulta com base no tipo de tópico (principal ou subtópico)
    if is_subtopic:
        # Para subtópicos, usamos uma consulta mais específica
        search_terms = [
            f"{topic} tutorial",
            f"{topic} guide",
            f"{topic} explained",
            f"{topic} how to",
            f"{topic} examples"
        ]
        # Escolher aleatoriamente um dos termos para evitar resultados repetitivos
        search_term = random.choice(search_terms)
        search_query = f"ytsearch{max_results*2}:{lang_prefix}{search_term}"
    else:
        # Para o tópico principal, usamos uma consulta mais geral
        search_query = f"ytsearch{max_results*2}:{lang_prefix}{topic}"

    try:
        # Executar busca de forma assíncrona
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: extract_info_with_ytdlp(search_query, ydl_opts))

        # Converter resultados para objetos Resource
        resources = []
        for entry in results:
            # Verificar se é um vídeo válido
            if entry.get('_type') == 'url' and 'youtube' in entry.get('url', ''):
                # Extrair duração em minutos
                duration_seconds = entry.get('duration')
                duration_minutes = int(duration_seconds / 60) if duration_seconds else None

                # Obter thumbnail
                thumbnail = get_best_thumbnail(entry)

                # Criar recurso
                resource = Resource(
                    id=f"youtube_{entry.get('id', uuid.uuid4().hex[:8])}",
                    title=entry.get('title', ''),
                    url=entry.get('url', ''),
                    type="video",
                    description=entry.get('description', '') or f"Canal: {entry.get('uploader', '')}",
                    duration=duration_minutes,
                    readTime=None,
                    difficulty="intermediate",
                    thumbnail=thumbnail
                )

                # Adicionar informação sobre o subtópico, se aplicável
                if is_subtopic:
                    # Adicionar um prefixo ao título para indicar que é específico para o subtópico
                    resource.title = f"{resource.title} - Relevante para: {topic}"

                resources.append(resource)

                if len(resources) >= max_results:
                    break

        return resources

    except Exception as e:
        print(f"Erro na busca do YouTube com yt-dlp: {e}")
        return []

def extract_info_with_ytdlp(search_query: str, ydl_opts: dict) -> List[dict]:
    """
    Extrai informações de vídeos usando yt-dlp.

    Args:
        search_query: Consulta de busca
        ydl_opts: Opções do yt-dlp

    Returns:
        Lista de informações de vídeos
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(search_query, download=False)
        if result and 'entries' in result:
            return result['entries']
        return []

def get_best_thumbnail(video_info: Dict[str, Any]) -> Optional[str]:
    """
    Obtém a melhor thumbnail disponível para um vídeo.

    Args:
        video_info: Informações do vídeo do YouTube

    Returns:
        URL da melhor thumbnail ou None se não encontrada
    """
    # Verificar se há thumbnails disponíveis
    thumbnails = video_info.get('thumbnails', [])

    if not thumbnails:
        # Fallback para thumbnail padrão do YouTube
        video_id = video_info.get('id')
        if video_id:
            return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        return None

    # Ordenar thumbnails por resolução (largura x altura)
    sorted_thumbnails = sorted(
        thumbnails,
        key=lambda t: (t.get('width', 0) * t.get('height', 0)),
        reverse=True
    )

    # Retornar a URL da melhor thumbnail
    return sorted_thumbnails[0].get('url') if sorted_thumbnails else None

def parse_duration(duration_str: str) -> Optional[int]:
    """
    Converte uma string de duração para minutos.

    Args:
        duration_str: String de duração (ex: "PT1H30M15S" ou "1:30:15")

    Returns:
        Duração em minutos ou None se não for possível converter
    """
    if not duration_str:
        return None

    # Formato ISO 8601 (PT1H30M15S)
    iso_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if iso_match:
        hours = int(iso_match.group(1) or 0)
        minutes = int(iso_match.group(2) or 0)
        seconds = int(iso_match.group(3) or 0)
        return hours * 60 + minutes + (1 if seconds > 30 else 0)

    # Formato HH:MM:SS ou MM:SS
    time_match = re.match(r'(?:(\d+):)?(\d+):(\d+)', duration_str)
    if time_match:
        hours = int(time_match.group(1) or 0)
        minutes = int(time_match.group(2) or 0)
        seconds = int(time_match.group(3) or 0)
        return hours * 60 + minutes + (1 if seconds > 30 else 0)

    return None


async def search_videos_for_subtopic(subtopic: str, max_results: int = 2, language: str = "pt") -> List[Resource]:
    """
    Busca vídeos do YouTube especificamente para um subtópico.

    Args:
        subtopic: O subtópico para buscar vídeos
        max_results: Número máximo de vídeos a retornar
        language: Código do idioma

    Returns:
        Lista de recursos de vídeo do YouTube
    """
    # Limpar o subtópico para melhorar a busca
    # Remover prefixos comuns que podem atrapalhar a busca
    clean_subtopic = subtopic
    prefixes_to_remove = [
        "Introduction to", "Getting Started with", "Understanding", "Basics of",
        "Advanced", "Mastering", "Practical", "Exploring", "Deep Dive into",
        "Essential", "Fundamentals of", "Working with", "Building with",
        "Developing with", "Professional", "Modern", "Effective", "Efficient",
        "Introdução a", "Introdução ao", "Conceitos de", "Fundamentos de",
        "Avançado", "Prático", "Explorando", "Essencial", "Trabalhando com",
        "Desenvolvendo com", "Profissional", "Moderno", "Eficiente"
    ]

    for prefix in prefixes_to_remove:
        if clean_subtopic.startswith(prefix):
            clean_subtopic = clean_subtopic[len(prefix):].strip()
            break

    # Buscar vídeos específicos para o subtópico
    return await search_youtube_videos(clean_subtopic, max_results=max_results, language=language, is_subtopic=True)
