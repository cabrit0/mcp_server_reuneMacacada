import uuid
import random
from typing import Dict, List, Tuple

from schemas import MCP, Node, Resource, Metadata, Quiz, Question


def generate_subtopics(topic: str, count: int = 10) -> List[str]:
    """
    Generate subtopics based on a main topic.

    Args:
        topic: The main topic
        count: Number of subtopics to generate

    Returns:
        List of subtopic strings
    """
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
    subtopics = []

    # Add some direct topic terms
    subtopics.extend(random.sample(topic_terms, min(len(topic_terms), count // 3)))

    # Add prefix + topic combinations
    for prefix in random.sample(prefixes, min(len(prefixes), count // 3)):
        subtopics.append(f"{prefix} {topic}")

    # Add topic + suffix combinations
    for suffix in random.sample(suffixes, min(len(suffixes), count // 3)):
        subtopics.append(f"{topic} {suffix}")

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


def create_node_structure(topic: str, subtopics: List[str], resources: List[Resource], min_nodes: int = 15, max_nodes: int = 28) -> Tuple[Dict[str, Node], List[str]]:
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
            for _ in range(min(2, len(remaining_resources))):
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

                        # Add quiz for lesson nodes
                        if node_type == "lesson" and random.random() < 0.3:
                            node.quiz = generate_quiz(topic, subtopic, node_resources)

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


def generate_learning_path(topic: str, resources: List[Resource], min_nodes: int = 15, max_nodes: int = 28) -> MCP:
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

    # Generate subtopics for the learning path
    num_subtopics = random.randint(20, 35)  # Generate more than we need to have variety
    subtopics = generate_subtopics(topic, num_subtopics)

    # Create node structure with randomness
    nodes, node_ids = create_node_structure(topic, subtopics, resources, min_nodes, max_nodes)

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


def group_resources(topic: str, resources: List[Resource]) -> Dict[str, List[Resource]]:
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


def generate_quiz(topic: str, group_name: str, resources: List[Resource]) -> Quiz:
    """
    Generate a quiz for a node.

    Args:
        topic: The topic of the learning path
        group_name: The name of the group
        resources: List of resources in the group

    Returns:
        Quiz object with placeholder questions
    """
    # Create placeholder questions
    questions = [
        Question(
            id=f"q_{uuid.uuid4().hex[:8]}",
            text=f"What is the main purpose of {topic}?",
            options=[
                f"To simplify {topic} development",
                f"To optimize {topic} performance",
                f"To standardize {topic} implementation",
                f"To visualize {topic} data"
            ],
            correctOptionIndex=0
        ),
        Question(
            id=f"q_{uuid.uuid4().hex[:8]}",
            text=f"Which of the following is NOT a feature of {topic}?",
            options=[
                f"Easy integration with other systems",
                f"Built-in security features",
                f"Automatic code generation",
                f"Cross-platform compatibility"
            ],
            correctOptionIndex=2
        )
    ]

    return Quiz(questions=questions, passingScore=70)


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
