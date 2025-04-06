"""
Módulo de gerenciamento de tarefas assíncronas para o MCP Server.

Este módulo fornece funcionalidades para criar, atualizar e obter o status de tarefas
assíncronas, permitindo que o servidor responda imediatamente ao cliente enquanto
processa tarefas demoradas em segundo plano.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable, List
from enum import Enum

# Configurar logging
logger = logging.getLogger("mcp_server.task_manager")

class TaskStatus(str, Enum):
    """Status possíveis para uma tarefa."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Representa uma tarefa assíncrona com status e progresso."""
    
    def __init__(self, task_id: str, description: str):
        self.id = task_id
        self.description = description
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.updated_at = time.time()
        self.completed_at = None
        self.messages: List[Dict[str, Any]] = []
    
    def update_progress(self, progress: int, message: str = None):
        """Atualiza o progresso da tarefa."""
        self.progress = min(max(progress, 0), 100)  # Garantir que está entre 0-100
        self.updated_at = time.time()
        
        if message:
            self.add_message(message)
        
        logger.info(f"Task {self.id} progress: {self.progress}% - {message}")
    
    def add_message(self, message: str):
        """Adiciona uma mensagem ao histórico da tarefa."""
        self.messages.append({
            "time": time.time(),
            "message": message
        })
    
    def mark_as_running(self):
        """Marca a tarefa como em execução."""
        self.status = TaskStatus.RUNNING
        self.updated_at = time.time()
        self.add_message("Tarefa iniciada")
    
    def mark_as_completed(self, result: Any = None):
        """Marca a tarefa como concluída."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.result = result
        self.updated_at = time.time()
        self.completed_at = time.time()
        self.add_message("Tarefa concluída com sucesso")
    
    def mark_as_failed(self, error: str):
        """Marca a tarefa como falha."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = time.time()
        self.completed_at = time.time()
        self.add_message(f"Tarefa falhou: {error}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a tarefa para um dicionário."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "messages": self.messages
        }


class TaskManager:
    """Gerenciador de tarefas assíncronas."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.max_tasks = 100  # Limite de tarefas armazenadas
    
    def create_task(self, description: str) -> Task:
        """
        Cria uma nova tarefa.
        
        Args:
            description: Descrição da tarefa
            
        Returns:
            A tarefa criada
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, description)
        
        # Limpar tarefas antigas se necessário
        if len(self.tasks) >= self.max_tasks:
            self._clean_old_tasks()
        
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id}: {description}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtém uma tarefa pelo ID.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            A tarefa ou None se não encontrada
        """
        return self.tasks.get(task_id)
    
    def _clean_old_tasks(self):
        """Remove tarefas antigas para liberar espaço."""
        # Ordenar tarefas por data de criação (mais antigas primeiro)
        sorted_tasks = sorted(
            self.tasks.items(),
            key=lambda x: x[1].created_at
        )
        
        # Remover 10% das tarefas mais antigas
        tasks_to_remove = max(1, len(self.tasks) // 10)
        for i in range(tasks_to_remove):
            if i < len(sorted_tasks):
                task_id = sorted_tasks[i][0]
                del self.tasks[task_id]
                logger.info(f"Removed old task {task_id}")
    
    async def run_task(
        self,
        task: Task,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Executa uma função assíncrona como uma tarefa.
        
        Args:
            task: A tarefa a ser executada
            func: A função assíncrona a ser executada
            *args, **kwargs: Argumentos para a função
            
        Returns:
            O resultado da função
        """
        task.mark_as_running()
        
        try:
            # Executar a função
            result = await func(*args, **kwargs)
            
            # Marcar como concluída
            task.mark_as_completed(result)
            return result
            
        except Exception as e:
            # Marcar como falha
            error_message = str(e)
            logger.error(f"Task {task.id} failed: {error_message}")
            task.mark_as_failed(error_message)
            raise
    
    def get_all_tasks(self) -> Dict[str, Task]:
        """Retorna todas as tarefas."""
        return self.tasks


# Instância global do gerenciador de tarefas
task_manager = TaskManager()
