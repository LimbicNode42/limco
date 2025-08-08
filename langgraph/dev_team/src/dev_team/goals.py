from dataclasses import dataclass, field
from typing import Dict, List, Optional

from utils_state import LangGraphImage

@dataclass
class EvaluationLoop:
  """Tracks the evaluation-optimization loop state"""
  current_stage: str = "development"  # development, unit_test, self_review, peer_review, integration_test, manager_review, cto_review
  loop_count: int = 0
  max_loops: int = 3
  escalation_count: int = 0
  max_escalations: int = 3
  feedback: List[str] = field(default_factory=list)
  evaluator: str = ""
  
@dataclass
class WorkItem:
  """Represents a piece of work that can be delegated"""
  id: str
  title: str
  description: str
  priority: int = 1  # 1-5, with 5 being highest
  assigned_to: Optional[str] = None
  status: str = "pending"  # pending, assigned, in_development, in_evaluation, completed, escalated, failed
  result: Optional[str] = None
  created_by: str = ""
  
  # Evaluator-Optimizer Pattern State
  evaluation_loop: EvaluationLoop = field(default_factory=EvaluationLoop)

@dataclass
class State:
  """This is the state for the entire graph"""
  name: str = "Dev Team"
  description: str = "A graph for a company to track their goals and progress."
  start_node: str = "__start__"
  
  # Human-in-the-loop State
  project_goals: str = "Define project objectives"
  
  # Orchestrator-Worker Pattern State
  work_queue: List[WorkItem] = field(default_factory=list)
  active_managers: List[str] = field(default_factory=list)
  active_engineers: Dict[str, List[str]] = field(default_factory=dict)  # manager_id -> [engineer_ids]
  completed_work: List[WorkItem] = field(default_factory=list)
  
  # Evaluator-Optimizer Pattern State
  evaluation_queue: List[WorkItem] = field(default_factory=list)  # Items in evaluation stages
  failed_work: List[WorkItem] = field(default_factory=list)  # Items that failed after max iterations
  
  # Current workflow state
  current_phase: str = "vision"  # vision, strategy, delegation, execution, evaluation, review

@dataclass
class Vision:
  """This is goal tracking for the Founder/CEO"""

  goal: str = """
    - Become the industry leader in AI-driven business communication solutions. 
    - Offer an innovative alternative platform that supercedes traditional business communication tools like Slack and Microsoft Teams.
    - The innovative and differentiating sauce is the use of AI to generate summaries in a branching conversation graph instead of the traditional chain format.
  """
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 5 * 360 # days

@dataclass
class TechnologyStrategy:
  """This is goal tracking for the CTO"""

  goal: str = """
    - Develop a graph based communication platform that integrates AI capabilities.
    - Each node is a topic of conversation, allowing for structured and efficient discussions.
    - Rather than a single chat history, each node will have its own history.
    - To avoid cognitive overload each node will contain an AI generated summary of the conversation.
    - Rather than engineers disputing each other the AI node summary will contain the AI's own research and provide options with pros and cons of each engineers proposals.
    - Each node will have a set of AI generated diagrams that can be used to visualize the conversation.
    - Each node will have a timer that will be used to track the time spent on the conversation.
    - Each node will have a timer that will be used to track the staleness of the conversation.
    - Each node will have tags so that engineers can filter conversations by topics of interest to them.
    - Similar to a social media platform nodes will be ranked on their hotness/trendingness.
    - Similar to a social media platform engineers will have a "For You" feed that will show them the most relevant nodes based on their interests and past interactions.
  """
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 360 # days
  
  # Orchestrator capabilities
  work_breakdown: List[WorkItem] = field(default_factory=list)
  delegation_strategy: str = "balanced"  # balanced, priority, expertise
  max_managers: int = 3

@dataclass
class TechnologyIteration:
  """This is goal tracking for the Engineering Manager"""

  goal: str = ""
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 30 # days
  
  # Manager-specific fields
  manager_id: str = ""
  assigned_work: List[WorkItem] = field(default_factory=list)
  engineer_assignments: Dict[str, List[str]] = field(default_factory=dict)  # engineer_id -> [work_item_ids]
  max_engineers: int = 5

@dataclass
class TechnologyTask:
  """This is goal tracking for the Senior Engineer"""

  goal: str = ""
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 15 # days
  
  # Engineer-specific fields
  engineer_id: str = ""
  assigned_work_items: List[WorkItem] = field(default_factory=list)
  completed_tasks: List[WorkItem] = field(default_factory=list)
  manager_id: str = ""  # Which manager this engineer reports to
