from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json
import yaml


class CostCalculatorInput(BaseModel):
    """Input schema for cost calculation tool."""
    project_timeline_months: float = Field(..., description="Project timeline in months")
    team_size: int = Field(..., description="Number of team members")
    complexity_factor: float = Field(default=1.0, description="Complexity multiplier (0.5-2.0)")
    ai_model_usage_hours: float = Field(default=100, description="Expected AI model usage hours")
    infrastructure_tier: str = Field(default="basic", description="Infrastructure tier: basic, standard, premium")


class CostCalculatorTool(BaseTool):
    name: str = "cost_calculator"
    description: str = (
        "Calculate comprehensive development costs including team costs, "
        "AI model usage, infrastructure costs, and ROI projections."
    )
    args_schema: Type[BaseModel] = CostCalculatorInput

    def _run(self, **kwargs) -> str:
        """Calculate project costs based on input parameters."""
        
        # Extract inputs
        timeline_months = kwargs.get('project_timeline_months', 3)
        team_size = kwargs.get('team_size', 5)
        complexity_factor = kwargs.get('complexity_factor', 1.0)
        ai_usage_hours = kwargs.get('ai_model_usage_hours', 100)
        infra_tier = kwargs.get('infrastructure_tier', 'basic')
        
        # Cost calculations
        monthly_team_cost = team_size * 8000  # $8k per person per month average
        total_team_cost = monthly_team_cost * timeline_months * complexity_factor
        
        # AI model costs (approximate)
        ai_cost_per_hour = 25  # $25/hour for high-end models
        total_ai_cost = ai_usage_hours * ai_cost_per_hour
        
        # Infrastructure costs
        infra_costs = {
            'basic': 500,
            'standard': 1500,
            'premium': 3000
        }
        monthly_infra_cost = infra_costs.get(infra_tier, 500)
        total_infra_cost = monthly_infra_cost * timeline_months
        
        # Calculate totals
        total_cost = total_team_cost + total_ai_cost + total_infra_cost
        
        # Create detailed breakdown
        cost_breakdown = {
            "project_timeline_months": timeline_months,
            "team_size": team_size,
            "complexity_factor": complexity_factor,
            "cost_breakdown": {
                "team_costs": {
                    "monthly_cost": monthly_team_cost,
                    "total_cost": total_team_cost,
                    "percentage": round((total_team_cost / total_cost) * 100, 1)
                },
                "ai_model_costs": {
                    "hourly_rate": ai_cost_per_hour,
                    "total_hours": ai_usage_hours,
                    "total_cost": total_ai_cost,
                    "percentage": round((total_ai_cost / total_cost) * 100, 1)
                },
                "infrastructure_costs": {
                    "tier": infra_tier,
                    "monthly_cost": monthly_infra_cost,
                    "total_cost": total_infra_cost,
                    "percentage": round((total_infra_cost / total_cost) * 100, 1)
                }
            },
            "total_project_cost": total_cost,
            "cost_per_month": round(total_cost / timeline_months, 2),
            "roi_scenarios": {
                "conservative": {
                    "monthly_revenue": total_cost * 0.15,
                    "break_even_months": round(total_cost / (total_cost * 0.15), 1),
                    "annual_roi": "80%"
                },
                "moderate": {
                    "monthly_revenue": total_cost * 0.25,
                    "break_even_months": round(total_cost / (total_cost * 0.25), 1),
                    "annual_roi": "200%"
                },
                "optimistic": {
                    "monthly_revenue": total_cost * 0.4,
                    "break_even_months": round(total_cost / (total_cost * 0.4), 1),
                    "annual_roi": "380%"
                }
            }
        }
        
        return json.dumps(cost_breakdown, indent=2)


class TechStackAnalysisInput(BaseModel):
    """Input schema for technology stack analysis tool."""
    project_type: str = Field(..., description="Type of project: web_app, mobile_app, api, desktop, etc.")
    target_platforms: List[str] = Field(..., description="Target platforms: web, ios, android, windows, mac, linux")
    expected_users: int = Field(default=1000, description="Expected number of users")
    performance_requirements: str = Field(default="standard", description="Performance level: basic, standard, high")
    team_expertise: List[str] = Field(default=[], description="Team's existing expertise areas")


class TechStackAnalyzerTool(BaseTool):
    name: str = "tech_stack_analyzer"
    description: str = (
        "Analyze project requirements and recommend optimal technology stack "
        "based on project type, scale, and team capabilities."
    )
    args_schema: Type[BaseModel] = TechStackAnalysisInput

    def _run(self, **kwargs) -> str:
        """Analyze requirements and recommend tech stack."""
        
        project_type = kwargs.get('project_type', 'web_app')
        platforms = kwargs.get('target_platforms', ['web'])
        users = kwargs.get('expected_users', 1000)
        performance = kwargs.get('performance_requirements', 'standard')
        expertise = kwargs.get('team_expertise', [])
        
        # Tech stack recommendations based on project type
        recommendations = {
            "web_app": {
                "frontend": {
                    "frameworks": ["React", "Vue.js", "Next.js"],
                    "styling": ["Tailwind CSS", "Styled Components"],
                    "state_management": ["Redux Toolkit", "Zustand"]
                },
                "backend": {
                    "frameworks": ["Node.js/Express", "Python/FastAPI", "Go/Gin"],
                    "databases": ["PostgreSQL", "MongoDB", "Redis (cache)"],
                    "apis": ["REST", "GraphQL"]
                },
                "infrastructure": {
                    "hosting": ["Vercel", "AWS", "Google Cloud"],
                    "cdn": ["Cloudflare", "AWS CloudFront"],
                    "monitoring": ["Sentry", "DataDog"]
                }
            },
            "mobile_app": {
                "frameworks": ["React Native", "Flutter", "Native"],
                "backend": ["Node.js", "Python", "Firebase"],
                "databases": ["Firebase", "PostgreSQL", "SQLite"],
                "services": ["Push notifications", "Analytics", "Crash reporting"]
            },
            "api": {
                "frameworks": ["FastAPI", "Express.js", "Go Gin", "Spring Boot"],
                "databases": ["PostgreSQL", "MongoDB", "Redis"],
                "tools": ["Swagger/OpenAPI", "Postman", "API Gateway"],
                "monitoring": ["New Relic", "DataDog", "Prometheus"]
            }
        }
        
        # Scale considerations
        scale_factors = {
            "small": {"max_users": 10000, "complexity": "low"},
            "medium": {"max_users": 100000, "complexity": "medium"},
            "large": {"max_users": 1000000, "complexity": "high"}
        }
        
        scale = "small" if users < 10000 else "medium" if users < 100000 else "large"
        
        # Performance considerations
        perf_recommendations = {
            "basic": {"caching": "Basic", "cdn": "Optional", "optimization": "Standard"},
            "standard": {"caching": "Redis", "cdn": "Recommended", "optimization": "Enhanced"},
            "high": {"caching": "Multi-layer", "cdn": "Required", "optimization": "Advanced"}
        }
        
        analysis = {
            "project_analysis": {
                "type": project_type,
                "platforms": platforms,
                "expected_scale": scale,
                "performance_tier": performance,
                "estimated_users": users
            },
            "recommended_stack": recommendations.get(project_type, recommendations["web_app"]),
            "scaling_considerations": {
                "current_tier": scale,
                "scaling_strategy": scale_factors[scale],
                "performance_optimizations": perf_recommendations[performance]
            },
            "team_alignment": {
                "existing_expertise": expertise,
                "recommended_training": [],
                "skill_gaps": []
            },
            "deployment_strategy": {
                "development": "Local + Staging environments",
                "testing": "Automated CI/CD pipeline",
                "production": "Blue-green deployment",
                "monitoring": "Full observability stack"
            },
            "cost_estimates": {
                "development_tools": "$500-2000/month",
                "infrastructure": f"${100 if scale == 'small' else 500 if scale == 'medium' else 2000}/month",
                "third_party_services": "$200-1000/month"
            }
        }
        
        return json.dumps(analysis, indent=2)


class RiskAssessmentInput(BaseModel):
    """Input schema for risk assessment tool."""
    project_complexity: str = Field(..., description="Project complexity: low, medium, high, very_high")
    timeline_months: float = Field(..., description="Project timeline in months")
    team_experience: str = Field(..., description="Team experience level: junior, mixed, senior, expert")
    technology_maturity: str = Field(..., description="Technology maturity: experimental, emerging, stable, mature")
    external_dependencies: int = Field(default=0, description="Number of external dependencies/integrations")


class RiskAssessmentTool(BaseTool):
    name: str = "risk_assessor"
    description: str = (
        "Assess project risks including technical, timeline, team, and business risks "
        "with mitigation strategies and probability assessments."
    )
    args_schema: Type[BaseModel] = RiskAssessmentInput

    def _run(self, **kwargs) -> str:
        """Assess project risks and provide mitigation strategies."""
        
        complexity = kwargs.get('project_complexity', 'medium')
        timeline = kwargs.get('timeline_months', 3)
        team_exp = kwargs.get('team_experience', 'mixed')
        tech_maturity = kwargs.get('technology_maturity', 'stable')
        ext_deps = kwargs.get('external_dependencies', 0)
        
        # Risk scoring (1-10 scale)
        risk_factors = {
            "technical_complexity": {
                "low": 2, "medium": 5, "high": 7, "very_high": 9
            }.get(complexity, 5),
            "timeline_pressure": min(9, max(1, 10 - timeline * 2)),
            "team_capability": {
                "expert": 2, "senior": 3, "mixed": 5, "junior": 8
            }.get(team_exp, 5),
            "technology_risk": {
                "mature": 2, "stable": 3, "emerging": 6, "experimental": 8
            }.get(tech_maturity, 3),
            "integration_complexity": min(9, ext_deps * 2)
        }
        
        # Calculate overall risk score
        overall_risk = sum(risk_factors.values()) / len(risk_factors)
        risk_level = "Low" if overall_risk < 3 else "Medium" if overall_risk < 6 else "High"
        
        # Risk assessment with mitigation strategies
        risk_assessment = {
            "overall_assessment": {
                "risk_score": round(overall_risk, 1),
                "risk_level": risk_level,
                "confidence": "High" if overall_risk < 3 or overall_risk > 7 else "Medium"
            },
            "risk_breakdown": {
                "technical_complexity": {
                    "score": risk_factors["technical_complexity"],
                    "impact": "High",
                    "probability": "Medium" if complexity in ["medium", "high"] else "Low",
                    "mitigation": [
                        "Conduct proof-of-concept for complex features",
                        "Break down complex features into smaller components",
                        "Regular architecture reviews",
                        "Pair programming for complex implementations"
                    ]
                },
                "timeline_pressure": {
                    "score": risk_factors["timeline_pressure"],
                    "impact": "High",
                    "probability": "High" if timeline < 2 else "Medium",
                    "mitigation": [
                        "Implement MVP-first approach",
                        "Regular sprint reviews and adjustments",
                        "Buffer time for unexpected issues",
                        "Clear scope definition and change management"
                    ]
                },
                "team_capability": {
                    "score": risk_factors["team_capability"],
                    "impact": "Medium",
                    "probability": "Medium" if team_exp in ["mixed", "junior"] else "Low",
                    "mitigation": [
                        "Provide targeted training for skill gaps",
                        "Pair senior developers with junior team members",
                        "Code review processes",
                        "Knowledge sharing sessions"
                    ]
                },
                "technology_risk": {
                    "score": risk_factors["technology_risk"],
                    "impact": "Medium",
                    "probability": "High" if tech_maturity in ["experimental", "emerging"] else "Low",
                    "mitigation": [
                        "Prototype with new technologies early",
                        "Have fallback technology options",
                        "Community support assessment",
                        "Regular technology evaluation"
                    ]
                },
                "integration_complexity": {
                    "score": risk_factors["integration_complexity"],
                    "impact": "High",
                    "probability": "High" if ext_deps > 3 else "Medium",
                    "mitigation": [
                        "Early integration testing",
                        "Mock external services for development",
                        "Comprehensive error handling",
                        "Fallback options for critical integrations"
                    ]
                }
            },
            "recommended_actions": [
                "Weekly risk assessment reviews",
                "Maintain risk register throughout project",
                "Implement early warning systems",
                "Regular stakeholder communication on risks",
                "Continuous monitoring of risk indicators"
            ],
            "success_probability": f"{max(10, 100 - overall_risk * 10)}%"
        }
        
        return json.dumps(risk_assessment, indent=2)
