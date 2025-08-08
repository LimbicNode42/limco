# Limco Troubleshooting Guide

## Common Issues and Solutions

### 1. API Rate Limiting Errors

**Symptoms:**
- "Overloaded" errors (HTTP 529)
- "Rate limit" errors (HTTP 429)
- "Too many requests" messages

**Solutions:**
```bash
# Use conservative rate limiting (recommended)
python -m limco.main test-safe

# Wait longer between attempts
# Conservative mode: 5s delays, 8 retries
# Aggressive mode: 3s delays, 6 retries
```

**Configuration:**
Edit `rate_limiting.conf` to increase delays:
```ini
[conservative]
base_delay = 10.0    # Increase from 5.0 for stricter limits
max_retries = 12     # Increase retry count
```

### 2. "Invalid response from LLM call - None or empty"

**Causes:**
- API rate limiting (silent rejection)
- Context window exceeded
- Model temporarily unavailable
- Network connectivity issues

**Solutions:**
1. **Wait and Retry:**
   ```bash
   # Wait 10-15 minutes then try again
   python -m limco.main test-safe
   ```

2. **Check API Keys:**
   ```bash
   # Verify your .env file has valid keys
   cat .env | grep API_KEY
   ```

3. **Test Individual Components:**
   ```bash
   # Test simple functionality first
   python -c "import limco.crew; print('✅ Import successful')"
   ```

### 3. Pydantic Deprecation Warnings

**Solution:**
These are harmless warnings that can be ignored. They come from the CrewAI library dependencies.

### 4. AgentOps Warnings

**Solution:**
Add to your `.env` file:
```ini
AGENTOPS_API_KEY=disabled
AGENTOPS_ENABLED=false
```

### 5. Progress Monitoring

**Expected Test Duration:**
- Conservative mode: 8-12 minutes for complete test
- First task completion: 3-5 minutes (normal)
- Rate limiting delays: 5-second gaps between API calls

**Success Indicators:**
- ✅ "Task Completed" messages
- 🔧 "Used Search the internet with Serper" (tool usage)
- 🛡️ "Rate limiting enabled" (protection active)

### 6. Performance Optimization

**For Faster Testing:**
```bash
# Use aggressive mode (if you have premium API access)
python -m limco.main test

# For standard API accounts, stick with:
python -m limco.main test-safe
```

**For Production Use:**
```bash
# Full development planning (30-45 minutes)
python -m limco.main run "Your project description"

# Faster production mode
python -m limco.main run-fast "Your project description"
```

### 7. API Key Configuration

**Required Keys:**
```ini
# Required for all agents
ANTHROPIC_API_KEY=sk-ant-api03-...

# Required for planning agents  
GOOGLE_API_KEY=AIzaSy...

# Optional but recommended for research
SERPER_API_KEY=dc25c4...
```

**Testing API Keys:**
```bash
# Test Anthropic
curl -H "x-api-key: YOUR_KEY" https://api.anthropic.com/v1/messages

# Test Google
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"
```

### 8. Emergency Troubleshooting

**If Nothing Works:**
1. Check internet connectivity
2. Verify API key validity and billing status
3. Try a simpler test goal
4. Check for service outages at:
   - https://status.anthropic.com/
   - https://status.cloud.google.com/

**Simple Functionality Test:**
```python
# Test basic imports
python -c "
import limco.crew
from limco.utils.rate_limiter import RateLimiter
print('✅ All imports successful')
"
```

### 9. Expected Behavior

**Normal Test Flow:**
1. 🔧 Environment loading
2. 🐌 Rate limiting activation  
3. 🚀 Crew execution start
4. 🤖 Agent task execution (CTO first)
5. 🔧 Tool usage (web searches)
6. ✅ First task completion
7. 🤖 Second agent starts (Product Manager)
8. ... continues through all 10 agents

**Completion Time:**
- Single task: 3-8 minutes
- Full crew (test): 20-40 minutes
- Full crew (production): 45-90 minutes

## Support

If issues persist:
1. Check the full error output above the "Exception" line
2. Verify all API keys are valid and have sufficient quota
3. Try again during off-peak hours
4. Consider upgrading to premium API accounts for higher rate limits
