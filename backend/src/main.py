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
                "Keep the diagram clear, focused on the main concepts, and properly formatted according to Mermaid syntax."
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

        with open("backend/prompts/tutor.txt", 'r') as file:
            content = file.read()
            print("File content read")
        
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

        with open("backend/prompts/business.txt", 'r') as file:
            content = file.read()
            print("File content read")
        
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
