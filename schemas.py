from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


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
