# Limco Quick Start Guide

Welcome to Limco - your autonomous software development company powered by AI agents!

## 🚀 5-Minute Setup

### 1. Install
```bash
cd limco
pip install -e .
```

### 2. Configure API Keys
Create `.env` file with your API keys:
```bash
# Choose one or more providers
OPENAI_API_KEY=your_key_here          # Recommended
ANTHROPIC_API_KEY=your_key_here       # Great for analysis
GOOGLE_API_KEY=your_key_here          # Most affordable

# Optional: Web search for market research
SERPER_API_KEY=your_key_here
```

### 3. Test & Run
```bash
# Quick test (uses faster rate limiting)
python -m limco.main test

# Run with example project (safe rate limiting)
python -m limco.main run

# Run with your goal
python -m limco.main run "Build a mobile app for..."

# For users with premium API accounts (faster)
python -m limco.main run-fast "Your project here..."
```

## 🛡️ Rate Limiting Explained

Limco automatically handles API rate limits to prevent quota exhaustion:

- **Default mode**: Conservative (3s delays, safer for all users)
- **Fast mode**: Aggressive (1.5s delays, for premium API accounts)
- **Smart retries**: Exponential backoff with up to 6 attempts
- **Error handling**: Graceful degradation when limits are hit

**If you get rate limit errors**: Use default mode and wait a few minutes before retrying.

## 🎯 What Happens Next

Your 10 AI agents will autonomously:
1. 📋 **Analyze** your business goal
2. 🏗️ **Design** technical architecture  
3. 💰 **Calculate** costs and ROI
4. 📈 **Research** market and competition
5. 🚀 **Plan** infrastructure and deployment
6. 🧪 **Strategy** quality assurance approach
7. ⚙️ **Detail** backend implementation
8. 🎨 **Design** frontend experience
9. 📊 **Summarize** everything for decision-making

## 📖 Need More Help?

- **Full Documentation**: See main `README.md`
- **Example Projects**: Check `examples/example_goals.md`  
- **Model Configuration**: See `OPTIMIZED_MODEL_ASSIGNMENT.md`
- **Technical Details**: Browse `docs/` folder

## 💡 Pro Tips

- **Start Simple**: Test with basic goals before complex projects
- **Clear Goals**: Be specific about what you want to build
- **Review Outputs**: Each agent provides detailed analysis worth reading
- **Iterate**: Use the insights to refine your project approach

## � Advanced Configuration

### Custom Model Assignment
Edit `OPTIMIZED_MODEL_ASSIGNMENT.md` to use different models for specific agents based on your API credits and preferences.

### Training Mode
```bash
python -m limco.main train 10 training_results.json
```

### Replay Specific Tasks  
```bash
python -m limco.main replay task_id_here
```

## 🐛 Troubleshooting

**API Key Issues**: Check `.env` file and API credit balance  
**Import Errors**: Ensure `pip install -e .` was successful  
**Slow Performance**: Try `gpt-3.5-turbo` or reduce goal complexity  

For more help, see full documentation in `README.md`

1. **Review the Executive Summary**: This is your complete project proposal
2. **Evaluate the Recommendations**: Consider the technical and business analysis
3. **Make Go/No-Go Decision**: Use the comprehensive analysis to decide
4. **Start Implementation**: Use the detailed plans as your development roadmap

Welcome to autonomous software development! 🚀
