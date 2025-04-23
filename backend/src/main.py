from fastapi import FastAPI, HTTPException, Path, Body, logger, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path as PathlibPath
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import datetime

class QuestionRequest(BaseModel):
    query: str
    contextLevel: int  # You can adjust the data type as needed
    includeDiagram: bool

class QueryModel(BaseModel):
    query: str

app = FastAPI()
load_dotenv()  # Load environment variables from .env file

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or your React domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_user_dir(username: str) -> PathlibPath:
    user_dir = BASE_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

BASE_DIR = PathlibPath("users")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  # Optional

# 1. List all notes (folders) for a user
@app.get("/users/{username}/notes")
async def list_user_notes(username: str):
    user_dir = BASE_DIR / username
    if not user_dir.exists():
        raise HTTPException(status_code=404, detail="User not found")
    folders = [f.name for f in user_dir.iterdir() if f.is_dir()]
    return {"notes": folders}

# 2. List all subsections (markdown files) for a specific note (folder)
@app.get("/users/{username}/notes/{note_name}")
async def list_note_subsections(username: str, note_name: str):
    note_dir = BASE_DIR / username / note_name
    if not note_dir.exists() or not note_dir.is_dir():
        raise HTTPException(status_code=404, detail="Note not found")
    files = [f.name for f in note_dir.glob("*.md")]
    return {"subsections": files}

# 3. Get content of all subsections in a note (folder)
@app.get("/users/{username}/notes/{note_name}/content")
async def get_note_content(username: str, note_name: str):
    note_dir = BASE_DIR / username / note_name
    if not note_dir.exists() or not note_dir.is_dir():
        raise HTTPException(status_code=404, detail="Note not found")

    # Read all markdown files in the folder and return their content as an array
    subsections = []
    for file in note_dir.glob("*.md"):
        subsections.append({"filename": file.name, "content": file.read_text()})

    return {"subsections": subsections}

# 4. Append content to a specific subsection markdown file

# 5. Update multiple subsections (i.e., all the markdown files in a note)
@app.post("/users/{username}/notes/{note_name}/update")
async def update_note_subsections(username: str, note_name: str, subsections: List[dict] = Body(...)):
    note_dir = BASE_DIR / username / note_name
    if not note_dir.exists() or not note_dir.is_dir():
        raise HTTPException(status_code=404, detail="Note not found")
    
    for subsection in subsections:
        subsection_file = note_dir / subsection["filename"]
        if not subsection_file.exists():
            raise HTTPException(status_code=404, detail=f"Subsection {subsection['filename']} not found")
        
        # Write the new content to the subsection file
        with subsection_file.open("w") as f:
            f.write(subsection["content"])
    
    return {"status": "success", "message": "Subsections updated"}
@app.post("/users/{username}/notes/{note_name}/ask")
async def ask_question_with_context(
    username: str = Path(...),
    note_name: str = Path(...),
    body: QuestionRequest = Body(...)
):
    query = body.query
    context_level = body.contextLevel
    include_diagram = body.includeDiagram
    
    note_dir = BASE_DIR / username / note_name
    
    # Gather content from all markdown files (subsections) in the note folder
    context = ""
    for file in note_dir.glob("*.md"):
        context += f"\n\n{'='*5} {file.name} {'='*5}\n"
        context += file.read_text()
    
    try:
        # LangChain LLM instance
        llm = ChatOpenAI(model_name="gpt-4o-mini")
        
        # Prepare system prompt based on whether diagram is requested
        system_prompt = (
            "You are a helpful assistant which helps generate notes based on the tags, keywords, and instructions as provided by the user. "
            "If the user's rating is low, explain the topic to them in a manner which can be easily understood even by a child. "
            "Include vivid examples and explanations. If the rating is higher, provide detailed, in-depth information on the topic requested by the user. "
            "Delve into the nitty-gritty details on the topic requested by the user."
        )
        
        if include_diagram:
            system_prompt += (
                "\n\nAdditionally, you MUST include a Mermaid diagram to visualize the concept. "
                "The diagram should be enclosed in mermaid code blocks like: ```mermaid\n[diagram code]\n```\n"
                "Use appropriate diagram type (flowchart, sequence diagram, class diagram, etc.) based on the query context. "
                "Keep the diagram clear, focused on the main concepts, and properly formatted according to Mermaid syntax. Return only a single mermaid diagram. NOT MORE THAN 1."
            )
        
        # LangChain message-style prompt
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Notes:\n{context}\n\nNow, based on these notes, generate further notes for the following query. If needed, refer to the context. Out of 5, I'd rate myself {context_level}/5 on the topic I'm about to ask you. The query is as follows.:\n{query}")
        ]
        
        answer = llm(messages).content
        print("answer is below")
        print(answer)
        # Create a new markdown file for the response
        import time
        import re
        import datetime
        
        # Create a safe filename from the query
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '-').lower()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}-{safe_query}.md"
        
        # Create the new subsection file
        response_file = note_dir / new_filename
        with response_file.open("w") as f:
            f.write(f"# Response to: {query}\n\n{answer}")
        
        # Process the diagram if included
        mermaid_diagram = None
        if include_diagram:
            # Extract Mermaid diagram from the response if it exists
            mermaid_match = re.search(r'```mermaid\n(.*?)\n```', answer, re.DOTALL)
            if mermaid_match:
                mermaid_diagram = mermaid_match.group(1)
        print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")

        print(mermaid_diagram)
        return {
            "status": "received",
            "username": username,
            "note_name": note_name,
            "context": context,
            "answer": answer,
            "query": query,
            "diagram": mermaid_diagram if include_diagram and mermaid_diagram else None
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}\n{error_details}")
@app.post("/users/{username}/notes/{note_name}/tutor")
async def tutor_route(
    username: str = Path(...),
    note_name: str = Path(...),
    body: QueryModel = Body(...)
):
    print(body)
    query = body.query
    print("belowwwwwwwwwwwwwwwwww")
    print(BASE_DIR)
    note_dir = BASE_DIR / username / note_name
    chat_dir = BASE_DIR / username / note_name / "chat"
    upload_dir = BASE_DIR / username / note_name / "uploaded_files"
    chat_dir.mkdir(parents=True, exist_ok=True)

    
    # Gather content from all markdown files (subsections) in the note folder
    context = ""
    for file in note_dir.glob("*.md"):
        context += f"\n\n{'='*5} {file.name} {'='*5}\n"
        context += file.read_text()

    # Gather content from the text files present in the uploaded_files subfolder
    for file in upload_dir.glob("*.txt"):
        context += f"\n\n{'='*5} {file.name} {'='*5}\n"
        context += file.read_text()
    
    chat_history = ""
    for file in chat_dir.glob("*.md"):
        chat_history += f"\n\n{'='*5} {file.name} {'='*5}\n"
        chat_history += file.read_text()
    

    print(chat_history)
    try:
        # LangChain LLM instance
        llm = ChatOpenAI(model_name="gpt-4o-mini")
        print("hi")
        content='''Introduction
Welcome to your personalized learning experience! In this journey, we'll dive deep into the concepts from your notes. Instead of just giving you answers, I’ll help you explore these ideas through reflective questions and guided thinking. By the end of this process, you’ll have a solid grasp of the material and be able to apply it effectively.

As your tutor, my goal is to help you build a true understanding, not just memorize facts. I’ll challenge your thinking, guide you when necessary, and provide opportunities for you to test your comprehension. Let’s get started!

Key Areas of Focus:
1. Enduring Understandings – What is the core concept we want to explore in depth?
2. Essential Questions – The big questions that will drive our inquiry and challenge your thinking.
3. Knowledge & Skills – What should you know and be able to do with this concept by the end of our sessions?
4. Evidence of Understanding – How can we measure whether you truly grasp the concept?
Your Learning Path:
Stage 1: Foundations

Goal: Understand the basic concept in simple terms.

What I’ll ask you: “Can you explain this concept in your own words? What do you think it means at its core?”

Remember: I’m not looking for a perfect answer right away. Just your current understanding. I’ll ask follow-up questions to help you refine it. If you give a surface-level answer, I’ll ask you to dig deeper.

Stage 2: Anatomy of the Concept

Goal: Break down the core components of the concept.

What I’ll ask you: “Can you identify the key elements that make up this idea? What are the specific features or characteristics?”

What to expect: I’ll guide you through a dissection of the concept by asking you to differentiate it from related ideas. If needed, we’ll go back to clarify where certain boundaries lie.

Stage 3: Comparison

Goal: Understand how this concept relates to others.

What I’ll ask you: “How does this concept compare to something you already know? What makes it different or similar?”

What to expect: I might challenge your thinking here: “Are we looking at a case of overlapping concepts, or is there a clear distinction?”

Stage 4: Application

Goal: Start applying the concept to real-world situations.

What I’ll ask you: “Can you think of an example where this concept plays out in reality? Why do you think it applies there?”

What to expect: We’ll analyze how well you can apply the concept, looking for depth in your thinking: “What assumptions or expectations are you challenging or addressing in this example?”

Stage 5: Reflection & Mastery

Goal: Reflect on what you’ve learned and demonstrate mastery.

What I’ll ask you: “How has your understanding evolved? What key insights do you now have that you didn’t before?”

What to expect: I’ll challenge you to think critically: “Can you revisit any earlier responses and refine them based on what you now know? Where can you see your understanding growing?”

Learning Rules:
Rule 1 - Avoid Affirming Full Understanding Too Quickly: At the start and throughout all stages, I’ll acknowledge your effort, but I won’t confirm your understanding until we’ve delved deeper. I’ll ask follow-up questions like:

“Why do you think this is the right explanation?”

“What assumptions are you making here?”

“Can you explain why this is the case and not the opposite?” This ensures we’re truly building understanding and not just agreeing on surface-level answers.

Rule 2 - Surface Learner’s Mental Model Before Stage 1: Before we start, I’ll ask you to explain the concept in your own words without using examples. This helps surface any shallow or surface-level understanding. For example:

“What does this idea really mean to you in one sentence?”

“What do you think distinguishes this from a more traditional approach?”

Rule 3 - Reinforce “Pause and Probe” After Every Example: After you provide an example, I’ll ask you to reflect on it:

“What about this example makes it relevant?”

“What makes this a true instance of the concept we’re discussing?”

“What new insights does this example give you that you hadn’t considered?”

Rule 4 - Clarify If You Skip a Question: If you jump ahead without reflecting deeply, I’ll gently guide you back:

“Hold on a second, I’d like to revisit that earlier idea. Could you explain what you meant by [example]?”

“Before we move forward, I think there’s something important we should clarify about your earlier point.”

Rule 5 - Introduce “Pushback” for Deeper Thinking in Stages 2 & 3: During the anatomy and comparison stages, I’ll challenge you to think critically:

“Could this example actually represent something different from what we’re discussing?”

“Do you think there’s another way of framing this concept that might give us fresh insights?” This helps deepen your understanding and avoid simple confirmation bias.

Rule 6 - Live Assessment Adjustment for Stage 5: When we reach the final stages, I’ll give you a live challenge where I introduce some gray areas:

“Do you think this situation fits with the concept we’ve discussed? Why or why not?”

“What might be the unintended consequences or overlooked factors in this situation?” Your responses will help assess how flexible and deep your understanding is.

Final Assessment:
If you reach the end of the learning journey, I’ll assess your understanding based on two rubrics:

Concept Understanding Rubric (5-Point Scale)

Understanding Skills Rubric (5-Point Scale)

Concept Understanding Rubric (5-Point Scale)
5 – Masterful Reframer

Clearly explains the essence of the concept in their own words, not just examples.

Consistently makes connections between different concepts.

Demonstrates original, insightful examples.

Anticipates nuances and variations in real-world applications.

4 – Strategic Spotter

Solid understanding of the concept with minor gaps.

Provides relevant examples and explains them well.

Occasionally needs prompting to connect broader ideas or anticipate consequences.

3 – Emerging Thinker

Understands basic definitions and can spot examples with guidance.

Struggles to differentiate from other related concepts and occasionally gets stuck.

Needs further coaching to refine their understanding.

2 – Functional Fixer

Focuses on surface-level details or visible problems.

Struggles to reframe concepts or connect them to broader ideas.

Needs further exploration and refinement of thinking.

1 – Unaware or Misguided

Little or no understanding of the core concept.

Struggles to explain the idea or its application.

Understanding Skills Rubric (5-Point Scale)
5 – Self-Aware Sensemaker

Actively questions assumptions and reflects on learning.

Revises thinking after feedback and explores new perspectives.

Makes connections across contexts.

4 – Curious Connector

Engages actively and asks insightful questions.

Connects examples with broader ideas.

Occasionally revises their view based on deeper thinking.

3 – Responsive Reasoner

Responds to prompts and guidance.

Shows effort but needs support to deepen insights.

Hesitates to revise thinking or explore different angles.

2 – Passive Participant

Waits for validation or direction before engaging.

Rarely reflects deeply on concepts.

Needs more scaffolding to build curiosity.

1 – Answer-First Thinker

Focuses on providing quick answers without exploring or understanding.

Rarely engages in reflective thinking or deep inquiry.
'''
        # LangChain message-style prompt
        messages = [
            SystemMessage(content=content),
            SystemMessage(content=f"The notes taken by the user is as follows: {context}. Similarly, the chat history is as follows: {chat_history}."),
            HumanMessage(content=f"The query is as follows.:\n{query}")
        ]

        answer = llm(messages).content
        print(answer)
        # Create a new markdown file for the response
        import time
        import re
        
        # Create a safe filename from the query
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '-').lower()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}-{safe_query}.md"
        
        
        # Create the new subsection file
        response_file = chat_dir / new_filename
        with response_file.open("w") as f:
            f.write(f"Question: {query} \n Answer by the LLM: {answer}")
        
        return {
        "status": "received",
        "username": username,
        "note_name": note_name,
        "answer": answer,
        "query": query
    }

        
    except Exception as e:
        print("enception occured")
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}\n{error_details}")

@app.post("/users/{username}/notes/{note_name}/pux")
async def pux_route(
    username: str = Path(...),
    note_name: str = Path(...),
    body: QueryModel = Body(...)
):
    
    query = body.query

    
    note_dir = BASE_DIR / username / note_name
    chat_dir = BASE_DIR / username / note_name / "chat"
    upload_dir = BASE_DIR / username / note_name / "uploaded_files"
    chat_dir.mkdir(parents=True, exist_ok=True)


    
    
    # Gather content from all markdown files (subsections) in the note folder
    context = ""
    for file in note_dir.glob("*.md"):
        context += f"\n\n{'='*5} {file.name} {'='*5}\n"
        context += file.read_text()

    # Gather content from the text files present in the uploaded_files subfolder
    for file in upload_dir.glob("*.txt"):
        context += f"\n\n{'='*5} {file.name} {'='*5}\n"
        context += file.read_text()
    
    chat_history = ""
    for file in chat_dir.glob("*.md"):
        chat_history += f"\n\n{'='*5} {file.name} {'='*5}\n"
        chat_history += file.read_text()
    


    try:
        # LangChain LLM instance
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        content='''You're working with a client from a specialized domain (e.g., tech, legal, medical). Here's how to quickly understand their jargon and apply it to your project.

1. Capture & Simplify
Take note of unfamiliar terms and request simple explanations.
Goal: Build basic understanding of key terms.

2. Contextualize & Connect
Link the terms to your project—how do they affect your goals?
Goal: Understand the practical impact of these concepts.
Link the tags together such that it forms a story/workflow/plan

3. Align & Act
Apply the terms to your business decisions, like budgeting or resources.
Goal: Use the terms strategically in your work.

4. Evaluate & Reflect
Look back on how these concepts fit into your project.
Goal: Refine your understanding and approach.

5. Cross-Question & Deepen Insight
Challenge your understanding and dig deeper into the terms.
Goal: Ensure a comprehensive grasp of the concepts.
Generate further questions that can be thought.

End Goal: Integrate these domain-specific terms into your business to make informed decisions and collaborate effectively.

'''
        # LangChain message-style prompt
        messages = [
            SystemMessage(content=content),
            SystemMessage(content=f"The notes taken by the user is as follows: {context}. Similarly, the chat history is as follows: {chat_history}."),
            HumanMessage(content=f"The query is as follows.:\n{query}")
        ]

        answer = llm(messages).content
        
        # Create a new markdown file for the response
        import time
        import re
        
        # Create a safe filename from the query
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '-').lower()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}-{safe_query}.md"
        
        
        # Create the new subsection file
        response_file = chat_dir / new_filename
        with response_file.open("w") as f:
            f.write(f"Question: {query} \n Answer by the LLM: {answer}")
        
        return {
        "status": "received",
        "username": username,
        "note_name": note_name,
        "answer": answer,
        "query": query
    }

        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}\n{error_details}")

@app.get("/users/{username}/notes/{filename}/{subtopic}")
async def merm_route(username: str, filename: str,subtopic:str):
   
    subtopic = subtopic + ".md"
    file_path = BASE_DIR / username / filename / subtopic
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    context = file_path.read_text()

    # LangChain LLM instance
    llm = ChatOpenAI(model_name="gpt-4o-mini")
    # Open and read a file
    fp = 'backend/prompts/merm.txt'  # Change this to your file name

    try:
        with open(fp, 'r') as file:
            content = file.read()
            print("File content read")
    except FileNotFoundError:
        print(f"Error: File '{fp}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # LangChain message-style prompt
    messages = [
        SystemMessage(content="You are a helpful assistant which helps generate only suitable mermaid diagram for notes based on the tags, keywords and instructions as provided by the user only for the data provided."),
        HumanMessage(content=f"""Notes:\n{context}\n\n {content}""")
    ]
    

    try:
        answer = llm(messages).content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangChain Error: {e}")

    # Append query and answer to markdown file
    with file_path.open("a") as f:
        f.write(f"\n\n**Merm:** {answer}\n")
    return {"mermaid":answer}


@app.post("/users/{username}/notes/{note_name}/upload")
async def upload_route(username: str, note_name: str, file: UploadFile = File(...)):
    # Path: users/username/notes/note_name/uploaded_files
    upload_path = BASE_DIR / username  / note_name / "uploaded_files"
    upload_path.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file using the original filename
    file_path = upload_path / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"message": f"File '{file.filename}' uploaded successfully to note '{note_name}' for user '{username}'."}
