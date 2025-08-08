from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
