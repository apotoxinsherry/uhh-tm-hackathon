from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path as PathlibPath
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

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

# 1. List markdown files for a user
@app.get("/users/{username}/notes")
async def list_user_notes(username: str):
    user_dir = BASE_DIR / username
    if not user_dir.exists():
        raise HTTPException(status_code=404, detail="User not found")
    files = [f.name for f in user_dir.glob("*.md")]
    return {"notes": files}

# 2. Get content of a specific markdown file
@app.get("/users/{username}/notes/{filename}")
async def get_note_content(username: str, filename: str):
    filename = filename + ".md"
    file_path = BASE_DIR / username / filename 
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": file_path.read_text()}

# 3. Append content to markdown file
@app.post("/users/{username}/notes/{filename}")
async def append_to_note(username: str, filename: str, content: str = Body(...)):
    filename = filename + ".md"
    file_path = BASE_DIR / username / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    with file_path.open("a") as f:
        f.write("\n" + content)
    return {"status": "success", "message": "Content appended"}


@app.post("/users/{username}/notes/{filename}/ask")
async def ask_question_with_context(
    username: str,
    filename: str,
    query: str = Body(..., embed=True),
):
    filename = filename + ".md"
    file_path = BASE_DIR / username / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    context = file_path.read_text()

    # LangChain LLM instance
    llm = ChatOpenAI(model_name="gpt-4o-mini")

    # LangChain message-style prompt
    messages = [
        SystemMessage(content="You are a helpful assistant which helps generate notes based on the tags, keywords and instructions as provided by the user."),
        HumanMessage(content=f"Notes:\n{context}\n\nNow, based on these notes, generate further notes for the following query. If needed, refer to the context. The query is as follows.:\n{query}")
    ]

    try:
        answer = llm(messages).content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangChain Error: {e}")

    # Append query and answer to markdown file
    with file_path.open("a") as f:
        f.write(f"\n\n**Q:** {query}\n**A:** {answer}\n")

    return {"query": query, "answer": answer}


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

    # LangChain message-style prompt
    messages = [
        SystemMessage(content="You are a helpful assistant which helps generate only suitable mermaid diagram for notes based on the tags, keywords and instructions as provided by the user only for the data provided."),
        HumanMessage(content=f"Notes:\n{context}\n\nNow, based on these notes generate mermaid syntax of only key important meaningfull diagrams (not more than 2) to make understanding easier with appropriate mermaid diagrams")
    ]

    try:
        answer = llm(messages).content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangChain Error: {e}")

    # Append query and answer to markdown file
    with file_path.open("a") as f:
        f.write(f"\n\n**Merm:** {answer}\n")
    return {"mermaid":answer}