import os
import logging
from typing import List, Optional, Tuple

from groq import Groq
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("Missing GROQ_API_KEY environment variable")

client = Groq(api_key=GROQ_API_KEY)


def web_search(query: str, max_results: int = 3) -> str:
    """Run a simple web search and return concise observation text."""
    endpoint = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error("Web search failed for query=%r: %s", query, exc)
        return f"Search failed for query: {query}"

    snippets: List[str] = []
    abstract = data.get("AbstractText", "").strip()
    if abstract:
        snippets.append(abstract)

    related = data.get("RelatedTopics", [])
    for item in related:
        if len(snippets) >= max_results:
            break
        if isinstance(item, dict):
            text = item.get("Text", "").strip()
            if text:
                snippets.append(text)

    if not snippets:
        return f"No search snippets found for query: {query}"

    return " | ".join(snippets[:max_results])


def build_react_prompt(question: str, history: List[str]) -> str:
    """Construct a ReAct-style prompt with explicit Thought/Action/Answer structure."""
    system_message = (
        "You are an agent that answers questions by reasoning step-by-step and "
        "using tools when needed. Use the ReAct format exactly."
    )

    tool_description = (
        "Tool:\n"
        "  Search[query]: Use this when current facts or evidence are needed from the web.\n"
        "Response format:\n"
        "  Thought: <reasoning>\n"
        "  Action: Search[\"...\"] OR Answer: <final answer>\n"
    )

    history_text = "\n".join(history) if history else ""
    user_text = (
        f"Question: {question}\n"
        f"{tool_description}\n"
        "Begin."
    )

    prompt = f"{system_message}\n\n{history_text}\n\n{user_text}"
    return prompt


def parse_react_output(output: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse model output and return either action query or final answer."""
    lines = output.splitlines()
    action_query: Optional[str] = None
    answer_text: Optional[str] = None

    # First pass: look for Answer (takes precedence)
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith("Answer:"):
            answer_text = line_stripped[len("Answer:"):].strip()
            if not answer_text and i + 1 < len(lines):
                answer_text = lines[i + 1].strip()
            return None, answer_text

    # Second pass: look for Action
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("Action:") and "Search[" in line_stripped:
            start = line_stripped.find("Search[")
            content = line_stripped[start + len("Search[") :].strip()
            if content.endswith("]"):
                query = content[:-1].strip().strip('"').strip("'")
                action_query = query
                break

    return action_query, answer_text


def run_react_agent(question: str, max_steps: int = 3) -> dict:
    """Execute the ReAct loop and return steps and final answer."""
    history: List[str] = []
    steps: List[dict] = []

    for step in range(1, max_steps + 1):
        prompt = build_react_prompt(question, history)
        logger.info("Step %d prompt built.", step)

        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a ReAct agent."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=600,
            )
        except Exception as exc:
            logger.error("Groq request failed: %s", exc)
            return {
                "success": False,
                "error": "Failed to get a response from Groq.",
                "steps": steps,
            }

        output = completion.choices[0].message.content.strip()
        logger.info("Model output:\n%s", output)

        action_query, answer_text = parse_react_output(output)

        step_data = {
            "step": step,
            "thinking": output,
        }

        if action_query:
            observation = web_search(action_query)
            observation_text = f"Observation: {observation}"
            history.append(output)
            history.append(observation_text)
            step_data["action"] = f"Search[{action_query}]"
            step_data["observation"] = observation
            steps.append(step_data)
            logger.info("Performed Search action for query=%r.", action_query)
            continue

        if answer_text:
            logger.info("Final answer produced.")
            step_data["action"] = "Answer"
            step_data["final_answer"] = answer_text
            steps.append(step_data)
            return {
                "success": True,
                "final_answer": answer_text,
                "steps": steps,
            }

        logger.warning("Output did not contain a valid Action or Answer.")
        step_data["action"] = "Unclear"
        steps.append(step_data)
        history.append(output)

    return {
        "success": False,
        "error": "Could not produce a final answer within the allowed steps.",
        "steps": steps,
    }


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    """API endpoint to ask a question and get ReAct reasoning."""
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    result = run_react_agent(question)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
