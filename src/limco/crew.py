from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from typing import List
import os

# Import custom tools
from limco.tools.custom_tool import CostCalculatorTool, TechStackAnalyzerTool, RiskAssessmentTool

# Helper function to get web search tools if available
def get_web_search_tools():
    """Returns web search tools if API keys are available"""
    tools = []
    try:
        if os.getenv('SERPER_API_KEY'):
            tools.extend([SerperDevTool(), ScrapeWebsiteTool()])
    except:
        pass
    return tools

# Helper function to get model names from environment
def get_claude_premium_model():
    """Get the premium Claude model for critical tasks"""
    return os.getenv('CLAUDE_PREMIUM_MODEL', 'claude-sonnet-4-20250514')

def get_claude_standard_model():
    """Get the standard Claude model for regular tasks"""
    return os.getenv('CLAUDE_STANDARD_MODEL', 'claude-3-7-sonnet-20250219')

def get_gemini_model():
    """Get the Gemini model for fast processing tasks"""
    return os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Limco():
    """
    Limco - Autonomous Software Development Company
    
    A comprehensive AI-driven software development crew consisting of:
    - Core Development Crew (8 agents)
    - Business Crew (2 agents)
    
    Phases:
    1. Goal Intake & Initial Planning
    2. Technical Planning & Estimation  
    3. Business Analysis & Cost Planning
    4. Quality & Operations Planning
    5. Implementation Coordination
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # =============================================================================
    # CORE DEVELOPMENT CREW AGENTS
    # =============================================================================
    
    @agent
    def overseer_cto(self) -> Agent:
        """Chief Technology Officer and Strategic Overseer - Uses Claude Premium for critical executive analysis"""
        return Agent(
            config=self.agents_config['overseer_cto'],
            tools=get_web_search_tools(),
            llm=get_claude_premium_model(),  # Critical: Executive decisions
            verbose=True
        )

    @agent
    def engineering_manager(self) -> Agent:
        """Engineering Manager and Resource Coordinator - Uses Gemini for fast timeline processing"""
        return Agent(
            config=self.agents_config['engineering_manager'],
            tools=[RiskAssessmentTool()],
            llm=get_gemini_model(),  # Fast: Resource planning
            verbose=True
        )

    @agent
    def product_manager(self) -> Agent:
        """Product Manager and Requirements Architect - Uses Claude Standard for detailed requirements"""
        return Agent(
            config=self.agents_config['product_manager'],
            tools=get_web_search_tools(),
            llm=get_claude_standard_model(),  # Standard: Requirements documentation
            verbose=True
        )

    @agent
    def staff_engineer(self) -> Agent:
        """Staff Engineer and Technical Architect - Uses Claude Premium for critical architecture decisions"""
        return Agent(
            config=self.agents_config['staff_engineer'],
            tools=[TechStackAnalyzerTool(), RiskAssessmentTool()],
            llm=get_claude_premium_model(),  # Critical: Technical architecture
            verbose=True
        )

    @agent
    def senior_engineer_backend(self) -> Agent:
        """Senior Backend Engineer and API Specialist - Uses Claude Premium for complex programming decisions"""
        return Agent(
            config=self.agents_config['senior_engineer_backend'],
            tools=[TechStackAnalyzerTool()],
            llm=get_claude_premium_model(),  # Critical: Complex programming
            verbose=True
        )

    @agent
    def senior_engineer_frontend(self) -> Agent:
        """Senior Frontend Engineer and UX Specialist - Uses Claude Premium for complex programming decisions"""
        return Agent(
            config=self.agents_config['senior_engineer_frontend'],
            tools=[TechStackAnalyzerTool()],
            llm=get_claude_premium_model(),  # Critical: Complex programming
            verbose=True
        )

    @agent
    def devops_engineer(self) -> Agent:
        """DevOps Engineer and Infrastructure Specialist - Uses Gemini for fast configuration management"""
        return Agent(
            config=self.agents_config['devops_engineer'],
            tools=[CostCalculatorTool(), TechStackAnalyzerTool()],
            llm=get_gemini_model(),  # Fast: Infrastructure automation
            verbose=True
        )

    @agent
    def qa_engineer(self) -> Agent:
        """Quality Assurance Engineer and Testing Strategist - Uses Claude Standard for systematic testing plans"""
        return Agent(
            config=self.agents_config['qa_engineer'],
            tools=[RiskAssessmentTool()],
            llm=get_claude_standard_model(),  # Standard: Testing methodology
            verbose=True
        )

    # =============================================================================
    # BUSINESS CREW AGENTS
    # =============================================================================

    @agent
    def token_economics_agent(self) -> Agent:
        """Token Economics Analyst and Cost Optimization Specialist - Uses Claude Premium for precise financial analysis"""
        return Agent(
            config=self.agents_config['token_economics_agent'],
            tools=[CostCalculatorTool()],
            llm=get_claude_premium_model(),  # Critical: Financial precision
            verbose=True
        )

    @agent
    def business_development_agent(self) -> Agent:
        """Business Development Strategist and Market Analyst - Uses Gemini for fast market research"""
        return Agent(
            config=self.agents_config['business_development_agent'],
            tools=get_web_search_tools(),
            llm=get_gemini_model(),  # Fast: Market analysis
            verbose=True
        )

    # =============================================================================
    # PHASE 1: GOAL INTAKE & INITIAL PLANNING TASKS
    # =============================================================================

    @task
    def ceo_goal_intake(self) -> Task:
        """Receive and analyze CEO goals, create strategic direction"""
        return Task(
            config=self.tasks_config['ceo_goal_intake'],
            agent=self.overseer_cto()
        )

    @task
    def product_requirements_definition(self) -> Task:
        """Break down goals into detailed product requirements"""
        return Task(
            config=self.tasks_config['product_requirements_definition'],
            agent=self.product_manager()
        )

    # =============================================================================
    # PHASE 2: TECHNICAL PLANNING & ESTIMATION TASKS
    # =============================================================================

    @task
    def technical_architecture_design(self) -> Task:
        """Design technical architecture and implementation approach"""
        return Task(
            config=self.tasks_config['technical_architecture_design'],
            agent=self.staff_engineer()
        )

    @task
    def resource_planning_and_estimation(self) -> Task:
        """Create project timeline and resource allocation"""
        return Task(
            config=self.tasks_config['resource_planning_and_estimation'],
            agent=self.engineering_manager()
        )

    # =============================================================================
    # PHASE 3: BUSINESS ANALYSIS & COST PLANNING TASKS
    # =============================================================================

    @task
    def cost_analysis_and_roi_projection(self) -> Task:
        """Calculate costs and ROI projections"""
        return Task(
            config=self.tasks_config['cost_analysis_and_roi_projection'],
            agent=self.token_economics_agent()
        )

    @task
    def market_validation_and_revenue_strategy(self) -> Task:
        """Analyze market opportunity and develop revenue strategy"""
        return Task(
            config=self.tasks_config['market_validation_and_revenue_strategy'],
            agent=self.business_development_agent()
        )

    # =============================================================================
    # PHASE 4: QUALITY & OPERATIONS PLANNING TASKS
    # =============================================================================

    @task
    def infrastructure_and_deployment_planning(self) -> Task:
        """Design infrastructure and deployment strategy"""
        return Task(
            config=self.tasks_config['infrastructure_and_deployment_planning'],
            agent=self.devops_engineer()
        )

    @task
    def quality_assurance_strategy(self) -> Task:
        """Define testing strategy and quality assurance"""
        return Task(
            config=self.tasks_config['quality_assurance_strategy'],
            agent=self.qa_engineer()
        )

    # =============================================================================
    # PHASE 5: IMPLEMENTATION COORDINATION TASKS
    # =============================================================================

    @task
    def backend_implementation_planning(self) -> Task:
        """Create backend implementation plan"""
        return Task(
            config=self.tasks_config['backend_implementation_planning'],
            agent=self.senior_engineer_backend()
        )

    @task
    def frontend_implementation_planning(self) -> Task:
        """Create frontend implementation plan"""
        return Task(
            config=self.tasks_config['frontend_implementation_planning'],
            agent=self.senior_engineer_frontend()
        )

    # =============================================================================
    # EXECUTIVE SUMMARY TASK
    # =============================================================================

    @task
    def executive_summary_and_recommendations(self) -> Task:
        """Consolidate all inputs into executive summary for CEO approval"""
        return Task(
            config=self.tasks_config['executive_summary_and_recommendations'],
            agent=self.overseer_cto(),
            output_file='executive_summary.md'
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates the Limco autonomous software development crew
        
        This crew implements a comprehensive 5-phase development process:
        1. Goal Intake & Initial Planning
        2. Technical Planning & Estimation
        3. Business Analysis & Cost Planning  
        4. Quality & Operations Planning
        5. Implementation Coordination
        
        The process culminates in an executive summary with recommendations
        for CEO approval before autonomous execution begins.
        """
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # Note: Could use Process.hierarchical with overseer_cto as manager
            # process=Process.hierarchical,
            # manager_agent=self.overseer_cto(),
        )
