# Human-in-the-Loop Repository Selection

## Overview

The development team system now includes comprehensive human-in-the-loop functionality for repository selection before any development work begins. This ensures that agents always work in the correct repository and follow proper development workflows.

## Key Features

- **Pre-Development Consultation**: Always asks human for repository choice before coding
- **Multi-Repository Support**: Can work across existing repositories or create new ones
- **Branch Protection**: Agents never work directly on master branch
- **Pull Request Workflow**: All changes go through human review via pull requests
- **Validation**: Validates repository access and format before proceeding

## Available Tools

### 1. `initiate_project_workflow`
**Purpose**: The entry point for all new development work.

**Usage**:
```python
initiate_project_workflow(
    project_description="Build a web scraping tool for e-commerce sites",
    suggested_repo_name="web-scraper-v2"  # Optional
)
```

**Output**: Complete workflow guidance including repository options.

### 2. `request_repository_selection`
**Purpose**: Direct request for human repository choice.

**Usage**:
```python
request_repository_selection(
    project_description="AI assistant integration",
    suggested_name="ai-assistant-tool"  # Optional
)
```

**Output**: Formatted request for human to choose repository.

### 3. `list_available_repositories`
**Purpose**: Help human see repository options.

**Usage**:
```python
list_available_repositories(
    include_private=True,  # Optional, default: True
    limit=20              # Optional, default: 20
)
```

**Output**: Guidance on finding and selecting repositories.

### 4. `process_repository_choice`
**Purpose**: Process human's repository selection and set up environment.

**Usage**:
```python
process_repository_choice(
    human_response="use-repo: LimbicNode42/my-project"
    # OR
    human_response="create-repo: new-awesome-project"
)
```

**Output**: Repository setup status and next steps.

## Workflow Examples

### Example 1: Starting New Development Work

```python
# Agent initiates workflow
result = initiate_project_workflow(
    "Build a machine learning pipeline for customer data analysis",
    "ml-customer-pipeline"
)

# Human sees options and responds
# Human: "create-repo: ml-customer-analytics"

# Agent processes choice
result = process_repository_choice("create-repo: ml-customer-analytics")

# System creates repository and sets up development environment
# Agents can now begin development work
```

### Example 2: Using Existing Repository

```python
# Agent asks for repository selection
result = request_repository_selection(
    "Add new API endpoints to existing service"
)

# Human responds
# Human: "use-repo: LimbicNode42/customer-api"

# Agent validates and sets up
result = process_repository_choice("use-repo: LimbicNode42/customer-api")

# Repository is validated and ready for development
```

## Human Response Format

### For Existing Repository
```
use-repo: owner/repository-name
```

**Examples**:
- `use-repo: LimbicNode42/web-app`
- `use-repo: mycompany/internal-tools`

### For New Repository
```
create-repo: repository-name
```

**Examples**:
- `create-repo: ai-assistant-v2`
- `create-repo: data-processing-pipeline`

## Development Workflow After Repository Selection

1. **Repository Setup**: System configures the chosen/created repository
2. **Branch Creation**: Agents create feature branches (never work on master)
3. **Development Work**: Agents implement features on their branches
4. **Pull Request Creation**: All changes submitted via pull requests
5. **Human Review**: Human reviews and approves/requests changes
6. **Merge**: Approved changes merged to master

## Security and Safety Features

### Branch Protection
- Agents never commit directly to master branch
- All work done on feature branches like `agent/feature-name`
- Master branch remains clean and stable

### Human Oversight
- All code changes require human review
- Pull requests provide clear change descriptions
- Human maintains final approval authority

### Repository Validation
- System validates repository access before proceeding
- Proper error handling for invalid repositories
- Clear error messages for troubleshooting

## Error Handling

### Common Scenarios

**Invalid Repository Format**:
```
❌ Invalid repository format. Please use 'owner/repository-name' format.
```

**Repository Not Found**:
```
❌ Could not access repository 'owner/repo'. Please verify the name and permissions.
```

**Invalid Repository Name for Creation**:
```
❌ Invalid repository name. Use lowercase letters, numbers, hyphens, and underscores only.
```

**Invalid Response Format**:
```
❌ Invalid response format. Please use:
- 'use-repo: owner/repository-name' for existing repository
- 'create-repo: repository-name' for new repository
```

## Integration with Existing GitHub Tools

The human-in-the-loop tools work seamlessly with the 19 existing GitHub tools:

- Repository choice sets the working repository
- All GitHub operations use the selected repository
- Multi-repository operations possible by specifying different repos
- Environment isolation ensures clean repository switching

## Best Practices

### For Development Teams
1. **Always start with `initiate_project_workflow`** for new development
2. **Provide clear project descriptions** to help with repository naming
3. **Use descriptive repository names** for better organization
4. **Review pull requests promptly** to maintain development velocity

### For Repository Management
1. **Use consistent naming conventions** for repositories
2. **Keep repository descriptions updated** 
3. **Maintain proper access permissions** for team members
4. **Archive unused repositories** to reduce clutter

## Testing

The human-in-the-loop functionality includes comprehensive test coverage:

- **18 unit tests** covering all tools and scenarios
- **Error handling tests** for various failure modes
- **Integration tests** with GitHub API mocking
- **Workflow validation tests** for complete processes

Run tests with:
```bash
pytest tests/unit_tests/test_human_in_loop_tools.py -v
```

## Future Enhancements

- **Repository Templates**: Pre-configured repository structures for common project types
- **Team Integration**: Support for team-based repository assignment
- **Automated Suggestions**: ML-based repository name suggestions
- **Workflow Analytics**: Tracking of repository usage patterns
