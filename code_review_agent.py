import ast
import os
from typing import Dict, List, Any
from groq import Groq

# Set your Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("Missing GROQ_API_KEY environment variable")

client = Groq(api_key=GROQ_API_KEY)

class CodeAnalyzer:
    """Analyze Python code using AST."""

    def __init__(self):
        self.issues = []

    def analyze(self, code: str) -> Dict[str, Any]:
        """Parse code and detect issues."""
        try:
            tree = ast.parse(code)
            self.issues = []
            self._visit_tree(tree)
            return {
                "parsed": True,
                "issues": self.issues,
                "complexity": self._calculate_complexity(tree)
            }
        except SyntaxError as e:
            return {
                "parsed": False,
                "error": f"Syntax error: {e.msg} at line {e.lineno}",
                "issues": []
            }

    def _visit_tree(self, node: ast.AST):
        """Traverse AST and collect issues."""
        if isinstance(node, ast.FunctionDef):
            self._check_function(node)
        elif isinstance(node, ast.Name):
            self._check_variable_usage(node)
        # Add more checks as needed

        for child in ast.iter_child_nodes(node):
            self._visit_tree(child)

    def _check_function(self, node: ast.FunctionDef):
        """Check function-related issues."""
        if len(node.body) > 20:
            self.issues.append(f"Function '{node.name}' is too long ({len(node.body)} statements)")

        # Check for mutable defaults
        for arg in node.args.defaults:
            if isinstance(arg, (ast.List, ast.Dict)):
                self.issues.append(f"Mutable default argument in function '{node.name}'")

    def _check_variable_usage(self, node: ast.Name):
        """Basic variable usage check (simplified)."""
        # This is a simplified check; full analysis would track definitions/uses
        pass

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity

def generate_initial_review(code: str, ast_findings: Dict) -> str:
    """Generate initial code review using AI."""
    prompt = f"""
Analyze this Python code for review:

Code:
{code}

AST Analysis:
- Parsed: {ast_findings['parsed']}
- Issues: {', '.join(ast_findings.get('issues', []))}
- Complexity: {ast_findings.get('complexity', 0)}

Provide a code review focusing on:
1. Bugs and errors
2. Style and readability
3. Performance improvements
4. Best practices

Be specific and actionable.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

def self_reflect_and_refine(initial_review: str, code: str, ast_findings: Dict) -> str:
    """Self-reflect on initial review and provide refined version."""
    prompt = f"""
Original Code Review:
{initial_review}

Code:
{code}

AST Findings: {ast_findings}

Self-reflection task:
1. Identify any inaccurate suggestions in the original review
2. Note any missed issues based on the code and AST findings
3. Check if suggestions are grounded in actual code problems
4. Consider if the review is balanced (not too harsh or lenient)

Then provide a REFINED REVIEW that addresses these reflections.
Make it more accurate, comprehensive, and actionable.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def review_code(code: str) -> Dict[str, Any]:
    """Complete code review workflow with self-reflection."""
    analyzer = CodeAnalyzer()
    ast_findings = analyzer.analyze(code)

    if not ast_findings["parsed"]:
        return {
            "success": False,
            "error": ast_findings["error"],
            "ast_findings": ast_findings
        }

    initial_review = generate_initial_review(code, ast_findings)
    refined_review = self_reflect_and_refine(initial_review, code, ast_findings)

    return {
        "success": True,
        "ast_findings": ast_findings,
        "initial_review": initial_review,
        "refined_review": refined_review
    }

# Example usage
if __name__ == "__main__":
    sample_code = """
def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    return total / len(numbers)

def process_data(data_list=[]):
    for item in data_list:
        print(item.upper())
    return len(data_list)

result = calculate_average([1, 2, 3, 4, 5])
print(f"Average: {result}")
"""

    review_result = review_code(sample_code)

    if review_result["success"]:
        print("AST Findings:", review_result["ast_findings"])
        print("\nInitial Review:")
        print(review_result["initial_review"])
        print("\nRefined Review:")
        print(review_result["refined_review"])
    else:
        print("Error:", review_result["error"])
