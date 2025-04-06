from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from enum import Enum


class Question(BaseModel):
    id: str
    text: str
    options: List[str]
    correctOptionIndex: int


class Quiz(BaseModel):
    questions: List[Question] = []
    passingScore: int = 70


class Metadata(BaseModel):
    difficulty: str = "intermediate"
    estimatedHours: int = 5
    tags: List[str] = []


class Resource(BaseModel):
    id: str
    title: str
    url: str
    type: str  # "article", "video", "documentation", "exercise", etc.
    description: Optional[str] = None
    duration: Optional[int] = None  # in minutes, for videos
    readTime: Optional[int] = None  # in minutes, for articles
    difficulty: Optional[str] = None
    thumbnail: Optional[str] = None  # URL da imagem de thumbnail


class Node(BaseModel):
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


class MCP(BaseModel):
    id: str
    title: str
    description: str
    rootNodeId: str
    nodes: Dict[str, Node]
    metadata: Metadata = Field(default_factory=Metadata)


class TaskStatus(str, Enum):
    """Status possíveis para uma tarefa."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskMessage(BaseModel):
    """Mensagem de progresso de uma tarefa."""
    time: float
    message: str


class TaskInfo(BaseModel):
    """Informações sobre uma tarefa assíncrona."""
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


class TaskCreationResponse(BaseModel):
    """Resposta para a criação de uma tarefa."""
    task_id: str
    status: str = "accepted"
    message: str = "Task created successfully"
