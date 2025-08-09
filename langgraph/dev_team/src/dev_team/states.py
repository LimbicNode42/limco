from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class HumanAssistanceRequest:
  """Request for human assistance when engineers encounter capability gaps"""
  id: str
  work_item_id: str
  engineer_id: str
  request_type: str  # "credentials", "access", "tools", "platform", "approval", "clarification"
  title: str
  description: str
  urgency: str = "medium"  # "low", "medium", "high", "critical"
  required_capabilities: List[str] = field(default_factory=list)
  blocked_tasks: List[str] = field(default_factory=list)
  suggested_solution: Optional[str] = None
  status: str = "pending"  # "pending", "in_progress", "resolved", "rejected"
  created_at: datetime = field(default_factory=datetime.now)
  resolved_at: Optional[datetime] = None
  human_response: Optional[str] = None
  provided_credentials: Dict[str, str] = field(default_factory=dict)
  provided_access: List[str] = field(default_factory=list)
  notes: List[str] = field(default_factory=list)

@dataclass
class CapabilityGap:
  """Represents a capability or access limitation that needs human intervention"""
  gap_type: str  # "missing_credentials", "insufficient_access", "missing_tools", "platform_unavailable", "permission_required"
  resource_name: str
  description: str
  impact_level: str = "medium"  # "low", "medium", "high", "critical"
  alternative_available: bool = False
  alternative_description: Optional[str] = None

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
class ComplexityBasedTeamStructure:
  """Dynamic team structure based on complexity analysis"""
  recommended_managers: int = 1
  recommended_engineers_per_manager: int = 2
  total_recommended_workers: int = 3
  complexity_score: float = 5.0
  requires_iteration: bool = False
  iteration_strategy: Optional[str] = None
  analysis_reasoning: str = ""

@dataclass
class IterationState:
  """Tracks multi-iteration execution state"""
  is_iterative: bool = False
  current_iteration: int = 0
  total_iterations: int = 1
  iteration_work_batches: List[List[str]] = field(default_factory=list)  # work_item_ids per iteration
  iteration_results: List[Dict[str, Any]] = field(default_factory=list)
  iteration_summaries: List[str] = field(default_factory=list)
  
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
  iteration_batch: int = 0  # Which iteration batch this item belongs to
  
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
  human_assistance_requests: List[HumanAssistanceRequest] = field(default_factory=list)
  pending_human_intervention: bool = False
  
  # Dynamic Team Structure State
  team_structure: ComplexityBasedTeamStructure = field(default_factory=ComplexityBasedTeamStructure)
  
  # Iteration Management State  
  iteration_state: IterationState = field(default_factory=IterationState)
  
  # Orchestrator-Worker Pattern State
  work_queue: List[WorkItem] = field(default_factory=list)
  active_managers: List[str] = field(default_factory=list)
  active_engineers: Dict[str, List[str]] = field(default_factory=dict)  # manager_id -> [engineer_ids]
  completed_work: List[WorkItem] = field(default_factory=list)
  
  # Evaluator-Optimizer Pattern State
  evaluation_queue: List[WorkItem] = field(default_factory=list)  # Items in evaluation stages
  failed_work: List[WorkItem] = field(default_factory=list)  # Items that failed after max iterations
  
  # Current workflow state
  current_phase: str = "vision"  # vision, strategy, delegation, execution, evaluation, review, human_assistance
  
  # Enhanced messaging and context
  messages: List[str] = field(default_factory=list)
  strategic_analysis: str = ""
  delegation_plan: str = ""
  implementation_details: str = ""
  qa_results: str = ""