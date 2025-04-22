from fastapi import FastAPI, HTTPException, Path, Body, logger
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
        
        # LangChain message-style prompt
        messages = [
            SystemMessage(content="You are a helpful assistant which helps generate notes based on the tags, keywords, and instructions as provided by the user."),
            HumanMessage(content=f"Notes:\n{context}\n\nNow, based on these notes, generate further notes for the following query. If needed, refer to the context. The query is as follows.:\n{query}")
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
        response_file = note_dir / new_filename
        with response_file.open("w") as f:
            f.write(f"# Response to: {query}\n\n{answer}")
        
        # Create the new subsection file
        response_file = note_dir / new_filename
        with response_file.open("w") as f:
            f.write(f"{answer}")
        
        return {
        "status": "received",
        "username": username,
        "note_name": note_name,
        "context": context,
        "answer": answer,
        "query": query
    }

        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}\n{error_details}")

# 4. Subroutes (returning nothing for now)
@app.get("/users/{username}/notes/{filename}/tutor")
async def tutor_route(username: str, filename: str):
    return {}

@app.get("/users/{username}/notes/{filename}/pux")
async def pux_route(username: str, filename: str):
    return {}

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
