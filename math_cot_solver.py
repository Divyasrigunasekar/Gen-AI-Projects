import os
import re
from groq import Groq
from typing import Dict, List, Optional

# Set your Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("Missing GROQ_API_KEY environment variable")

client = Groq(api_key=GROQ_API_KEY)

def build_cot_prompt(problem: str) -> str:
    """Construct a CoT prompt for math problem solving."""
    system_message = (
        "You are a math expert solving problems using Chain-of-Thought reasoning. "
        "For each problem, show your work step-by-step, explain your reasoning, "
        "and box the final answer using \\boxed{}."
    )

    examples = """
Example 1 (Arithmetic):
Problem: What is 15 + 27?
Step 1: Add the units place: 5 + 7 = 12, write 2, carry 1.
Step 2: Add the tens place: 1 + 1 + 2 = 4.
Final Answer: \\boxed{42}

Example 2 (Algebra):
Problem: Solve 2x - 5 = 11.
Step 1: Add 5 to both sides: 2x = 16.
Step 2: Divide both sides by 2: x = 8.
Final Answer: \\boxed{8}

Example 3 (Word Problem):
Problem: A train travels 120 km in 2 hours. What is its speed?
Step 1: Speed = distance / time.
Step 2: Speed = 120 km / 2 hours = 60 km/h.
Final Answer: \\boxed{60 km/h}
"""

    prompt = f"{system_message}\n\n{examples}\n\nNow solve this problem step by step:\n{problem}\n\nContinue reasoning until you reach the final answer. End with Final Answer: \\boxed{{answer}}\n\nStep 1:"
    return prompt

def call_groq_api(prompt: str, model: str = "llama-3.1-8b-instant", max_tokens: int = 1000) -> str:
    """Call Groq API and return the response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful math tutor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent math answers
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def parse_cot_response(response: str) -> Dict[str, any]:
    """Parse the CoT response into steps and final answer."""
    steps = []
    final_answer = None

    # Extract steps
    step_pattern = r"Step (\d+):(.*?)(?=Step \d+:|$)"
    matches = re.findall(step_pattern, response, re.DOTALL)
    for step_num, step_text in matches:
        steps.append({
            "step": int(step_num),
            "reasoning": step_text.strip()
        })

    # Extract final answer
    boxed_pattern = r"\\boxed\{([^}]+)\}"
    match = re.search(boxed_pattern, response)
    if match:
        final_answer = match.group(1).strip()

    return {
        "steps": steps,
        "final_answer": final_answer,
        "full_response": response
    }

def validate_answer(problem: str, parsed_result: Dict) -> Dict:
    """Basic validation: check if steps seem logical and answer is present."""
    result = parsed_result.copy()
    result["validation"] = {
        "has_steps": len(result["steps"]) > 0,
        "has_answer": result["final_answer"] is not None,
        "step_count": len(result["steps"]),
        "warnings": []
    }

    # Simple checks
    if not result["validation"]["has_answer"]:
        result["validation"]["warnings"].append("No final answer found.")

    if len(result["steps"]) < 2:
        result["validation"]["warnings"].append("Few reasoning steps - may be incomplete.")

    # For arithmetic, check if answer is numeric
    if "arithmetic" in problem.lower() and result["final_answer"]:
        try:
            float(result["final_answer"])
        except ValueError:
            result["validation"]["warnings"].append("Answer doesn't appear numeric for arithmetic problem.")

    return result

def solve_math_problem(problem: str) -> Dict:
    """Main function to solve a math problem using CoT."""
    prompt = build_cot_prompt(problem)
    response = call_groq_api(prompt)
    parsed = parse_cot_response(response)
    validated = validate_answer(problem, parsed)
    return validated

# Example usage
if __name__ == "__main__":
    problem = "Solve for x: 3x + 7 = 22"
    result = solve_math_problem(problem)

    print("Problem:", problem)
    print("\nReasoning Steps:")
    for step in result["steps"]:
        print(f"Step {step['step']}: {step['reasoning']}")

    print(f"\nFinal Answer: {result['final_answer']}")
    print(f"\nValidation: {result['validation']}")
