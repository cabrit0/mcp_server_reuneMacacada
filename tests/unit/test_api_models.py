"""
Testes unitários para os modelos de dados da API.
"""

import pytest
from pydantic import ValidationError
import json
from api.models import (
    Question,
    Quiz,
    Metadata,
    Resource,
    Node,
    MCP,
    TaskStatus,
    TaskMessage,
    TaskInfo,
    TaskCreationResponse
)


class TestQuestion:
    """Testes para o modelo Question."""

    def test_valid_question(self):
        """Teste de criação de uma pergunta válida."""
        question = Question(
            id="q1",
            text="Qual é a capital do Brasil?",
            options=["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
            correctOptionIndex=2
        )
        assert question.id == "q1"
        assert question.text == "Qual é a capital do Brasil?"
        assert len(question.options) == 4
        assert question.correctOptionIndex == 2

    def test_invalid_correct_option_index(self):
        """Teste de validação do índice da opção correta."""
        # Índice maior que o número de opções
        with pytest.raises(ValidationError):
            Question(
                id="q1",
                text="Qual é a capital do Brasil?",
                options=["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
                correctOptionIndex=4
            )

        # Índice negativo
        with pytest.raises(ValidationError):
            Question(
                id="q1",
                text="Qual é a capital do Brasil?",
                options=["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
                correctOptionIndex=-1
            )


class TestQuiz:
    """Testes para o modelo Quiz."""

    def test_valid_quiz(self):
        """Teste de criação de um quiz válido."""
        quiz = Quiz(
            questions=[
                Question(
                    id="q1",
                    text="Qual é a capital do Brasil?",
                    options=["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
                    correctOptionIndex=2
                ),
                Question(
                    id="q2",
                    text="Qual é a capital da Argentina?",
                    options=["Buenos Aires", "Córdoba", "Rosário", "Mendoza"],
                    correctOptionIndex=0
                )
            ],
            passingScore=70
        )
        assert len(quiz.questions) == 2
        assert quiz.passingScore == 70

    def test_invalid_passing_score(self):
        """Teste de validação da pontuação mínima."""
        # Pontuação negativa
        with pytest.raises(ValidationError):
            Quiz(
                questions=[],
                passingScore=-10
            )

        # Pontuação maior que 100
        with pytest.raises(ValidationError):
            Quiz(
                questions=[],
                passingScore=110
            )


class TestMetadata:
    """Testes para o modelo Metadata."""

    def test_valid_metadata(self):
        """Teste de criação de metadados válidos."""
        metadata = Metadata(
            difficulty="intermediate",
            estimatedHours=10,
            tags=["python", "programming", "beginner"]
        )
        assert metadata.difficulty == "intermediate"
        assert metadata.estimatedHours == 10
        assert len(metadata.tags) == 3

    def test_invalid_difficulty(self):
        """Teste de validação da dificuldade."""
        with pytest.raises(ValidationError):
            Metadata(
                difficulty="super-hard",  # Valor inválido
                estimatedHours=10,
                tags=["python", "programming", "beginner"]
            )

    def test_invalid_estimated_hours(self):
        """Teste de validação das horas estimadas."""
        with pytest.raises(ValidationError):
            Metadata(
                difficulty="intermediate",
                estimatedHours=-5,  # Valor inválido
                tags=["python", "programming", "beginner"]
            )


class TestResource:
    """Testes para o modelo Resource."""

    def test_valid_resource(self):
        """Teste de criação de um recurso válido."""
        resource = Resource(
            id="r1",
            title="Introdução ao Python",
            url="https://example.com/python-intro",
            type="article",
            description="Um guia para iniciantes em Python",
            readTime=15,
            difficulty="beginner",
            thumbnail="https://example.com/images/python-thumb.jpg"
        )
        assert resource.id == "r1"
        assert resource.title == "Introdução ao Python"
        assert resource.url == "https://example.com/python-intro"
        assert resource.type == "article"
        assert resource.description == "Um guia para iniciantes em Python"
        assert resource.readTime == 15
        assert resource.difficulty == "beginner"
        assert resource.thumbnail == "https://example.com/images/python-thumb.jpg"

    def test_invalid_type(self):
        """Teste de validação do tipo de recurso."""
        with pytest.raises(ValidationError):
            Resource(
                id="r1",
                title="Introdução ao Python",
                url="https://example.com/python-intro",
                type="invalid-type",  # Valor inválido
                description="Um guia para iniciantes em Python"
            )

    def test_invalid_duration(self):
        """Teste de validação da duração."""
        with pytest.raises(ValidationError):
            Resource(
                id="r1",
                title="Introdução ao Python",
                url="https://example.com/python-intro",
                type="video",
                description="Um vídeo para iniciantes em Python",
                duration=-10  # Valor inválido
            )


class TestNode:
    """Testes para o modelo Node."""

    def test_valid_node(self):
        """Teste de criação de um nó válido."""
        node = Node(
            id="n1",
            title="Introdução ao Python",
            description="Aprenda os conceitos básicos de Python",
            type="lesson",
            resources=[
                Resource(
                    id="r1",
                    title="Introdução ao Python",
                    url="https://example.com/python-intro",
                    type="article"
                )
            ],
            prerequisites=["n0"],
            visualPosition={"x": 100, "y": 200, "level": 1}
        )
        assert node.id == "n1"
        assert node.title == "Introdução ao Python"
        assert node.type == "lesson"
        assert len(node.resources) == 1
        assert node.prerequisites == ["n0"]
        assert node.visualPosition["x"] == 100
        assert node.visualPosition["y"] == 200
        assert node.visualPosition["level"] == 1

    def test_invalid_type(self):
        """Teste de validação do tipo de nó."""
        with pytest.raises(ValidationError):
            Node(
                id="n1",
                title="Introdução ao Python",
                description="Aprenda os conceitos básicos de Python",
                type="invalid-type",  # Valor inválido
                resources=[]
            )

    def test_invalid_state(self):
        """Teste de validação do estado do nó."""
        with pytest.raises(ValidationError):
            Node(
                id="n1",
                title="Introdução ao Python",
                description="Aprenda os conceitos básicos de Python",
                type="lesson",
                state="invalid-state",  # Valor inválido
                resources=[]
            )

    def test_invalid_visual_position(self):
        """Teste de validação da posição visual."""
        with pytest.raises(ValidationError):
            Node(
                id="n1",
                title="Introdução ao Python",
                description="Aprenda os conceitos básicos de Python",
                type="lesson",
                resources=[],
                visualPosition={"x": 100}  # Faltam chaves obrigatórias
            )


class TestMCP:
    """Testes para o modelo MCP."""

    def test_valid_mcp(self):
        """Teste de criação de um MCP válido."""
        mcp = MCP(
            id="mcp1",
            title="Aprendendo Python",
            description="Um plano de aprendizagem para Python",
            rootNodeId="n0",
            nodes={
                "n0": Node(
                    id="n0",
                    title="Introdução ao Python",
                    description="Aprenda os conceitos básicos de Python",
                    type="lesson",
                    resources=[]
                ),
                "n1": Node(
                    id="n1",
                    title="Variáveis e Tipos de Dados",
                    description="Aprenda sobre variáveis e tipos de dados em Python",
                    type="lesson",
                    resources=[],
                    prerequisites=["n0"]
                )
            }
        )
        assert mcp.id == "mcp1"
        assert mcp.title == "Aprendendo Python"
        assert mcp.rootNodeId == "n0"
        assert len(mcp.nodes) == 2
        assert "n0" in mcp.nodes
        assert "n1" in mcp.nodes

    def test_to_dict(self):
        """Teste do método to_dict."""
        mcp = MCP(
            id="mcp1",
            title="Aprendendo Python",
            description="Um plano de aprendizagem para Python",
            rootNodeId="n0",
            nodes={
                "n0": Node(
                    id="n0",
                    title="Introdução ao Python",
                    description="Aprenda os conceitos básicos de Python",
                    type="lesson",
                    resources=[]
                )
            }
        )
        mcp_dict = mcp.to_dict()
        assert isinstance(mcp_dict, dict)
        assert mcp_dict["id"] == "mcp1"
        assert mcp_dict["title"] == "Aprendendo Python"
        assert mcp_dict["rootNodeId"] == "n0"
        assert "n0" in mcp_dict["nodes"]

    def test_to_json(self):
        """Teste do método to_json."""
        mcp = MCP(
            id="mcp1",
            title="Aprendendo Python",
            description="Um plano de aprendizagem para Python",
            rootNodeId="n0",
            nodes={
                "n0": Node(
                    id="n0",
                    title="Introdução ao Python",
                    description="Aprenda os conceitos básicos de Python",
                    type="lesson",
                    resources=[]
                )
            }
        )
        mcp_json = mcp.to_json()
        assert isinstance(mcp_json, str)
        
        # Verificar se o JSON é válido
        mcp_dict = json.loads(mcp_json)
        assert mcp_dict["id"] == "mcp1"
        assert mcp_dict["title"] == "Aprendendo Python"

    def test_from_dict(self):
        """Teste do método from_dict."""
        mcp_dict = {
            "id": "mcp1",
            "title": "Aprendendo Python",
            "description": "Um plano de aprendizagem para Python",
            "rootNodeId": "n0",
            "nodes": {
                "n0": {
                    "id": "n0",
                    "title": "Introdução ao Python",
                    "description": "Aprenda os conceitos básicos de Python",
                    "type": "lesson",
                    "resources": [],
                    "prerequisites": [],
                    "rewards": [],
                    "hints": [],
                    "visualPosition": {"x": 0, "y": 0, "level": 0},
                    "state": "available"
                }
            }
        }
        mcp = MCP.from_dict(mcp_dict)
        assert mcp.id == "mcp1"
        assert mcp.title == "Aprendendo Python"
        assert mcp.rootNodeId == "n0"
        assert "n0" in mcp.nodes

    def test_from_json(self):
        """Teste do método from_json."""
        mcp_json = """
        {
            "id": "mcp1",
            "title": "Aprendendo Python",
            "description": "Um plano de aprendizagem para Python",
            "rootNodeId": "n0",
            "nodes": {
                "n0": {
                    "id": "n0",
                    "title": "Introdução ao Python",
                    "description": "Aprenda os conceitos básicos de Python",
                    "type": "lesson",
                    "resources": [],
                    "prerequisites": [],
                    "rewards": [],
                    "hints": [],
                    "visualPosition": {"x": 0, "y": 0, "level": 0},
                    "state": "available"
                }
            }
        }
        """
        mcp = MCP.from_json(mcp_json)
        assert mcp.id == "mcp1"
        assert mcp.title == "Aprendendo Python"
        assert mcp.rootNodeId == "n0"
        assert "n0" in mcp.nodes


class TestTaskInfo:
    """Testes para o modelo TaskInfo."""

    def test_valid_task_info(self):
        """Teste de criação de informações de tarefa válidas."""
        task_info = TaskInfo(
            id="task1",
            description="Gerar MCP para Python",
            status=TaskStatus.RUNNING,
            progress=50,
            created_at=1650123456.789,
            updated_at=1650123466.789
        )
        assert task_info.id == "task1"
        assert task_info.description == "Gerar MCP para Python"
        assert task_info.status == TaskStatus.RUNNING
        assert task_info.progress == 50
        assert task_info.created_at == 1650123456.789
        assert task_info.updated_at == 1650123466.789

    def test_invalid_progress(self):
        """Teste de validação do progresso."""
        # Progresso negativo
        with pytest.raises(ValidationError):
            TaskInfo(
                id="task1",
                description="Gerar MCP para Python",
                status=TaskStatus.RUNNING,
                progress=-10,
                created_at=1650123456.789,
                updated_at=1650123466.789
            )

        # Progresso maior que 100
        with pytest.raises(ValidationError):
            TaskInfo(
                id="task1",
                description="Gerar MCP para Python",
                status=TaskStatus.RUNNING,
                progress=110,
                created_at=1650123456.789,
                updated_at=1650123466.789
            )


class TestTaskCreationResponse:
    """Testes para o modelo TaskCreationResponse."""

    def test_valid_task_creation_response(self):
        """Teste de criação de uma resposta de criação de tarefa válida."""
        response = TaskCreationResponse(
            task_id="task1",
            status="accepted",
            message="Task created successfully"
        )
        assert response.task_id == "task1"
        assert response.status == "accepted"
        assert response.message == "Task created successfully"
