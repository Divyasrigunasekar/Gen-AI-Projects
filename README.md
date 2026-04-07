# Gen-AI Projects

A collection of AI-powered applications built with Python, Flask, and Groq API.

## Projects

### 1. ReAct Agent (react_agent.py / app.py)
A question-answering agent that uses **Reasoning + Acting** pattern to answer questions by combining step-by-step reasoning with web search capabilities.

**Features:**
- Step-by-step reasoning before actions
- Web search integration using DuckDuckGo API
- Beautiful web interface at `http://localhost:5000`
- Supports complex queries requiring external knowledge

**Usage:**
```bash
# Set API key
$env:GROQ_API_KEY="your-groq-key"

# Run CLI version
python react_agent.py

# Run web version
python app.py
```

### 2. Support Prompt Generator (support_prompt_app.py)
A UI-driven prompt builder that generates production-ready customer support prompts for ReAct, Chain-of-Thought, and Self-Reflection patterns.

**Features:**
- Build prompts for realistic customer support scenarios
- Choose between ReAct, CoT, and Self-Reflection templates
- Copy-paste ready output for OpenAI Playground or notebooks
- Web interface at `http://localhost:5003`

**Usage:**
```bash
# Run web version
python support_prompt_app.py
```

### 3. Self-Reflecting Code Review Agent (code_review_agent.py / code_review_app.py)
An AI-powered code review system that analyzes Python code using AST, generates feedback, and then self-reflects to improve its own suggestions.

**Features:**
- AST-based structural analysis (detects syntax errors, complexity, mutable defaults)
- AI-generated initial code review (bugs, style, performance)
- Self-reflection mechanism for more accurate feedback
- Web interface at `http://localhost:5002`
- Prevents hallucinations by grounding suggestions in code analysis

**Usage:**
```bash
# Set API key
$env:GROQ_API_KEY="your-groq-key"

# Run CLI version
python code_review_agent.py

# Run web version
python code_review_app.py
```

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Divyasrigunasekar/Gen-AI-Projects.git
   cd Gen-AI-Projects
   ```

2. **Install dependencies:**
   ```bash
   pip install groq flask requests
   ```

3. **Get Groq API Key:**
   - Visit [https://console.groq.com/keys](https://console.groq.com/keys)
   - Create a new API key
   - Set environment variable: `$env:GROQ_API_KEY="your-key"`

4. **Run the applications:**
   - ReAct Agent: `python app.py` (opens at http://localhost:5000)
   - Math Solver: `python math_app.py` (opens at http://localhost:5001)
   - Code Review: `python code_review_app.py` (opens at http://localhost:5002)
   - Support Prompt Generator: `python support_prompt_app.py` (opens at http://localhost:5003)

## Repository Structure

```
Gen-AI-Projects/
├── app.py                 # ReAct web app
├── math_app.py           # Math solver web app
├── code_review_app.py    # Code review web app
├── support_prompt_app.py # Support prompt generator web app
├── react_agent.py        # ReAct CLI
├── math_cot_solver.py    # Math solver CLI
├── code_review_agent.py  # Code review CLI
├── templates/
│   ├── index.html        # ReAct UI
│   ├── math_index.html   # Math UI
│   ├── code_review.html  # Code review UI
│   └── support_prompt.html # Support prompt UI
├── README.md             # Documentation
└── .gitignore            # Exclusions
```

## Architecture

### ReAct Pattern
```
User Query → Thought → Action (Search) → Observation → Thought → Answer
```

### Chain-of-Thought Pattern
```
Problem → Step 1 → Step 2 → ... → Final Answer
```

## Technologies Used

- **Python 3.14**
- **Groq API** (llama-3.1-8b-instant model)
- **Flask** (web frameworks)
- **DuckDuckGo API** (web search)
- **HTML/CSS/JavaScript** (web interfaces)

## Examples

### ReAct Agent
- Input: "What is the projected global population in 2030?"
- Output: Step-by-step reasoning with web search and final answer

### Math Solver
- Input: "Solve for x: 3x + 7 = 22"
- Output: Step 1: Subtract 7 → Step 2: Divide by 3 → Answer: x = 5

### Code Review Agent
- Input: Python function with mutable default
- Output: AST analysis → Initial review → Self-reflection → Refined review

## Contributing

Feel free to contribute by:
- Adding new problem types
- Improving the UI/UX
- Adding more AI models
- Enhancing validation logic

## License

MIT License - feel free to use and modify.

---

Built with ❤️ using AI engineering best practices.