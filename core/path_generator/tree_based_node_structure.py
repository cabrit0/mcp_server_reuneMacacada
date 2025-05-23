"""
Tree-based implementation of the node structure service.
"""

import uuid
import random
import asyncio
from typing import Dict, List, Tuple, Optional, Set

from infrastructure.logging import logger
from api.models import Node, Resource, Quiz, ExerciseSet
from services.youtube import get_youtube
from core.path_generator.node_structure_service import NodeStructureService
from core.path_generator.quiz_generator_service import QuizGeneratorService
from core.path_generator.exercise_generator_service import ExerciseGeneratorService


class TreeBasedNodeStructure(NodeStructureService):
    """
    Tree-based implementation of the node structure service.
    Creates a tree-like structure of nodes with branches and paths.
    """

    def __init__(self, quiz_generator: QuizGeneratorService, exercise_generator: ExerciseGeneratorService = None):
        """
        Initialize the tree-based node structure service.

        Args:
            quiz_generator: Quiz generator service
            exercise_generator: Exercise generator service (optional)
        """
        self.logger = logger.get_logger("path_generator.node_structure")
        self.quiz_generator = quiz_generator
        self.exercise_generator = exercise_generator
        self.logger.info("Initialized TreeBasedNodeStructure")

    async def create_node_structure(
        self,
        topic: str,
        subtopics: List[str],
        resources: List[Resource],
        min_nodes: int = 15,
        max_nodes: int = 28,
        min_width: int = 3,
        max_width: int = 5,
        min_height: int = 3,
        max_height: int = 7,
        language: str = "pt"
    ) -> Tuple[Dict[str, Node], List[str]]:
        """
        Create a node structure with the given subtopics.
        Optimized for performance with parallel video fetching.

        Args:
            topic: The main topic
            subtopics: List of subtopics
            resources: List of resources to distribute
            min_nodes: Minimum number of nodes
            max_nodes: Maximum number of nodes
            min_width: Minimum width of the tree (nodes at first level)
            max_width: Maximum width at any level of the tree
            min_height: Minimum height of the tree (depth)
            max_height: Maximum height of the tree (depth)
            language: Language for resources

        Returns:
            Tuple of (nodes dictionary, list of node IDs)
        """
        nodes: Dict[str, Node] = {}
        node_ids: List[str] = []

        # Use the min_width and max_width parameters to control the tree structure
        # Higher value means more depth (longer paths), lower means more breadth (wider tree)
        depth_preference = random.uniform(0.3, 0.7)

        # Create a root node
        root_id = f"introduction_{uuid.uuid4().hex[:8]}"
        root_node = Node(
            id=root_id,
            title=f"Introduction to {topic}",
            description=f"Get started with {topic} and learn the basic concepts.",
            type="lesson",
            resources=resources[:2] if resources else [],  # Assign a couple of resources to the root
            prerequisites=[],
            visualPosition={"x": 0, "y": 0, "level": 0}
        )
        nodes[root_id] = root_node
        node_ids.append(root_id)

        # Track used resources by ID to avoid unhashable type issues
        used_resource_ids = set()
        if resources and len(resources) >= 2:
            for r in resources[:2]:
                if hasattr(r, 'id'):
                    used_resource_ids.add(r.id)
                elif isinstance(r, dict) and 'id' in r:
                    used_resource_ids.add(r['id'])

        # Use the first two resources for the root node
        # Assign more resources to the root node (up to 3)
        root_node.resources = resources[:3] if resources else []

        # Get remaining resources
        remaining_resources = [r for r in resources if r.id not in used_resource_ids]

        # Create main branches based on min_width and max_width
        num_main_branches = random.randint(min_width, max_width)  # Use min_width and max_width
        main_branch_ids = []

        # Pre-fetch videos for main branches in parallel
        main_branch_video_tasks = []
        for i in range(min(num_main_branches, len(subtopics))):
            subtopic = subtopics[i]
            main_branch_video_tasks.append(
                get_youtube().search_videos_for_topic(topic, subtopic, max_results=1, language=language)
            )

        # Wait for all video tasks to complete
        main_branch_videos_results = await asyncio.gather(*main_branch_video_tasks, return_exceptions=True)

        # Create main branches
        for i in range(num_main_branches):
            if i < len(subtopics):
                subtopic = subtopics[i]
                branch_id = f"branch_{i}_{uuid.uuid4().hex[:8]}"

                # Assign some resources to this branch
                branch_resources = []

                # Use pre-fetched videos
                if i < len(main_branch_videos_results) and not isinstance(main_branch_videos_results[i], Exception):
                    subtopic_videos = main_branch_videos_results[i]

                    # Adicionar vídeos específicos para este subtópico
                    for video in subtopic_videos:
                        branch_resources.append(video)
                        if hasattr(video, 'id'):
                            used_resource_ids.add(video.id)
                        elif isinstance(video, dict) and 'id' in video:
                            used_resource_ids.add(video['id'])

                # Adicionar outros recursos gerais (até 2 por ramo)
                for _ in range(min(2, len(remaining_resources))):
                    if remaining_resources:
                        resource = random.choice(remaining_resources)
                        branch_resources.append(resource)
                        remaining_resources.remove(resource)
                        if hasattr(resource, 'id'):
                            used_resource_ids.add(resource.id)
                        elif isinstance(resource, dict) and 'id' in resource:
                            used_resource_ids.add(resource['id'])

                branch_node = Node(
                    id=branch_id,
                    title=subtopic,
                    description=f"Learn about {subtopic} and its applications.",
                    type="lesson",
                    resources=branch_resources,
                    prerequisites=[root_id],
                    visualPosition={"x": (i - num_main_branches // 2) * 200, "y": 200, "level": 1}
                )
                nodes[branch_id] = branch_node
                node_ids.append(branch_id)
                main_branch_ids.append(branch_id)

        # Create subnodes for each main branch
        current_level = 2
        current_subtopic_index = num_main_branches

        # Calculate how many subnodes we need to create
        remaining_nodes = max_nodes - len(nodes)
        remaining_subtopics = len(subtopics) - num_main_branches

        # Determine how many subtopics to use for each branch
        subtopics_per_branch = {}
        if remaining_subtopics > 0 and len(main_branch_ids) > 0:
            # Distribute subtopics evenly across branches
            base_count = remaining_subtopics // len(main_branch_ids)
            extra = remaining_subtopics % len(main_branch_ids)

            for i, branch_id in enumerate(main_branch_ids):
                subtopics_per_branch[branch_id] = base_count + (1 if i < extra else 0)

        # Pre-fetch videos for subnodes in parallel
        subnode_video_tasks = {}
        subnode_subtopics = {}

        for branch_id in main_branch_ids:
            if current_subtopic_index >= len(subtopics):
                break

            # Decide how many nodes to create in this branch based on min_height and max_height
            if random.random() < depth_preference:
                # More depth - create a longer path
                branch_length = random.randint(min_height - 1, max_height - 1)  # Adjust for height parameters
                branch_width = 1  # Just one path
            else:
                # More breadth - create a wider branch
                branch_length = random.randint(1, min_height)  # At least min_height levels
                branch_width = random.randint(2, min(3, max_width))  # Control width with max_width

            # Calculate how many subtopics we need for this branch
            nodes_in_branch = min(branch_length * branch_width, subtopics_per_branch.get(branch_id, 0))

            # Pre-fetch videos for this branch's subtopics
            for j in range(nodes_in_branch):
                if current_subtopic_index < len(subtopics):
                    subtopic = subtopics[current_subtopic_index]
                    task_key = f"{branch_id}_{j}"
                    subnode_video_tasks[task_key] = get_youtube().search_videos_for_topic(
                        topic, subtopic, max_results=1, language=language
                    )
                    subnode_subtopics[task_key] = subtopic
                    current_subtopic_index += 1

        # Wait for all video tasks to complete
        subnode_videos_results = {}
        for task_key, task in subnode_video_tasks.items():
            try:
                subnode_videos_results[task_key] = await asyncio.wait_for(task, timeout=5)
            except (asyncio.TimeoutError, Exception) as e:
                self.logger.warning(f"Error fetching videos for subnode {task_key}: {str(e)}")
                subnode_videos_results[task_key] = []

        # For each main branch, create a path of nodes
        current_subtopic_index = num_main_branches  # Reset index
        for branch_id in main_branch_ids:
            # Decide how many nodes to create in this branch based on min_height and max_height
            if random.random() < depth_preference:
                # More depth - create a longer path
                branch_length = random.randint(min_height - 1, max_height - 1)  # Adjust for height parameters
                branch_width = 1  # Just one path
            else:
                # More breadth - create a wider branch
                branch_length = random.randint(1, min_height)  # At least min_height levels
                branch_width = random.randint(2, min(3, max_width))  # Control width with max_width

            # Create the nodes for this branch
            parent_ids = [branch_id]
            for level in range(branch_length):
                new_parent_ids = []
                for parent_id in parent_ids:
                    for width in range(branch_width):
                        if current_subtopic_index < len(subtopics) and len(nodes) < max_nodes:
                            subtopic = subtopics[current_subtopic_index]
                            current_subtopic_index += 1

                            node_id = f"node_{len(nodes)}_{uuid.uuid4().hex[:8]}"

                            # Assign resources
                            node_resources = []

                            # Use pre-fetched videos
                            task_key = f"{branch_id}_{level * branch_width + width}"
                            if task_key in subnode_videos_results:
                                node_videos = subnode_videos_results[task_key]

                                # Adicionar vídeos específicos para este subtópico
                                for video in node_videos:
                                    node_resources.append(video)
                                    if hasattr(video, 'id'):
                                        used_resource_ids.add(video.id)
                                    elif isinstance(video, dict) and 'id' in video:
                                        used_resource_ids.add(video['id'])

                            # Adicionar outros recursos gerais (até 2 por subnó)
                            # Aumentar a probabilidade de atribuir recursos aos nós
                            num_resources = min(2, len(remaining_resources))
                            if random.random() < 0.7:  # 70% de chance de atribuir recursos
                                for _ in range(num_resources):
                                    if remaining_resources:
                                        resource = random.choice(remaining_resources)
                                        node_resources.append(resource)
                                        remaining_resources.remove(resource)
                                        if hasattr(resource, 'id'):
                                            used_resource_ids.add(resource.id)
                                        elif isinstance(resource, dict) and 'id' in resource:
                                            used_resource_ids.add(resource['id'])

                            # Determine node type
                            if level == branch_length - 1 and random.random() < 0.5:
                                node_type = random.choice(["exercise_set", "project", "quiz"])
                            else:
                                node_type = "lesson"

                            # Create the node
                            node = Node(
                                id=node_id,
                                title=subtopic,
                                description=f"Learn about {subtopic} and master its concepts.",
                                type=node_type,
                                resources=node_resources,
                                prerequisites=[parent_id],
                                visualPosition={
                                    "x": (main_branch_ids.index(branch_id) - num_main_branches // 2) * 200 + (width - branch_width // 2) * 100,
                                    "y": (current_level + level) * 200,
                                    "level": current_level + level
                                }
                            )

                            # We'll add quizzes later using distribute_quizzes

                            nodes[node_id] = node
                            node_ids.append(node_id)
                            new_parent_ids.append(node_id)

                parent_ids = new_parent_ids if new_parent_ids else parent_ids

            current_level += branch_length + 1

        # If we still don't have enough nodes, add some more
        while len(nodes) < min_nodes and current_subtopic_index < len(subtopics):
            # Pick a random existing node as parent
            parent_id = random.choice(node_ids)
            subtopic = subtopics[current_subtopic_index]
            current_subtopic_index += 1

            node_id = f"extra_node_{len(nodes)}_{uuid.uuid4().hex[:8]}"

            # Assign resources (até 2 por nó extra)
            node_resources = []
            num_resources = min(2, len(remaining_resources))
            # Aumentar a probabilidade de atribuir recursos aos nós extras
            if random.random() < 0.8:  # 80% de chance de atribuir recursos
                for _ in range(num_resources):
                    if remaining_resources:
                        resource = random.choice(remaining_resources)
                        node_resources.append(resource)
                        remaining_resources.remove(resource)
                        if hasattr(resource, 'id'):
                            used_resource_ids.add(resource.id)
                        elif isinstance(resource, dict) and 'id' in resource:
                            used_resource_ids.add(resource['id'])

            # Create the node
            node = Node(
                id=node_id,
                title=subtopic,
                description=f"Explore {subtopic} in detail.",
                type=random.choice(["lesson", "exercise_set", "project"]),
                resources=node_resources,
                prerequisites=[parent_id],
                visualPosition={
                    "x": random.randint(-500, 500),
                    "y": random.randint(200, 1000),
                    "level": random.randint(1, 5)
                }
            )

            nodes[node_id] = node
            node_ids.append(node_id)

        # Distribute any remaining resources
        if remaining_resources:
            # Identificar nós sem recursos
            nodes_without_resources = [node_id for node_id in node_ids if not nodes[node_id].resources]

            # Priorizar nós sem recursos
            if nodes_without_resources:
                # Distribuir recursos para nós sem recursos primeiro
                for node_id in nodes_without_resources:
                    if not remaining_resources:
                        break
                    # Atribuir até 2 recursos por nó sem recursos
                    for _ in range(min(2, len(remaining_resources))):
                        if remaining_resources:
                            resource = remaining_resources.pop(0)
                            nodes[node_id].resources.append(resource)

            # Distribuir recursos restantes aleatoriamente
            while remaining_resources:
                # Pick a random node, priorizando nós com poucos recursos
                nodes_with_few_resources = [node_id for node_id in node_ids if len(nodes[node_id].resources) < 2]
                if nodes_with_few_resources:
                    node_id = random.choice(nodes_with_few_resources)
                else:
                    node_id = random.choice(node_ids)

                # Adicionar recurso
                resource = remaining_resources.pop(0)
                nodes[node_id].resources.append(resource)

        self.logger.info(f"Created node structure with {len(nodes)} nodes for topic '{topic}'")
        return nodes, node_ids

    def distribute_quizzes(
        self,
        nodes: Dict[str, Node],
        node_ids: List[str],
        topic: str,
        resources: List[Resource],
        target_percentage: float = 0.25
    ) -> Dict[str, Node]:
        """
        Distribute quizzes strategically across the learning tree.

        Args:
            nodes: Dictionary of nodes
            node_ids: List of node IDs
            topic: The main topic
            resources: List of resources
            target_percentage: Target percentage of nodes to have quizzes

        Returns:
            Updated dictionary of nodes
        """
        # Calculate target number of quizzes
        num_nodes = len(nodes)
        target_quizzes = max(1, int(num_nodes * target_percentage))

        # Identify root node
        root_id = node_ids[0] if node_ids else None
        if not root_id:
            return nodes

        # Map the tree structure
        tree_map = self._map_tree_structure(nodes, root_id)

        # Identify branches (paths from root to leaf)
        branches = self._identify_branches(tree_map, root_id)

        # Categorize nodes by level
        levels = self._categorize_nodes_by_level(nodes)

        # Select nodes for quizzes
        quiz_nodes = self._select_quiz_nodes(nodes, branches, levels, target_quizzes)

        # Apply quizzes to selected nodes
        for node_id in quiz_nodes:
            node = nodes[node_id]
            # Get resources for this node
            node_resources = node.resources
            # Generate a quiz based on node resources
            node.quiz = self.quiz_generator.generate_quiz(topic, node.title, node_resources)

        self.logger.info(f"Distributed {len(quiz_nodes)} quizzes across {num_nodes} nodes")
        return nodes

    def distribute_exercises(
        self,
        nodes: Dict[str, Node],
        node_ids: List[str],
        topic: str,
        resources: List[Resource],
        target_percentage: float = 0.15
    ) -> Dict[str, Node]:
        """
        Distribute exercises strategically across the learning tree.

        Args:
            nodes: Dictionary of nodes
            node_ids: List of node IDs
            topic: The main topic
            resources: List of resources
            target_percentage: Target percentage of nodes to have exercises

        Returns:
            Updated dictionary of nodes
        """
        # Check if exercise generator is available
        if not self.exercise_generator:
            self.logger.warning("Exercise generator not available, skipping exercise distribution")
            return nodes

        # Calculate target number of exercise sets
        num_nodes = len(nodes)
        target_exercises = max(1, int(num_nodes * target_percentage))

        # Identify root node
        root_id = node_ids[0] if node_ids else None
        if not root_id:
            return nodes

        # Map the tree structure
        tree_map = self._map_tree_structure(nodes, root_id)

        # Identify branches (paths from root to leaf)
        branches = self._identify_branches(tree_map, root_id)

        # Categorize nodes by level
        levels = self._categorize_nodes_by_level(nodes)

        # Select nodes for exercises (prioritize nodes of type "exercise_set")
        exercise_nodes = self._select_exercise_nodes(nodes, branches, levels, target_exercises)

        # Apply exercises to selected nodes
        for node_id in exercise_nodes:
            node = nodes[node_id]
            # Get resources for this node
            node_resources = node.resources
            # Generate an exercise set based on node resources
            node.exerciseSet = self.exercise_generator.generate_exercise_set(topic, node.title, node_resources)

        self.logger.info(f"Distributed {len(exercise_nodes)} exercise sets across {num_nodes} nodes")
        return nodes

    def _map_tree_structure(self, nodes: Dict[str, Node], _root_id: str) -> Dict[str, List[str]]:
        """
        Map the tree structure with parent-child relationships.

        Args:
            nodes: Dictionary of nodes
            _root_id: ID of the root node

        Returns:
            Dictionary mapping node IDs to lists of child node IDs
        """
        tree_map = {node_id: [] for node_id in nodes}

        # For each node, add it to its prerequisites' children
        for node_id, node in nodes.items():
            for prereq_id in node.prerequisites:
                if prereq_id in tree_map:
                    tree_map[prereq_id].append(node_id)

        return tree_map

    def _identify_branches(self, tree_map: Dict[str, List[str]], root_id: str) -> List[List[str]]:
        """
        Identify all branches (paths from root to leaf).

        Args:
            tree_map: Dictionary mapping node IDs to lists of child node IDs
            root_id: ID of the root node

        Returns:
            List of branches (each branch is a list of node IDs)
        """
        branches = []

        def traverse(node_id, current_path):
            current_path.append(node_id)
            children = tree_map[node_id]

            if not children:  # Leaf node
                branches.append(current_path.copy())
            else:
                for child_id in children:
                    traverse(child_id, current_path)

            current_path.pop()

        # Start traversal from the root
        traverse(root_id, [])

        return branches

    def _categorize_nodes_by_level(self, nodes: Dict[str, Node]) -> Dict[str, List[str]]:
        """
        Categorize nodes by their level in the tree.

        Args:
            nodes: Dictionary of nodes

        Returns:
            Dictionary mapping level names to lists of node IDs
        """
        levels = {"beginner": [], "intermediate": [], "advanced": []}

        for node_id, node in nodes.items():
            level = node.visualPosition.get("level", 0)

            if level <= 1:
                levels["beginner"].append(node_id)
            elif level <= 3:
                levels["intermediate"].append(node_id)
            else:
                levels["advanced"].append(node_id)

        return levels

    def _select_quiz_nodes(self, nodes: Dict[str, Node], branches: List[List[str]], levels: Dict[str, List[str]], target_quizzes: int) -> List[str]:
        """
        Select nodes for quizzes ensuring even distribution.

        Args:
            nodes: Dictionary of nodes
            branches: List of branches (each branch is a list of node IDs)
            levels: Dictionary mapping level names to lists of node IDs
            target_quizzes: Target number of quizzes

        Returns:
            List of node IDs selected for quizzes
        """
        selected_nodes = set()

        # Ensure at least one quiz per branch (if possible)
        for branch in branches:
            if len(selected_nodes) >= target_quizzes:
                break

            # Skip very short branches
            if len(branch) <= 2:
                continue

            # Select a node in the middle of the branch
            mid_index = len(branch) // 2
            selected_nodes.add(branch[mid_index])

        # Distribute remaining quizzes across levels
        remaining = target_quizzes - len(selected_nodes)
        if remaining > 0:
            # Calculate distribution across levels
            level_quotas = {
                "beginner": max(1, int(remaining * 0.3)),
                "intermediate": max(1, int(remaining * 0.5)),
                "advanced": max(1, int(remaining * 0.2))
            }

            # Adjust to ensure sum equals remaining
            total = sum(level_quotas.values())
            if total > remaining:
                # Reduce quotas proportionally
                for level in level_quotas:
                    level_quotas[level] = max(0, int(level_quotas[level] * (remaining / total)))

            # Select nodes from each level
            for level, quota in level_quotas.items():
                candidates = [node_id for node_id in levels[level]
                             if node_id not in selected_nodes]

                # Skip if no candidates
                if not candidates:
                    continue

                # Select nodes with spacing
                selected = self._select_with_spacing(candidates, quota, nodes)
                selected_nodes.update(selected)

        return list(selected_nodes)

    def _select_with_spacing(self, candidates: List[str], quota: int, nodes: Dict[str, Node]) -> List[str]:
        """
        Select nodes with spacing between them.

        Args:
            candidates: List of candidate node IDs
            quota: Number of nodes to select
            nodes: Dictionary of nodes

        Returns:
            List of selected node IDs
        """
        if not candidates:
            return []

        selected = []
        remaining = quota

        # Sort candidates by position
        sorted_candidates = sorted(candidates,
                                  key=lambda x: (nodes[x].visualPosition.get("y", 0),
                                               nodes[x].visualPosition.get("x", 0)))

        # Select with spacing
        i = 0
        while i < len(sorted_candidates) and remaining > 0:
            selected.append(sorted_candidates[i])
            remaining -= 1
            # Skip next node to ensure spacing
            i += 2

        return selected

    def get_nodes(self) -> Dict[str, Node]:
        """
        Get the current nodes dictionary.

        Returns:
            Dictionary of nodes
        """
        # This is a simple implementation that returns an empty dictionary
        # In a real implementation, we would store the nodes as an instance variable
        # and return them here
        return {}

    def _select_exercise_nodes(self, nodes: Dict[str, Node], branches: List[List[str]], levels: Dict[str, List[str]], target_exercises: int) -> List[str]:
        """
        Select nodes for exercises ensuring even distribution and prioritizing nodes of type "exercise_set".

        Args:
            nodes: Dictionary of nodes
            branches: List of branches (each branch is a list of node IDs)
            levels: Dictionary mapping level names to lists of node IDs
            target_exercises: Target number of exercise sets

        Returns:
            List of node IDs selected for exercises
        """
        selected_nodes = set()

        # First, prioritize nodes of type "exercise_set"
        exercise_set_nodes = [node_id for node_id, node in nodes.items() if node.type == "exercise_set"]

        # Add all exercise_set nodes (up to the target)
        for node_id in exercise_set_nodes:
            if len(selected_nodes) >= target_exercises:
                break
            selected_nodes.add(node_id)

        # If we still need more, ensure at least one exercise per branch (if possible)
        if len(selected_nodes) < target_exercises:
            for branch in branches:
                if len(selected_nodes) >= target_exercises:
                    break

                # Skip very short branches
                if len(branch) <= 2:
                    continue

                # Select a node near the end of the branch (for practical exercises after learning)
                end_index = len(branch) - 1
                candidate = branch[end_index]

                # Skip if already selected or if it has a quiz
                if candidate in selected_nodes or nodes[candidate].quiz:
                    continue

                selected_nodes.add(candidate)

        # Distribute remaining exercises across levels, prioritizing intermediate and advanced
        remaining = target_exercises - len(selected_nodes)
        if remaining > 0:
            # Calculate distribution across levels
            level_quotas = {
                "beginner": max(0, int(remaining * 0.1)),
                "intermediate": max(1, int(remaining * 0.5)),
                "advanced": max(1, int(remaining * 0.4))
            }

            # Adjust to ensure sum equals remaining
            total = sum(level_quotas.values())
            if total > remaining:
                # Reduce quotas proportionally
                for level in level_quotas:
                    level_quotas[level] = max(0, int(level_quotas[level] * (remaining / total)))

            # Select nodes from each level
            for level, quota in level_quotas.items():
                candidates = [node_id for node_id in levels[level]
                             if node_id not in selected_nodes and not nodes[node_id].quiz]

                # Skip if no candidates
                if not candidates:
                    continue

                # Select nodes with spacing
                selected = self._select_with_spacing(candidates, quota, nodes)
                selected_nodes.update(selected)

        return list(selected_nodes)
