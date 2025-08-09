"""Dynamic Task Complexity Analyzer for Orchestrator-Worker Patterns.

This module provides intelligent task complexity assessment to dynamically determine
how many worker agents (managers, engineers) should be created based on the task
characteristics, while respecting human-set limits and handling iterations for
overflow scenarios.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage

import states
from models import get_model_for_agent


class ComplexityDimension(Enum):
    """Different dimensions of task complexity"""
    SCOPE = "scope"  # How broad the project is
    TECHNICAL_DEPTH = "technical_depth"  # How technically complex
    INTEGRATION_POINTS = "integration_points"  # How many systems/APIs to integrate
    TIMELINE_PRESSURE = "timeline_pressure"  # How tight the timeline
    RISK_LEVEL = "risk_level"  # How risky/critical the project
    COORDINATION_NEEDS = "coordination_needs"  # How much cross-team coordination needed


@dataclass
class ComplexityAssessment:
    """Result of complexity analysis"""
    overall_score: float  # 0.0 to 10.0
    dimension_scores: Dict[ComplexityDimension, float]
    recommended_managers: int
    recommended_engineers_per_manager: int
    total_recommended_workers: int
    reasoning: str
    requires_iteration: bool = False
    iteration_strategy: Optional[str] = None


@dataclass
class ResourceLimits:
    """Human-set limits for resource allocation"""
    max_managers: int = 3
    max_engineers_per_manager: int = 3
    max_total_workers: int = 9
    allow_iterations: bool = True
    max_iterations: int = 3


class TaskComplexityAnalyzer:
    """Analyzes task complexity and recommends optimal team structure"""
    
    def __init__(self):
        self.model = get_model_for_agent("cto")  # Use technical model for analysis
    
    async def analyze_task_complexity(
        self, 
        project_goals: str, 
        work_context: str = "",
        limits: Optional[ResourceLimits] = None,
        config: Optional[RunnableConfig] = None
    ) -> ComplexityAssessment:
        """
        Analyze task complexity and recommend optimal team structure.
        
        Args:
            project_goals: The main project objectives
            work_context: Additional context about the work
            limits: Human-set resource limits
            config: LangGraph configuration
            
        Returns:
            ComplexityAssessment with recommendations
        """
        if limits is None:
            limits = ResourceLimits()
        
        # Create analysis prompt
        system_prompt = self._create_analysis_prompt()
        human_prompt = self._create_task_prompt(project_goals, work_context, limits)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = await self.model.ainvoke(messages)
            analysis_text = response.content
            
            # Parse the structured response
            assessment = self._parse_analysis_response(analysis_text, limits)
            
            print(f"\n🔍 Complexity Analysis Results:")
            print(f"   Overall Complexity: {assessment.overall_score:.1f}/10.0")
            print(f"   Recommended Managers: {assessment.recommended_managers}")
            print(f"   Engineers per Manager: {assessment.recommended_engineers_per_manager}")
            print(f"   Total Workers: {assessment.total_recommended_workers}")
            if assessment.requires_iteration:
                print(f"   ⚠️  Requires Iteration: {assessment.iteration_strategy}")
            
            return assessment
            
        except Exception as e:
            print(f"Error in complexity analysis: {e}")
            # Fallback to conservative estimates
            return ComplexityAssessment(
                overall_score=5.0,
                dimension_scores={dim: 5.0 for dim in ComplexityDimension},
                recommended_managers=1,
                recommended_engineers_per_manager=2,
                total_recommended_workers=3,
                reasoning="Fallback assessment due to analysis error"
            )
    
    def _create_analysis_prompt(self) -> str:
        """Create the system prompt for complexity analysis"""
        return """You are an expert project complexity analyzer and team sizing specialist.

Your job is to analyze project requirements and recommend optimal team structure for a software development project.

Analyze these complexity dimensions (score 0.0-10.0 for each):

1. **SCOPE** (0-10): How broad is the project?
   - 0-2: Single feature/component
   - 3-4: Multiple related features  
   - 5-6: Full application or major system
   - 7-8: Multiple applications/systems
   - 9-10: Platform or ecosystem

2. **TECHNICAL_DEPTH** (0-10): How technically complex?
   - 0-2: Standard CRUD operations
   - 3-4: Complex business logic
   - 5-6: Advanced algorithms, ML/AI
   - 7-8: Distributed systems, real-time processing
   - 9-10: Research-level complexity

3. **INTEGRATION_POINTS** (0-10): How many external dependencies?
   - 0-2: Self-contained or 1-2 APIs
   - 3-4: 3-5 external systems
   - 5-6: 6-10 integration points
   - 7-8: 10+ systems, complex data flows
   - 9-10: Enterprise-wide integration

4. **TIMELINE_PRESSURE** (0-10): How urgent/tight timeline?
   - 0-2: Flexible timeline, no rush
   - 3-4: Standard project timeline
   - 5-6: Somewhat aggressive timeline
   - 7-8: Very tight deadline
   - 9-10: Emergency/crisis timeline

5. **RISK_LEVEL** (0-10): How critical/risky?
   - 0-2: Internal tool, low impact
   - 3-4: Standard business application
   - 5-6: Important customer-facing features
   - 7-8: Business-critical systems
   - 9-10: Mission-critical, high-stakes

6. **COORDINATION_NEEDS** (0-10): How much team coordination required?
   - 0-2: Individual work, minimal coordination
   - 3-4: Small team, standard coordination
   - 5-6: Cross-functional team coordination
   - 7-8: Multiple teams, complex dependencies
   - 9-10: Organization-wide coordination

Based on these scores, recommend team structure:
- **Managers**: 1-3 (each manages a sub-team)
- **Engineers per Manager**: 1-3 (technical workers per sub-team)

**IMPORTANT TEAM SIZING GUIDELINES:**
- For complexity 1-3: 1 manager, 1-2 engineers (2-3 total)
- For complexity 4-6: 1-2 managers, 2-3 engineers each (4-8 total) 
- For complexity 7-8: 2-3 managers, 3 engineers each (9-12 total)
- For complexity 9-10: 3 managers, 3 engineers each (12+ total)

**DO NOT be overly conservative.** Enterprise projects with many components, integrations, and high complexity NEED larger teams.

**CRITICAL**: Always respond in this EXACT format:

SCOPE_SCORE: [0.0-10.0]
TECHNICAL_DEPTH_SCORE: [0.0-10.0]  
INTEGRATION_POINTS_SCORE: [0.0-10.0]
TIMELINE_PRESSURE_SCORE: [0.0-10.0]
RISK_LEVEL_SCORE: [0.0-10.0]
COORDINATION_NEEDS_SCORE: [0.0-10.0]
OVERALL_COMPLEXITY: [0.0-10.0]
RECOMMENDED_MANAGERS: [1-3]
ENGINEERS_PER_MANAGER: [1-3]
REASONING: [Your detailed reasoning for the recommendations]"""

    def _create_task_prompt(self, project_goals: str, work_context: str, limits: ResourceLimits) -> str:
        """Create the human prompt with task details"""
        return f"""Analyze this project for optimal team sizing:

**PROJECT GOALS:**
{project_goals}

**ADDITIONAL CONTEXT:**
{work_context or "No additional context provided"}

**RESOURCE CONSTRAINTS:**
- Maximum Managers: {limits.max_managers}
- Maximum Engineers per Manager: {limits.max_engineers_per_manager}  
- Maximum Total Workers: {limits.max_total_workers}
- Iterations Allowed: {'Yes' if limits.allow_iterations else 'No'}
- Maximum Iterations: {limits.max_iterations if limits.allow_iterations else 'N/A'}

Please analyze the complexity across all dimensions and recommend the optimal team structure within these constraints."""

    def _parse_analysis_response(self, response: str, limits: ResourceLimits) -> ComplexityAssessment:
        """Parse the structured response from the LLM"""
        
        # Extract scores using regex
        patterns = {
            'scope': r'SCOPE_SCORE:\s*([0-9\.]+)',
            'technical_depth': r'TECHNICAL_DEPTH_SCORE:\s*([0-9\.]+)',
            'integration_points': r'INTEGRATION_POINTS_SCORE:\s*([0-9\.]+)',
            'timeline_pressure': r'TIMELINE_PRESSURE_SCORE:\s*([0-9\.]+)',
            'risk_level': r'RISK_LEVEL_SCORE:\s*([0-9\.]+)',
            'coordination_needs': r'COORDINATION_NEEDS_SCORE:\s*([0-9\.]+)',
            'overall': r'OVERALL_COMPLEXITY:\s*([0-9\.]+)',
            'managers': r'RECOMMENDED_MANAGERS:\s*([0-9]+)',
            'engineers': r'ENGINEERS_PER_MANAGER:\s*([0-9]+)',
            'reasoning': r'REASONING:\s*(.+?)(?=\n\n|\Z)'
        }
        
        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                if key in ['managers', 'engineers']:
                    extracted[key] = int(match.group(1))
                elif key == 'reasoning':
                    extracted[key] = match.group(1).strip()
                else:
                    extracted[key] = float(match.group(1))
        
        # Build dimension scores
        dimension_scores = {}
        for dim in ComplexityDimension:
            if dim.value in extracted:
                dimension_scores[dim] = extracted[dim.value]
            else:
                dimension_scores[dim] = 5.0  # Default fallback
        
        # Get recommendations with bounds checking
        recommended_managers = min(extracted.get('managers', 1), limits.max_managers)
        recommended_engineers = min(extracted.get('engineers', 2), limits.max_engineers_per_manager)
        
        # Use raw values to check iteration needs BEFORE applying limits
        raw_managers = extracted.get('managers', 1)
        raw_engineers = extracted.get('engineers', 2)
        raw_total = raw_managers * raw_engineers
        
        # Apply limits for actual recommendations
        total_workers = recommended_managers * recommended_engineers
        
        # Check if we need iteration due to constraints
        requires_iteration = False
        iteration_strategy = None
        
        if raw_total > limits.max_total_workers and limits.allow_iterations:
            requires_iteration = True
            iteration_strategy = f"Task requires {raw_total} workers but limit is {limits.max_total_workers}. Will handle in {(raw_total // limits.max_total_workers) + 1} iterations."
        
        return ComplexityAssessment(
            overall_score=extracted.get('overall', 5.0),
            dimension_scores=dimension_scores,
            recommended_managers=recommended_managers,
            recommended_engineers_per_manager=recommended_engineers,
            total_recommended_workers=total_workers,
            reasoning=extracted.get('reasoning', "No reasoning provided"),
            requires_iteration=requires_iteration,
            iteration_strategy=iteration_strategy
        )


class IterationManager:
    """Manages multi-iteration task execution when worker limits are exceeded"""
    
    def __init__(self):
        self.current_iteration = 0
        self.total_iterations = 0
        self.iteration_results: List[Dict[str, Any]] = []
    
    def plan_iterations(
        self, 
        work_queue: List[states.WorkItem], 
        limits: ResourceLimits,
        total_required_workers: int
    ) -> List[List[states.WorkItem]]:
        """
        Split work queue into iterations based on resource limits.
        
        Args:
            work_queue: All work items to be completed
            limits: Resource constraints
            total_required_workers: Ideal number of workers needed
            
        Returns:
            List of work item batches, one per iteration
        """
        if total_required_workers <= limits.max_total_workers:
            return [work_queue]  # No iteration needed
        
        # Calculate items per iteration
        max_items_per_iteration = limits.max_total_workers
        iterations = []
        
        # Group by priority first, then split
        work_by_priority = {}
        for item in work_queue:
            priority = item.priority
            if priority not in work_by_priority:
                work_by_priority[priority] = []
            work_by_priority[priority].append(item)
        
        # Create iterations, prioritizing high-priority items
        current_batch = []
        current_batch_size = 0
        
        # Sort priorities (5 = highest, 1 = lowest)
        for priority in sorted(work_by_priority.keys(), reverse=True):
            for item in work_by_priority[priority]:
                if current_batch_size >= max_items_per_iteration:
                    iterations.append(current_batch)
                    current_batch = []
                    current_batch_size = 0
                
                current_batch.append(item)
                current_batch_size += 1
        
        # Add remaining items
        if current_batch:
            iterations.append(current_batch)
        
        self.total_iterations = len(iterations)
        
        print(f"\n🔄 Iteration Planning:")
        print(f"   Total work items: {len(work_queue)}")
        print(f"   Required workers: {total_required_workers}")
        print(f"   Max workers per iteration: {limits.max_total_workers}")
        print(f"   Planned iterations: {self.total_iterations}")
        
        return iterations
    
    def should_continue_iteration(self) -> bool:
        """Check if there are more iterations to run"""
        return self.current_iteration < self.total_iterations
    
    def advance_iteration(self) -> int:
        """Move to next iteration and return current iteration number"""
        self.current_iteration += 1
        return self.current_iteration
    
    def record_iteration_result(self, result: Dict[str, Any]):
        """Record the results of current iteration"""
        self.iteration_results.append({
            "iteration": self.current_iteration,
            "timestamp": result.get("timestamp"),
            "completed_work": result.get("completed_work", []),
            "summary": result.get("summary", "")
        })
    
    def get_iteration_summary(self) -> str:
        """Get summary of all completed iterations"""
        if not self.iteration_results:
            return "No iterations completed yet"
        
        summary_parts = [f"Completed {len(self.iteration_results)} iterations:"]
        
        for result in self.iteration_results:
            completed_count = len(result.get("completed_work", []))
            summary_parts.append(f"  Iteration {result['iteration']}: {completed_count} items completed")
        
        return "\n".join(summary_parts)


# Convenience functions for use in agents
async def assess_project_complexity(
    project_goals: str,
    work_context: str = "",
    config: Optional[RunnableConfig] = None
) -> ComplexityAssessment:
    """Convenience function to assess project complexity"""
    analyzer = TaskComplexityAnalyzer()
    
    # Extract limits from config if available
    configuration = config.get("configurable", {}) if config else {}
    limits = ResourceLimits(
        max_managers=configuration.get("max_managers", 3),
        max_engineers_per_manager=configuration.get("max_engineers_per_manager", 3),
        max_total_workers=configuration.get("max_total_workers", 9),
        allow_iterations=configuration.get("allow_iterations", True),
        max_iterations=configuration.get("max_iterations", 3)
    )
    
    return await analyzer.analyze_task_complexity(project_goals, work_context, limits, config)


def create_iteration_manager() -> IterationManager:
    """Create a new iteration manager"""
    return IterationManager()
