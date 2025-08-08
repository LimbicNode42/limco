# Limco - Autonomous Software Development Company

**Version**: 1.0  
**Created**: 2025-08-06  
**Author**: LimbicNode42  

An AI-powered autonomous software development company built with CrewAI that can take high-level business goals and autonomously plan, analyze, and provide comprehensive project proposals.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- API Keys for AI services (OpenAI, Anthropic, or Google)
- Optional: Serper API key for web search

### Installation
```bash
cd limco
pip install -e .
```

### Setup Environment
Create a `.env` file:
```bash
# Required: Choose one AI provider
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here  
# OR
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Web search for market research
SERPER_API_KEY=your_serper_api_key_here
```

### First Run
```bash
# Test the system (uses faster rate limiting)
python -m limco.main test

# Test with conservative rate limiting (safer)
python -m limco.main test-safe

# Run with example project (conservative rate limiting)
python -m limco.main run

# Run with aggressive rate limiting (faster but may hit limits)
python -m limco.main run-fast

# Run with your own goal
python -m limco.main run "Your project description here..."
```

## 🛡️ Rate Limiting & API Management

Limco includes intelligent rate limiting to prevent API quota exhaustion and handle rate limits gracefully.

### Rate Limiting Modes

**Conservative Mode (Default - Recommended)**
- 5 second delays between operations
- Up to 8 retry attempts with exponential backoff
- Maximum 5 minute retry delays
- Best for: Standard API accounts, production use

**Aggressive Mode (For Premium Users)**
- 3 second delays between operations  
- Up to 6 retry attempts with exponential backoff
- Maximum 2 minute retry delays
- Best for: Premium API accounts, testing

### Commands with Rate Limiting

```bash
# Conservative (safer, slower)
python -m limco.main run               # Default mode
python -m limco.main test-safe         # Conservative testing

# Aggressive (faster, may hit limits)  
python -m limco.main run-fast          # Aggressive mode
python -m limco.main test              # Aggressive testing
```

### Handling Rate Limits

If you encounter rate limit errors:
1. **Wait and retry** - Rate limits usually reset after a few minutes
2. **Use conservative mode** - `python -m limco.main run` (default)
3. **Check API quotas** - Ensure you have sufficient API credits
4. **Customize settings** - Edit `rate_limiting.conf` for your needs

## 🏗️ What You Get

### 10 Specialized AI Agents
**Core Development Crew (8 agents):**
- **CTO/Overseer** - Strategic technical leadership
- **Engineering Manager** - Resource planning and timelines  
- **Product Manager** - Requirements and scope definition
- **Staff Engineer** - Technical architecture design
- **Senior Backend Engineer** - Backend/API implementation
- **Senior Frontend Engineer** - Frontend/UX implementation
- **DevOps Engineer** - Infrastructure and deployment
- **QA Engineer** - Quality strategy and testing

**Business Crew (2 agents):**
- **Token Economics Agent** - Cost analysis and ROI
- **Business Development Agent** - Revenue strategy and market validation

### 5-Phase Autonomous Process
1. **Goal Intake** - Strategic analysis and direction
2. **Technical Planning** - Architecture and resource estimation
3. **Business Analysis** - Cost analysis and revenue strategy
4. **Quality Planning** - Infrastructure and testing strategy
5. **Implementation Coordination** - Detailed implementation plans

## 🎯 Team Structure

## Detailed Role Definitions

### Phase 1: Goal Intake & Initial Planning

#### **Overseer/CTO Agent**
**Role**: Strategic Technical Leadership & CEO Interface

**Responsibilities**:
- Receives high-level goals from CEO (LimbicNode42)
- Translates business objectives into technical strategy
- Coordinates all crews and ensures alignment
- Primary point of contact for CEO communications
- Makes final technical architecture decisions
- Consolidates team inputs into executive summaries

**Reports to**: CEO (LimbicNode42)  
**Manages**: All technical crews  
**Key Deliverables**: Strategic direction, executive summaries, final recommendations

#### **Product Manager Agent**
**Role**: Requirements & Scope Definition

**Responsibilities**:
- Breaks down CEO goals into user stories and requirements
- Defines success metrics and acceptance criteria
- Conducts market research and competitive analysis
- Prioritizes features based on business value
- Creates detailed product requirements documents

**Collaborates with**: Business Development Agent for market insights  
**Key Deliverables**: Product requirements document, user stories, success metrics

### Phase 2: Technical Planning & Estimation

#### **Engineering Manager Agent**
**Role**: Resource Planning & Timeline Estimation

**Responsibilities**:
- Estimates effort and timeline for all technical work
- Assigns tasks across engineering team based on skills/capacity
- Identifies risks and dependencies
- Creates sprint plans and milestone schedules
- Coordinates team resources and manages capacity

**Collaborates with**: Staff Engineer for technical complexity assessment  
**Key Deliverables**: Project timeline, resource allocation, risk assessment, sprint plans

#### **Staff Engineer Agent**
**Role**: Technical Architecture & Design

**Responsibilities**:
- Designs system architecture and technical approach
- Identifies technical risks and complexity factors
- Provides accurate effort estimates for complex features
- Defines technical standards and best practices
- Mentors senior engineers on complex implementations

**Collaborates with**: DevOps Engineer for infrastructure planning  
**Key Deliverables**: Technical architecture document, implementation plan, technical standards

### Phase 3: Business Analysis & Cost Planning

#### **Token Economics Agent**
**Role**: Cost Analysis & ROI Optimization

**Responsibilities**:
- Calculates development costs (token usage, compute resources)
- Projects ROI based on timeline and resource requirements
- Identifies cost optimization opportunities
- Monitors real-time spending during execution
- Suggests model optimizations and prompt improvements
- Tracks budget vs actual spending

**Collaborates with**: Engineering Manager for resource estimates  
**Key Deliverables**: Cost analysis, budget recommendations, ROI projections, cost monitoring reports

#### **Business Development Agent**
**Role**: Revenue Strategy & Market Validation

**Responsibilities**:
- Analyzes revenue potential of proposed features/products
- Identifies potential customers, partners, or monetization strategies
- Validates market demand and competitive positioning
- Develops go-to-market strategy
- Identifies partnership and licensing opportunities

**Collaborates with**: Product Manager for market requirements  
**Key Deliverables**: Revenue projections, market analysis, business case, go-to-market strategy

### Phase 4: Quality & Operations Planning

#### **DevOps Engineer Agent**
**Role**: Infrastructure & Deployment Planning

**Responsibilities**:
- Plans infrastructure requirements and scaling needs
- Designs CI/CD pipelines and deployment strategy
- Estimates infrastructure costs and operational overhead
- Identifies security and compliance requirements
- Manages deployment automation and monitoring

**Collaborates with**: Staff Engineer for system requirements  
**Key Deliverables**: Infrastructure plan, deployment strategy, operational costs, CI/CD setup

#### **QA Engineer Agent**
**Role**: Quality Strategy & Testing Planning

**Responsibilities**:
- Defines testing strategy and quality gates
- Estimates testing effort and timeline
- Identifies potential quality risks
- Plans automation and manual testing approaches
- Ensures code quality and performance standards

**Collaborates with**: Engineering Manager for timeline integration  
**Key Deliverables**: Testing strategy, quality metrics, testing timeline, test automation plans

### Phase 5: Implementation Team

#### **Senior Engineer Agent #1**
**Role**: Lead Feature Development (Backend/API Focus)

**Responsibilities**:
- Implements core features and complex functionality
- Mentors junior developers and reviews code
- Ensures technical standards are maintained
- Coordinates with other engineers on integrations
- Focuses on backend systems, APIs, and data architecture

**Reports to**: Engineering Manager  
**Specialization**: Backend/API development, database design, system integrations

#### **Senior Engineer Agent #2**
**Role**: Frontend & User Experience Development

**Responsibilities**:
- Implements user interfaces and user experience
- Ensures responsive design and accessibility
- Optimizes frontend performance
- Coordinates with Product Manager on UX decisions
- Maintains design system and UI components

**Reports to**: Engineering Manager  
**Specialization**: Frontend/UI development, user experience, design systems

## 🔧 API Setup Options

### Option 1: OpenAI (Recommended)
**Cost**: ~$2-5 per project analysis | **Quality**: Excellent
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4
```

### Option 2: Anthropic Claude (Great for Analysis)
**Cost**: ~$0.50-1.50 per analysis | **Quality**: Excellent for detailed docs
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MODEL_NAME=claude-3-sonnet-20240229
```

### Option 3: Google Gemini (Most Affordable)
**Cost**: ~$0.10-0.30 per analysis | **Quality**: Good
```bash
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-pro
```

### Option 4: Mixed Models (Optimized)
Use different models for different agents based on their strengths:
```bash
# Premium for critical programming decisions
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Fast planning and management
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Web search for market research
SERPER_API_KEY=your_serper_api_key_here
```

## 📝 Example Usage

See `examples/example_goals.md` for detailed project examples including:
- SaaS CRM Platform ($50k budget, 3-month timeline)
- AI-Powered Task Management ($75k budget, 4-month timeline) 
- E-commerce Analytics Platform ($100k budget, 6-month timeline)
- Educational Content Platform ($80k budget, 7-month timeline)
- Healthcare Practice Management ($120k budget, 10-month timeline)

## 🎯 Expected Outputs

Each project analysis provides:
1. **Strategic Planning Document** - Technical strategy and approach
2. **Product Requirements Document** - Detailed user stories and acceptance criteria
3. **Technical Architecture Document** - System design and implementation plan
4. **Project Management Plan** - Timeline, resources, and risk assessment
5. **Financial Analysis Report** - Cost breakdown and ROI projections
6. **Business Case & GTM Strategy** - Market analysis and revenue strategy
7. **Infrastructure Plan** - DevOps and deployment strategy
8. **Quality Assurance Strategy** - Testing approach and quality gates
9. **Backend Implementation Plan** - API and database design
10. **Frontend Implementation Plan** - UI/UX and responsive design
11. **Executive Summary** - Consolidated recommendations and next steps

## 🚀 What Makes Limco Special

- **Autonomous Planning**: Takes high-level goals and creates detailed execution plans
- **Multi-Model Optimization**: Uses the best AI model for each agent's strengths
- **Cost-Aware**: Includes detailed cost analysis and ROI projections
- **Business-Focused**: Combines technical planning with market analysis
- **Production-Ready**: Includes infrastructure, testing, and deployment planning