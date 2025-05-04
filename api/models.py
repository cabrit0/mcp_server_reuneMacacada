"""
Modelos de dados para a API do MCP Server.

Este módulo contém os modelos Pydantic que definem a estrutura de dados da API,
incluindo os modelos para MCPs, nós, recursos, metadados, quizzes, exercícios, etc.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class Question(BaseModel):
    """
    Modelo para uma pergunta de quiz.

    Attributes:
        id: Identificador único da pergunta
        text: Texto da pergunta
        options: Lista de opções de resposta
        correctOptionIndex: Índice da opção correta (0-based)
    """
    id: str
    text: str
    options: List[str]
    correctOptionIndex: int

    @validator('correctOptionIndex')
    def validate_correct_option_index(cls, v, values):
        """Valida se o índice da opção correta está dentro dos limites."""
        if 'options' in values and v >= len(values['options']):
            raise ValueError(f'correctOptionIndex deve ser menor que o número de opções ({len(values["options"])})')
        if v < 0:
            raise ValueError('correctOptionIndex não pode ser negativo')
        return v


class Quiz(BaseModel):
    """
    Modelo para um quiz.

    Attributes:
        questions: Lista de perguntas do quiz
        passingScore: Pontuação mínima para passar no quiz (0-100)
    """
    questions: List[Question] = []
    passingScore: int = 70

    @validator('passingScore')
    def validate_passing_score(cls, v):
        """Valida se a pontuação mínima está entre 0 e 100."""
        if v < 0 or v > 100:
            raise ValueError('passingScore deve estar entre 0 e 100')
        return v


class Exercise(BaseModel):
    """
    Modelo para um exercício prático.

    Attributes:
        id: Identificador único do exercício
        title: Título do exercício
        description: Descrição do exercício
        difficulty: Nível de dificuldade do exercício
        instructions: Instruções passo a passo para o exercício
        hints: Lista de dicas para o exercício (para revelação progressiva)
        solution: Solução do exercício
        verificationMethod: Método de verificação da resposta (multiple_choice, text_match, etc.)
        options: Lista de opções para exercícios de múltipla escolha
        correctAnswer: Resposta correta para o exercício
    """
    id: str
    title: str
    description: str
    difficulty: str = "intermediate"
    instructions: str
    hints: List[str] = []
    solution: str
    verificationMethod: str  # "multiple_choice", "text_match", etc.
    options: Optional[List[str]] = None
    correctAnswer: str

    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Valida se o nível de dificuldade é válido."""
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if v.lower() not in valid_difficulties:
            raise ValueError(f'difficulty deve ser um dos seguintes: {", ".join(valid_difficulties)}')
        return v.lower()

    @validator('verificationMethod')
    def validate_verification_method(cls, v):
        """Valida se o método de verificação é válido."""
        valid_methods = ["multiple_choice", "text_match", "code_execution", "manual"]
        if v.lower() not in valid_methods:
            raise ValueError(f'verificationMethod deve ser um dos seguintes: {", ".join(valid_methods)}')
        return v.lower()

    @validator('options')
    def validate_options(cls, v, values):
        """Valida se as opções estão presentes para exercícios de múltipla escolha."""
        if 'verificationMethod' in values and values['verificationMethod'] == "multiple_choice":
            if v is None or len(v) < 2:
                raise ValueError('options deve conter pelo menos 2 opções para exercícios de múltipla escolha')
        return v


class ExerciseSet(BaseModel):
    """
    Modelo para um conjunto de exercícios práticos.

    Attributes:
        exercises: Lista de exercícios no conjunto
        passingScore: Pontuação mínima para passar no conjunto de exercícios (0-100)
    """
    exercises: List[Exercise] = []
    passingScore: int = 70

    @validator('passingScore')
    def validate_passing_score(cls, v):
        """Valida se a pontuação mínima está entre 0 e 100."""
        if v < 0 or v > 100:
            raise ValueError('passingScore deve estar entre 0 e 100')
        return v


class Metadata(BaseModel):
    """
    Metadados para um MCP.

    Attributes:
        difficulty: Nível de dificuldade do MCP (beginner, intermediate, advanced)
        estimatedHours: Tempo estimado para completar o MCP em horas
        tags: Lista de tags relacionadas ao MCP
    """
    difficulty: str = "intermediate"
    estimatedHours: int = 5
    tags: List[str] = []

    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Valida se o nível de dificuldade é válido."""
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if v.lower() not in valid_difficulties:
            raise ValueError(f'difficulty deve ser um dos seguintes: {", ".join(valid_difficulties)}')
        return v.lower()

    @validator('estimatedHours')
    def validate_estimated_hours(cls, v):
        """Valida se o tempo estimado é positivo."""
        if v < 0:
            raise ValueError('estimatedHours não pode ser negativo')
        return v


class Resource(BaseModel):
    """
    Modelo para um recurso de aprendizagem.

    Attributes:
        id: Identificador único do recurso
        title: Título do recurso
        url: URL do recurso
        type: Tipo do recurso (article, video, documentation, exercise, etc.)
        description: Descrição do recurso
        duration: Duração do recurso em minutos (para vídeos)
        readTime: Tempo de leitura em minutos (para artigos)
        difficulty: Nível de dificuldade do recurso
        thumbnail: URL da imagem de thumbnail
    """
    id: str
    title: str
    url: str
    type: str  # "article", "video", "documentation", "exercise", etc.
    description: Optional[str] = None
    duration: Optional[int] = None  # in minutes, for videos
    readTime: Optional[int] = None  # in minutes, for articles
    difficulty: Optional[str] = None
    thumbnail: Optional[str] = None  # URL da imagem de thumbnail

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o recurso para um dicionário para serialização.
        Este método é usado pelo sistema de cache.

        Returns:
            Representação em dicionário do recurso
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resource':
        """
        Cria um objeto Resource a partir de um dicionário.
        Este método é usado pelo sistema de cache.

        Args:
            data: Representação em dicionário do recurso

        Returns:
            Objeto Resource
        """
        return cls(**data)

    @validator('type')
    def validate_type(cls, v):
        """Valida se o tipo do recurso é válido."""
        valid_types = ["article", "video", "documentation", "exercise", "tutorial", "course", "book", "tool", "quiz", "other"]
        if v.lower() not in valid_types:
            raise ValueError(f'type deve ser um dos seguintes: {", ".join(valid_types)}')
        return v.lower()

    @validator('duration', 'readTime')
    def validate_time(cls, v):
        """Valida se a duração/tempo de leitura é positivo."""
        if v is not None and v < 0:
            raise ValueError('duration/readTime não pode ser negativo')
        return v

    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Valida se o nível de dificuldade é válido."""
        if v is not None:
            valid_difficulties = ["beginner", "intermediate", "advanced"]
            if v.lower() not in valid_difficulties:
                raise ValueError(f'difficulty deve ser um dos seguintes: {", ".join(valid_difficulties)}')
            return v.lower()
        return v


class Node(BaseModel):
    """
    Modelo para um nó na árvore de aprendizagem.

    Attributes:
        id: Identificador único do nó
        title: Título do nó
        description: Descrição do nó
        type: Tipo do nó (lesson, quiz, project, exercise_set, etc.)
        state: Estado do nó (available, locked, completed)
        resources: Lista de recursos associados ao nó
        prerequisites: Lista de IDs de nós que são pré-requisitos para este nó
        rewards: Lista de recompensas por completar o nó
        hints: Lista de dicas para o nó
        visualPosition: Posição visual do nó na interface
        quiz: Quiz associado ao nó (opcional)
        exerciseSet: Conjunto de exercícios associado ao nó (opcional)
    """
    id: str
    title: str
    description: str
    type: str  # "lesson", "quiz", "project", "exercise_set", etc.
    state: str = "available"  # "available", "locked", "completed"
    resources: List[Resource] = []
    prerequisites: List[str] = []
    rewards: List[str] = []
    hints: List[str] = []
    visualPosition: Dict[str, Union[int, float]] = Field(default_factory=lambda: {"x": 0, "y": 0, "level": 0})
    quiz: Optional[Quiz] = None
    exerciseSet: Optional[ExerciseSet] = None

    @validator('type')
    def validate_type(cls, v):
        """Valida se o tipo do nó é válido."""
        valid_types = ["lesson", "quiz", "project", "exercise_set", "challenge", "assessment", "reference"]
        if v.lower() not in valid_types:
            raise ValueError(f'type deve ser um dos seguintes: {", ".join(valid_types)}')
        return v.lower()

    @validator('state')
    def validate_state(cls, v):
        """Valida se o estado do nó é válido."""
        valid_states = ["available", "locked", "completed", "in_progress"]
        if v.lower() not in valid_states:
            raise ValueError(f'state deve ser um dos seguintes: {", ".join(valid_states)}')
        return v.lower()

    @validator('visualPosition')
    def validate_visual_position(cls, v):
        """Valida se a posição visual contém as chaves necessárias."""
        required_keys = ["x", "y", "level"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f'visualPosition deve conter a chave: {key}')
        return v


class MCP(BaseModel):
    """
    Modelo para um Master Content Plan (MCP).

    Attributes:
        id: Identificador único do MCP
        title: Título do MCP
        description: Descrição do MCP
        topic: Tópico principal do MCP
        category: Categoria do tópico (ex: "technology", "finance", "health")
        language: Idioma do MCP (ex: "pt", "en", "es")
        rootNodeId: ID do nó raiz da árvore de aprendizagem
        nodes: Dicionário de nós, onde a chave é o ID do nó
        totalHours: Estimativa de horas para completar o plano de aprendizagem
        tags: Lista de tags relacionadas ao tópico
        metadata: Metadados do MCP
    """
    id: str
    title: str
    description: str
    topic: str
    category: str
    language: str
    rootNodeId: str
    nodes: Dict[str, Node]
    totalHours: int
    tags: List[str]
    metadata: Metadata = Field(default_factory=Metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para um dicionário."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCP':
        """Cria um modelo a partir de um dicionário."""
        return cls(**data)

    def to_json(self) -> str:
        """Converte o modelo para uma string JSON."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'MCP':
        """Cria um modelo a partir de uma string JSON."""
        import json
        return cls(**json.loads(json_str))


class TaskStatus(str, Enum):
    """Status possíveis para uma tarefa."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskMessage(BaseModel):
    """
    Mensagem de progresso de uma tarefa.

    Attributes:
        time: Timestamp da mensagem
        message: Texto da mensagem
    """
    time: float
    message: str


class TaskInfo(BaseModel):
    """
    Informações sobre uma tarefa assíncrona.

    Attributes:
        id: Identificador único da tarefa
        description: Descrição da tarefa
        status: Status atual da tarefa
        progress: Progresso da tarefa (0-100)
        result: Resultado da tarefa (quando concluída)
        error: Mensagem de erro (quando falha)
        created_at: Timestamp de criação da tarefa
        updated_at: Timestamp da última atualização da tarefa
        completed_at: Timestamp de conclusão da tarefa
        messages: Lista de mensagens de progresso
    """
    id: str
    description: str
    status: TaskStatus
    progress: int
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float
    completed_at: Optional[float] = None
    messages: List[Dict[str, Any]] = []

    @validator('progress')
    def validate_progress(cls, v):
        """Valida se o progresso está entre 0 e 100."""
        if v < 0 or v > 100:
            raise ValueError('progress deve estar entre 0 e 100')
        return v





class TaskCreationResponse(BaseModel):
    """
    Resposta para a criação de uma tarefa.

    Attributes:
        task_id: Identificador único da tarefa criada
        status: Status da criação da tarefa
        message: Mensagem sobre a criação da tarefa
    """
    task_id: str
    status: str = "accepted"
    message: str = "Task created successfully"
