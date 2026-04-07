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

### 2. Chain-of-Thought Math Solver (math_cot_solver.py / math_app.py)
A math problem solver that uses **Chain-of-Thought** prompting to solve complex math problems with explicit step-by-step reasoning.

**Features:**
- Supports arithmetic, algebra, and word problems
- Step-by-step reasoning with validation
- Web interface at `http://localhost:5001`
- Educational tool for learning math problem-solving

**Usage:**
```bash
# Set API key
$env:GROQ_API_KEY="your-groq-key"

# Run CLI version
python math_cot_solver.py

# Run web version
python math_app.py
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