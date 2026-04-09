import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai import LLM

# Load environment variables
load_dotenv()

def run_healthcare_crew(topic: str, complexity_level: str) -> str:
    # Initialize the LLM (GPT-4o) using CrewAI's built-in wrapper
    llm = LLM(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

    # Define Complexity Instructions for the Writer
    complexity_instructions = {
        "Low": "Use very simple words, short sentences, and highly accessible language (Grade 6-8 reading level). Avoid complex medical jargon.",
        "Medium": "Use clear language accessible to the general public, but include some basic medical terms with brief explanations.",
        "High": "Include technical biological terms, detailed physiological explanations, and advanced medical terminology suitable for someone with strong health literacy."
    }
    
    tone_instruction = complexity_instructions.get(complexity_level, complexity_instructions["Medium"])

    # 1. Medical Researcher
    researcher = Agent(
        role='Medical Researcher',
        goal=f'Find comprehensive, accurate, and evidence-based information on {topic}.',
        backstory=(
            "You are an expert medical researcher with years of experience navigating complex "
            "clinical data, studies, and health guidelines. Your job is to gather the most "
            "accurate and reliable facts to ensure patient safety and correct information."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # 2. Health Communicator (Writer)
    writer = Agent(
        role='Health Communicator',
        goal=f'Write an engaging and understandable guide about {topic} based on the research. {tone_instruction}',
        backstory=(
            "You are a skilled medical writer who specializes in translating complex medical "
            "jargon into accessible, patient-friendly language. You are compassionate and "
            "always consider the reader's health literacy."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # 3. Medical Fact-Checker (Editor)
    editor = Agent(
        role='Medical Fact-Checker',
        goal=f'Review the drafted guide on {topic} for accuracy, empathy, safety, and clear structure.',
        backstory=(
            "You are a meticulous medical editor and fact-checker. You ensure that the tone is "
            "empathetic, the medical advice is safe and accurate, and the document is structured "
            "logically for the best patient experience."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # Tasks
    research_task = Task(
        description=f'Research the latest, evidence-based medical information on: {topic}. '
                    f'Include details on symptoms, causes, diagnosis, treatments, and lifestyle modifications.',
        expected_output=f'A comprehensive research report on {topic} containing facts, medical guidelines, and relevant data.',
        agent=researcher
    )

    write_task = Task(
        description=f'Using the research report, write an educational guide for patients about {topic}. '
                    f'CRITICAL: You MUST adhere to this complexity constraint: {tone_instruction}',
        expected_output=f'A well-written, easy-to-read patient guide on {topic} that strictly follows the requested reading level.',
        agent=writer
    )

    edit_task = Task(
        description=f'Review the drafted patient guide about {topic}. '
                    f'Check that the text flows well, the medical facts from the research are accurately represented, '
                    f'the tone is empathetic, and the complexity perfectly matches the constraint: {tone_instruction}. '
                    f'Format the final output cleanly in Markdown.',
        expected_output=f'A finalized, polished patient guide in Markdown format ready for publication.',
        output_file=os.path.join(os.getcwd(), 'Patient_Guide.md'),
        agent=editor
    )

    # Assemble Crew
    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, write_task, edit_task],
        process=Process.sequential,
        verbose=True,
        share_crew=False
    )

    # Execute the crew workflow
    result = crew.kickoff()
    
    # Return string representation of the final result
    return str(result)
