import uuid
import random
import asyncio
from typing import Dict, List, Tuple, Optional

from schemas import MCP, Node, Resource, Metadata, Quiz, Question
from categories import get_subtopics_for_category, detect_category
from youtube_integration import search_videos_for_subtopic


def generate_subtopics(topic: str, count: int = 10) -> List[str]:
    """
    Generate subtopics based on a main topic using category-specific templates.

    Args:
        topic: The main topic
        count: Number of subtopics to generate

    Returns:
        List of subtopic strings
    """
    # Get category-specific subtopics
    category_subtopics = get_subtopics_for_category(topic, count)

    # If we got enough subtopics from the category, return them
    if len(category_subtopics) >= count:
        return category_subtopics[:count]

    # Otherwise, fill in with generic subtopics
    # Common prefixes and suffixes to create subtopics
    prefixes = [
        "Introduction to", "Getting Started with", "Understanding", "Basics of",
        "Advanced", "Mastering", "Practical", "Exploring", "Deep Dive into",
        "Essential", "Fundamentals of", "Working with", "Building with",
        "Developing with", "Professional", "Modern", "Effective", "Efficient",
        "Comprehensive Guide to", "Quick Start with", "Step-by-Step", "Hands-on",
        "Theory of", "Principles of", "Concepts in", "Techniques for", "Strategies for",
        "Best Practices in", "Common Patterns in", "Architecture of", "Design Patterns for"
    ]

    suffixes = [
        "Basics", "Fundamentals", "Concepts", "Principles", "Techniques",
        "Patterns", "Best Practices", "Applications", "Examples", "Case Studies",
        "Projects", "Exercises", "Challenges", "Tools", "Libraries", "Frameworks",
        "Development", "Implementation", "Deployment", "Testing", "Debugging",
        "Optimization", "Performance", "Security", "Scalability", "Maintenance",
        "Integration", "APIs", "Data Structures", "Algorithms", "UI/UX", "Frontend", "Backend"
    ]

    # Topic-specific terms (could be expanded based on the actual topic)
    topic_terms = [
        f"{topic} for Beginners",
        f"{topic} for Intermediate Users",
        f"{topic} for Advanced Users",
        f"{topic} in Practice",
        f"{topic} Theory",
        f"Real-world {topic}",
        f"{topic} Architecture",
        f"{topic} Design",
        f"{topic} Implementation",
        f"{topic} Testing",
        f"{topic} Deployment",
        f"{topic} Maintenance",
        f"{topic} Best Practices",
        f"{topic} Common Mistakes",
        f"{topic} Tips and Tricks",
        f"{topic} Performance Optimization",
        f"{topic} Security Considerations",
        f"{topic} Scalability",
        f"{topic} vs. Alternatives",
        f"Future of {topic}"
    ]

    # Generate subtopics using combinations of prefixes, the topic, and suffixes
    subtopics = category_subtopics.copy()

    # Add some direct topic terms if needed
    if len(subtopics) < count:
        remaining_terms = [term for term in topic_terms if term not in subtopics]
        subtopics.extend(random.sample(remaining_terms, min(len(remaining_terms), (count - len(subtopics)) // 3)))

    # Add prefix + topic combinations if needed
    if len(subtopics) < count:
        for prefix in random.sample(prefixes, min(len(prefixes), (count - len(subtopics)) // 3)):
            new_subtopic = f"{prefix} {topic}"
            if new_subtopic not in subtopics:
                subtopics.append(new_subtopic)

    # Add topic + suffix combinations if needed
    if len(subtopics) < count:
        for suffix in random.sample(suffixes, min(len(suffixes), (count - len(subtopics)) // 3)):
            new_subtopic = f"{topic} {suffix}"
            if new_subtopic not in subtopics:
                subtopics.append(new_subtopic)

    # Ensure we have enough subtopics
    while len(subtopics) < count:
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        subtopic = f"{prefix} {topic} {suffix}"
        if subtopic not in subtopics:
            subtopics.append(subtopic)

    # Shuffle and return the requested number of subtopics
    random.shuffle(subtopics)
    return subtopics[:count]


async def create_node_structure(topic: str, subtopics: List[str], resources: List[Resource], min_nodes: int = 15, max_nodes: int = 28, language: str = "pt") -> Tuple[Dict[str, Node], List[str]]:
    """
    Create a node structure with the given subtopics.

    Args:
        topic: The main topic
        subtopics: List of subtopics
        resources: List of resources to distribute
        min_nodes: Minimum number of nodes
        max_nodes: Maximum number of nodes

    Returns:
        Tuple of (nodes dictionary, list of node IDs)
    """
    nodes: Dict[str, Node] = {}
    node_ids: List[str] = []

    # Decide on a structure: more breadth or more depth
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
        used_resource_ids.update([r.id for r in resources[:2]])

    # Use the first two resources for the root node
    root_node.resources = resources[:2] if resources else []

    # Get remaining resources
    remaining_resources = [r for r in resources if r.id not in used_resource_ids]

    # Create main branches
    num_main_branches = random.randint(3, 5)  # 3-5 main branches
    main_branch_ids = []

    for i in range(num_main_branches):
        if i < len(subtopics):
            subtopic = subtopics[i]
            branch_id = f"branch_{i}_{uuid.uuid4().hex[:8]}"

            # Assign some resources to this branch
            branch_resources = []

            # Buscar vídeos específicos para este subtópico
            subtopic_videos = await search_videos_for_subtopic(subtopic, max_results=1, language=language)

            # Adicionar vídeos específicos para este subtópico
            for video in subtopic_videos:
                branch_resources.append(video)
                used_resource_ids.add(video.id)

            # Adicionar outros recursos gerais
            for _ in range(min(1, len(remaining_resources))):
                if remaining_resources:
                    resource = random.choice(remaining_resources)
                    branch_resources.append(resource)
                    remaining_resources.remove(resource)
                    used_resource_ids.add(resource.id)

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

    # For each main branch, create a path of nodes
    for branch_id in main_branch_ids:
        # Decide how many nodes to create in this branch
        if random.random() < depth_preference:
            # More depth - create a longer path
            branch_length = random.randint(2, 4)  # 2-4 nodes in sequence
            branch_width = 1  # Just one path
        else:
            # More breadth - create a wider branch
            branch_length = random.randint(1, 2)  # 1-2 levels
            branch_width = random.randint(2, 3)  # 2-3 nodes per level

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

                        # Buscar vídeos específicos para este subtópico
                        node_videos = await search_videos_for_subtopic(subtopic, max_results=1, language=language)

                        # Adicionar vídeos específicos para este subtópico
                        for video in node_videos:
                            node_resources.append(video)
                            used_resource_ids.add(video.id)

                        # Adicionar outros recursos gerais
                        for _ in range(min(1, len(remaining_resources))):
                            if remaining_resources:
                                resource = random.choice(remaining_resources)
                                node_resources.append(resource)
                                remaining_resources.remove(resource)
                                used_resource_ids.add(resource.id)

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

        # Assign resources
        node_resources = []
        for _ in range(min(1, len(remaining_resources))):
            if remaining_resources:
                resource = random.choice(remaining_resources)
                node_resources.append(resource)
                remaining_resources.remove(resource)
                used_resource_ids.add(resource.id)

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
        for resource in remaining_resources:
            # Pick a random node
            node_id = random.choice(node_ids)
            nodes[node_id].resources.append(resource)

    return nodes, node_ids


async def generate_learning_path(topic: str, resources: List[Resource], min_nodes: int = 15, max_nodes: int = 28, category: Optional[str] = None, language: str = "pt") -> MCP:
    """
    Generate a learning path based on a topic and a list of resources.

    Args:
        topic: The topic of the learning path
        resources: List of resources to include in the path

    Returns:
        MCP object representing the learning path
    """
    # Generate a unique ID for the MCP
    mcp_id = f"{topic.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

    # Create metadata
    metadata = Metadata(
        difficulty="intermediate",
        estimatedHours=estimate_total_hours(resources),
        tags=[topic.lower()] + generate_tags(topic, resources)
    )

    # Use provided category or detect it automatically
    if category is None:
        category = detect_category(topic)
        print(f"Detected category for '{topic}': {category}")
    else:
        print(f"Using provided category for '{topic}': {category}")

    # Generate subtopics for the learning path based on category
    num_subtopics = random.randint(20, 35)  # Generate more than we need to have variety
    subtopics = generate_subtopics(topic, num_subtopics)

    # Create node structure with randomness
    nodes, node_ids = await create_node_structure(topic, subtopics, resources, min_nodes, max_nodes, language=language)

    # Distribute quizzes strategically
    nodes = distribute_quizzes(nodes, node_ids, topic, resources, target_percentage=0.25)

    # Validate that we have enough nodes
    if len(nodes) < min(10, min_nodes):
        raise ValueError(f"Could not generate enough nodes for topic: {topic}. Only generated {len(nodes)} nodes. Please try a different topic or adjust parameters.")

    # Create the MCP
    mcp = MCP(
        id=mcp_id,
        title=f"Learning Path: {topic.title()}",
        description=f"A comprehensive learning path to master {topic}.",
        rootNodeId=node_ids[0] if node_ids else "",
        nodes=nodes,
        metadata=metadata
    )

    return mcp


def group_resources(_topic: str, resources: List[Resource]) -> Dict[str, List[Resource]]:
    """
    Group resources by type and content.

    Args:
        topic: The topic of the learning path
        resources: List of resources to group

    Returns:
        Dictionary mapping group names to lists of resources
    """
    # Define groups
    groups = {
        "Introduction to": [],
        "Fundamentals of": [],
        "Advanced": [],
        "Practical": [],
        "Examples and Exercises for": []
    }

    # Keywords for each group
    keywords = {
        "Introduction to": ["introduction", "getting started", "beginner", "basics", "fundamental"],
        "Fundamentals of": ["tutorial", "guide", "how to", "learn", "course"],
        "Advanced": ["advanced", "expert", "in-depth", "deep dive", "mastering"],
        "Practical": ["project", "application", "implementation", "building", "creating"],
        "Examples and Exercises for": ["example", "exercise", "practice", "challenge", "quiz"]
    }

    # Assign resources to groups based on title, description, and type
    for resource in resources:
        assigned = False

        # Check resource title and description against keywords
        for group, group_keywords in keywords.items():
            if any(keyword in resource.title.lower() or
                   (resource.description and keyword in resource.description.lower())
                   for keyword in group_keywords):
                groups[group].append(resource)
                assigned = True
                break

        # If not assigned based on keywords, assign based on resource type
        if not assigned:
            if resource.type == "documentation":
                groups["Fundamentals of"].append(resource)
            elif resource.type == "video":
                groups["Introduction to"].append(resource)
            elif resource.type == "exercise":
                groups["Examples and Exercises for"].append(resource)
            else:
                # Default to Fundamentals
                groups["Fundamentals of"].append(resource)

    # Ensure we have at least one resource in Introduction
    if not groups["Introduction to"] and groups["Fundamentals of"]:
        # Move the first fundamental resource to introduction
        groups["Introduction to"].append(groups["Fundamentals of"].pop(0))

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def determine_node_type(group_name: str, resources: List[Resource]) -> str:
    """
    Determine the type of node based on the group name and resources.

    Args:
        group_name: The name of the group
        resources: List of resources in the group

    Returns:
        Node type (lesson, exercise_set, project_idea, etc.)
    """
    if "exercise" in group_name.lower() or all(r.type == "exercise" for r in resources):
        return "exercise_set"
    elif "project" in group_name.lower() or any(r.type == "project" for r in resources):
        return "project_idea"
    else:
        return "lesson"


def generate_description(group_name: str, topic: str) -> str:
    """
    Generate a description for a node based on the group name and topic.

    Args:
        group_name: The name of the group
        topic: The topic of the learning path

    Returns:
        Description for the node
    """
    descriptions = {
        "Introduction to": f"Get started with {topic} and learn the basic concepts.",
        "Fundamentals of": f"Learn the core principles and techniques of {topic}.",
        "Advanced": f"Dive deeper into advanced concepts and techniques in {topic}.",
        "Practical": f"Apply your knowledge by building practical applications with {topic}.",
        "Examples and Exercises for": f"Practice your skills with examples and exercises related to {topic}."
    }

    return descriptions.get(group_name, f"Learn about {group_name} {topic}.")


def extract_keywords(resources: List[Resource], _topic: str) -> List[str]:
    """Extract keywords from resources."""
    # Combine all resource titles and descriptions
    text = ""
    for resource in resources:
        text += resource.title + " "
        if resource.description:
            text += resource.description + " "

    # Simple keyword extraction (could be enhanced with NLP)
    words = text.lower().split()
    # Remove common words and short words
    stopwords = ["the", "and", "or", "in", "on", "at", "to", "a", "an", "of", "for", "with",
                "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
                "do", "does", "did", "but", "by", "from"]
    words = [word for word in words if word not in stopwords and len(word) > 3]

    # Count word frequency
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    # Return top keywords
    return [word for word, _ in sorted_words[:10]]


def generate_question(topic: str, node_title: str, keyword: str, question_index: int) -> Question:
    """Generate a question based on a keyword."""
    question_id = f"q_{uuid.uuid4().hex[:8]}"

    # Different question types based on index
    if question_index == 0:
        # Definition question
        text = f"What is {keyword} in the context of {topic}?"
        options = [
            f"A fundamental concept in {topic}",
            f"An advanced technique used in {topic}",
            f"A tool commonly used with {topic}",
            f"A historical aspect of {topic}"
        ]
        correct_index = 0

    elif question_index == 1:
        # Purpose question
        text = f"What is the main purpose of {keyword} in {topic}?"
        options = [
            f"To simplify {topic} processes",
            f"To optimize {topic} performance",
            f"To enhance {topic} functionality",
            f"To standardize {topic} implementation"
        ]
        correct_index = 2

    elif question_index == 2:
        # Relationship question
        text = f"How does {keyword} relate to {node_title}?"
        options = [
            f"It's a prerequisite for understanding {node_title}",
            f"It's an advanced concept that builds on {node_title}",
            f"It's a key component of {node_title}",
            f"It's an alternative approach to {node_title}"
        ]
        correct_index = 2

    else:
        # Negative question
        text = f"Which of the following is NOT associated with {keyword} in {topic}?"
        options = [
            f"Understanding core principles",
            f"Implementing best practices",
            f"Avoiding common pitfalls",
            f"Replacing traditional methods"
        ]
        correct_index = 3

    return Question(
        id=question_id,
        text=text,
        options=options,
        correctOptionIndex=correct_index
    )


def generate_generic_question(_topic: str, node_title: str, index: int) -> Question:
    """Generate a generic question when keywords aren't available."""
    question_id = f"q_{uuid.uuid4().hex[:8]}"

    if index == 0:
        text = f"What is the most important aspect of {node_title}?"
        options = [
            f"Understanding the fundamentals",
            f"Practicing with examples",
            f"Learning advanced techniques",
            f"Exploring related topics"
        ]
        correct_index = 0

    elif index == 1:
        text = f"Which approach is best for learning about {node_title}?"
        options = [
            f"Reading comprehensive guides",
            f"Watching video tutorials",
            f"Hands-on practice with examples",
            f"Discussing with experts"
        ]
        correct_index = 2

    else:
        text = f"What skill is most valuable when working with {node_title}?"
        options = [
            f"Attention to detail",
            f"Creative problem-solving",
            f"Systematic approach",
            f"Technical knowledge"
        ]
        correct_index = 1

    return Question(
        id=question_id,
        text=text,
        options=options,
        correctOptionIndex=correct_index
    )


def generate_quiz(topic: str, node_title: str, resources: List[Resource]) -> Quiz:
    """
    Generate a quiz for a node based on its resources.

    Args:
        topic: The topic of the learning path
        node_title: The title of the node
        resources: List of resources in the node

    Returns:
        Quiz object with questions
    """
    # Extract keywords from resources
    keywords = extract_keywords(resources, topic)

    # Generate questions based on keywords and node title
    questions = []

    # Create 3-5 questions
    num_questions = min(5, max(3, len(keywords)))

    for i in range(num_questions):
        if i < len(keywords):
            keyword = keywords[i]
            # Generate a question based on the keyword
            question = generate_question(topic, node_title, keyword, i)
            questions.append(question)

    # If we couldn't generate enough questions, add generic ones
    while len(questions) < 3:
        question = generate_generic_question(topic, node_title, len(questions))
        questions.append(question)

    return Quiz(questions=questions, passingScore=70)


def map_tree_structure(nodes: Dict[str, Node], _root_id: str) -> Dict[str, List[str]]:
    """Map the tree structure with parent-child relationships."""
    tree_map = {node_id: [] for node_id in nodes}

    # For each node, add it to its prerequisites' children
    for node_id, node in nodes.items():
        for prereq_id in node.prerequisites:
            if prereq_id in tree_map:
                tree_map[prereq_id].append(node_id)

    return tree_map


def identify_branches(tree_map: Dict[str, List[str]], root_id: str) -> List[List[str]]:
    """Identify all branches (paths from root to leaf)."""
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


def categorize_nodes_by_level(nodes: Dict[str, Node]) -> Dict[str, List[str]]:
    """Categorize nodes by their level in the tree."""
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


def select_quiz_nodes(nodes: Dict[str, Node], branches: List[List[str]], levels: Dict[str, List[str]], target_quizzes: int) -> List[str]:
    """Select nodes for quizzes ensuring even distribution."""
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
            selected = select_with_spacing(candidates, quota, nodes)
            selected_nodes.update(selected)

    return list(selected_nodes)


def select_with_spacing(candidates: List[str], quota: int, nodes: Dict[str, Node]) -> List[str]:
    """Select nodes with spacing between them."""
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


def distribute_quizzes(nodes: Dict[str, Node], node_ids: List[str], topic: str, _resources: List[Resource], target_percentage: float = 0.25) -> Dict[str, Node]:
    """Distribute quizzes strategically across the learning tree."""
    # Calculate target number of quizzes
    num_nodes = len(nodes)
    target_quizzes = max(1, int(num_nodes * target_percentage))

    # Identify root node
    root_id = node_ids[0] if node_ids else None
    if not root_id:
        return nodes

    # Map the tree structure
    tree_map = map_tree_structure(nodes, root_id)

    # Identify branches (paths from root to leaf)
    branches = identify_branches(tree_map, root_id)

    # Categorize nodes by level
    levels = categorize_nodes_by_level(nodes)

    # Select nodes for quizzes
    quiz_nodes = select_quiz_nodes(nodes, branches, levels, target_quizzes)

    # Apply quizzes to selected nodes
    for node_id in quiz_nodes:
        node = nodes[node_id]
        # Get resources for this node
        node_resources = node.resources
        # Generate a quiz based on node resources
        node.quiz = generate_quiz(topic, node.title, node_resources)

    return nodes


def estimate_total_hours(resources: List[Resource]) -> int:
    """
    Estimate the total hours needed to complete the learning path.

    Args:
        resources: List of resources in the learning path

    Returns:
        Estimated hours
    """
    total_minutes = 0

    for resource in resources:
        if resource.duration:
            total_minutes += resource.duration
        elif resource.readTime:
            total_minutes += resource.readTime
        else:
            # Default: 30 minutes per resource
            total_minutes += 30

    # Add time for exercises, projects, and quizzes
    total_minutes += len(resources) * 15

    # Convert to hours and round up
    hours = (total_minutes + 59) // 60

    # Ensure a minimum of 1 hour
    return max(1, hours)


def generate_tags(topic: str, resources: List[Resource]) -> List[str]:
    """
    Generate tags for the MCP based on the topic and resources.

    Args:
        topic: The topic of the learning path
        resources: List of resources in the learning path

    Returns:
        List of tags
    """
    # Start with the topic as the main tag
    tags = [topic.lower()]

    # Add tags based on resource types
    resource_types = set(r.type for r in resources)
    for resource_type in resource_types:
        tags.append(resource_type)

    # Add "programming" tag if it seems to be a programming topic
    programming_keywords = ["code", "programming", "development", "software", "app", "web", "language"]
    if any(keyword in topic.lower() for keyword in programming_keywords):
        tags.append("programming")

    # Add "tutorial" tag
    tags.append("tutorial")

    # Limit to 5 tags
    return tags[:5]
