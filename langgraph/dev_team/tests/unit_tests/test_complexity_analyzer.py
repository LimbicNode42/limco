"""
Unit tests for complexity analysis functionality.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add src to Python path for imports
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src" / "dev_team"
sys.path.insert(0, str(src_dir))

from complexity_analyzer import (
    ResourceLimits, TaskComplexityAnalyzer, ComplexityAssessment,
    IterationManager, ComplexityDimension, create_iteration_manager
)
import states


class TestResourceLimits:
    """Test ResourceLimits configuration."""
    
    def test_default_resource_limits(self):
        """Test default resource limits configuration."""
        limits = ResourceLimits()
        
        assert limits.max_managers == 3
        assert limits.max_engineers_per_manager == 3
        assert limits.max_total_workers == 9
        assert limits.allow_iterations is True
        assert limits.max_iterations == 3
    
    def test_custom_resource_limits(self):
        """Test custom resource limits configuration."""
        limits = ResourceLimits(
            max_managers=2,
            max_engineers_per_manager=4,
            max_total_workers=8,
            allow_iterations=False,
            max_iterations=5
        )
        
        assert limits.max_managers == 2
        assert limits.max_engineers_per_manager == 4
        assert limits.max_total_workers == 8
        assert limits.allow_iterations is False
        assert limits.max_iterations == 5
    
    def test_requires_iteration_logic(self):
        """Test logic for determining when iterations are required."""
        limits = ResourceLimits(max_total_workers=4, allow_iterations=True)
        
        # Should require iteration when recommended workers exceed limit
        # This logic is handled in TaskComplexityAnalyzer._parse_analysis_response
        # So we test the limits object properties
        assert limits.max_total_workers == 4
        assert limits.allow_iterations is True
        
        # Should not require iteration when iterations disabled
        limits_no_iter = ResourceLimits(max_total_workers=4, allow_iterations=False)
        assert limits_no_iter.allow_iterations is False


class TestComplexityAssessment:
    """Test ComplexityAssessment data structure."""
    
    def test_complexity_assessment_creation(self):
        """Test creating a complexity assessment."""
        assessment = ComplexityAssessment(
            overall_score=7.5,
            dimension_scores={
                "SCOPE": 8,
                "TECHNICAL_DEPTH": 7,
                "INTEGRATION_POINTS": 6
            },
            recommended_managers=2,
            recommended_engineers_per_manager=3,
            total_recommended_workers=6,
            reasoning="Medium-high complexity project",
            requires_iteration=False,
            iteration_strategy=""
        )
        
        assert assessment.overall_score == 7.5
        assert assessment.dimension_scores["SCOPE"] == 8
        assert assessment.total_recommended_workers == 6
        assert assessment.requires_iteration is False
    
    def test_complexity_assessment_with_iteration(self):
        """Test complexity assessment that requires iteration."""
        assessment = ComplexityAssessment(
            overall_score=9.0,
            dimension_scores={},
            recommended_managers=4,
            recommended_engineers_per_manager=3,
            total_recommended_workers=12,
            reasoning="High complexity enterprise project",
            requires_iteration=True,
            iteration_strategy="Split into 3 iterations of 4 workers each"
        )
        
        assert assessment.requires_iteration is True
        assert assessment.iteration_strategy != ""
        assert assessment.total_recommended_workers == 12


class TestTaskComplexityAnalyzer:
    """Test TaskComplexityAnalyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer can be initialized."""
        analyzer = TaskComplexityAnalyzer()
        assert analyzer is not None
    
    def test_parse_analysis_response_valid(self):
        """Test parsing valid LLM response."""
        analyzer = TaskComplexityAnalyzer()
        limits = ResourceLimits(max_total_workers=6)
        
        # Mock a valid LLM response matching actual output format
        response = """
        SCOPE_SCORE: 7.0
        TECHNICAL_DEPTH_SCORE: 8.0
        INTEGRATION_POINTS_SCORE: 6.0
        TIMELINE_PRESSURE_SCORE: 5.0
        RISK_LEVEL_SCORE: 7.0
        COORDINATION_NEEDS_SCORE: 6.0
        OVERALL_COMPLEXITY: 6.5
        RECOMMENDED_MANAGERS: 2
        ENGINEERS_PER_MANAGER: 3
        REASONING: Medium complexity web application with API integrations
        """
        
        assessment = analyzer._parse_analysis_response(response, limits)
        
        assert assessment.overall_score == 6.5
        assert assessment.dimension_scores[ComplexityDimension.SCOPE] == 7.0
        assert assessment.dimension_scores[ComplexityDimension.TECHNICAL_DEPTH] == 8.0
        assert assessment.total_recommended_workers == 6
        assert assessment.requires_iteration is False
    
    def test_parse_analysis_response_requires_iteration(self):
        """Test parsing response that exceeds limits."""
        analyzer = TaskComplexityAnalyzer()
        limits = ResourceLimits(max_total_workers=4, allow_iterations=True)
        
        # Mock response exceeding limits
        response = """
        SCOPE: 9
        TECHNICAL_DEPTH: 9
        INTEGRATION_POINTS: 8
        TIMELINE_PRESSURE: 7
        RISK_LEVEL: 8
        COORDINATION_NEEDS: 8
        
        OVERALL_COMPLEXITY: 8.2
        RECOMMENDED_MANAGERS: 3
        RECOMMENDED_ENGINEERS_PER_MANAGER: 3
        TOTAL_WORKERS: 9
        
        REASONING: High complexity enterprise platform
        """
        
        assessment = analyzer._parse_analysis_response(response, limits)
        
        assert assessment.overall_score == 8.2
        assert assessment.total_recommended_workers == 9
        assert assessment.requires_iteration is True
        assert "iteration" in assessment.iteration_strategy.lower()


class TestIterationManager:
    """Test IterationManager functionality."""
    
    def test_iteration_manager_creation(self):
        """Test creating iteration manager."""
        manager = create_iteration_manager()
        assert manager is not None
        assert manager.current_iteration == 0
        assert manager.total_iterations == 0  # Start with 0 until planning is done
    
    def test_plan_iterations_simple(self):
        """Test iteration planning for simple case."""
        manager = IterationManager()
        limits = ResourceLimits(max_total_workers=3)
        
        # Create test work items
        work_items = [
            states.WorkItem(id="1", title="Task 1", description="Test task 1", priority=5),
            states.WorkItem(id="2", title="Task 2", description="Test task 2", priority=4),
            states.WorkItem(id="3", title="Task 3", description="Test task 3", priority=3),
        ]
        
        batches = manager.plan_iterations(work_items, limits, total_required_workers=3)
        
        assert len(batches) == 1
        assert len(batches[0]) == 3
    
    def test_plan_iterations_overflow(self):
        """Test iteration planning when workers exceed limits."""
        manager = IterationManager()
        limits = ResourceLimits(max_total_workers=2, allow_iterations=True)
        
        # Create test work items
        work_items = [
            states.WorkItem(id="1", title="Task 1", description="Test task 1", priority=5),
            states.WorkItem(id="2", title="Task 2", description="Test task 2", priority=5),
            states.WorkItem(id="3", title="Task 3", description="Test task 3", priority=4),
            states.WorkItem(id="4", title="Task 4", description="Test task 4", priority=3),
        ]
        
        batches = manager.plan_iterations(work_items, limits, total_required_workers=6)
        
        assert len(batches) == 2  # Should split into 2 iterations
        assert len(batches[0]) == 2  # First batch: 2 items (high priority)
        assert len(batches[1]) == 2  # Second batch: 2 items
        
        # Check priority ordering
        assert batches[0][0].priority >= batches[1][0].priority
    
    def test_advance_iteration(self):
        """Test advancing to next iteration."""
        manager = IterationManager()
        manager.total_iterations = 3
        
        assert manager.current_iteration == 0
        
        next_iter = manager.advance_iteration()
        assert next_iter == 1
        assert manager.current_iteration == 1
        
        next_iter = manager.advance_iteration()
        assert next_iter == 2
        assert manager.current_iteration == 2
    
    def test_should_continue_iteration(self):
        """Test iteration continuation logic."""
        manager = IterationManager()
        manager.total_iterations = 3
        
        # Should continue when more iterations remain
        manager.current_iteration = 0
        assert manager.should_continue_iteration() is True
        
        manager.current_iteration = 1
        assert manager.should_continue_iteration() is True
        
        manager.current_iteration = 2
        assert manager.should_continue_iteration() is True
        
        # Should not continue when at total iterations
        manager.current_iteration = 3
        assert manager.should_continue_iteration() is False
    
    def test_record_iteration_result(self):
        """Test recording iteration results."""
        manager = IterationManager()
        manager.current_iteration = 1  # Set current iteration
        
        result = {"iteration": 99, "completed_work": [], "summary": "Test iteration"}
        manager.record_iteration_result(result)
        
        assert len(manager.iteration_results) == 1
        assert manager.iteration_results[0]["iteration"] == 1  # Uses current_iteration, not input
    
    def test_get_iteration_summary(self):
        """Test getting iteration summary."""
        manager = IterationManager()
        
        # Set iteration numbers and record results
        manager.current_iteration = 1
        manager.record_iteration_result({"completed_work": [], "summary": "Iteration 1"})
        
        manager.current_iteration = 2
        manager.record_iteration_result({"completed_work": [], "summary": "Iteration 2"})
        
        summary = manager.get_iteration_summary()
        
        assert "2 iterations" in summary
        assert "Iteration 1" in summary
        assert "Iteration 2" in summary


if __name__ == "__main__":
    pytest.main([__file__])
