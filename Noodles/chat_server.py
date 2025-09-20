from __future__ import annotations

import os
import json
import asyncio
import logging
from datetime import datetime

def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        color = self.COLORS.get(level, "")
        msg = super().format(record)
        return f"{color}[{ts}] {level:<8}{self.RESET} {msg}"
from typing import Any, Dict, List, Optional, Tuple

try:
    import colorama
    colorama.init()  # Enable ANSI colors on Windows
except ImportError:
    pass  # Fallback to plain ANSI if colorama not installed

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

from fastmcp.client.client import Client
from fastmcp.utilities.json_schema_type import json_schema_to_type

# LangChain chat models
try:
    from langchain_groq import ChatGroq  # Groq
except Exception:  # pragma: no cover
    ChatGroq = None  # type: ignore
try:
    from langchain_google_genai import ChatGoogleGenerativeAI as ChatGemini  # Gemini
except Exception:  # pragma: no cover
    ChatGemini = None  # type: ignore
try:
    # ChatOllama lives in langchain_community for classic API
    from langchain_community.chat_models import ChatOllama  # Ollama
except Exception:  # pragma: no cover
    try:
        # Fallback newer package name if installed
        from langchain_ollama import ChatOllama  # type: ignore
    except Exception:
        ChatOllama = None  # type: ignore

try:
    import ollama  # Direct Ollama client
except Exception:  # pragma: no cover
    ollama = None  # type: ignore

from langchain_core.messages import SystemMessage, HumanMessage


# -----------------
# Custom Ollama LLM
# -----------------

class OllamaLLM:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url
        if ollama is None:
            raise RuntimeError("ollama package not installed")

    def invoke(self, messages):
        # Convert LangChain messages to Ollama format
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                ollama_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                ollama_messages.append({"role": "user", "content": msg.content})
        # Call Ollama directly
        response = ollama.chat(
            model=self.model,
            messages=ollama_messages,
            options={"temperature": 0}
        )
        # Return AIMessage-like object
        from langchain_core.messages import AIMessage
        return AIMessage(content=response['message']['content'])


# -----------------------
# Environment and Logging
# -----------------------

_found = find_dotenv()
if _found:
    load_dotenv(_found)
else:
    # Explicit workspace path fallback
    _env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red bg
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        color = self.COLORS.get(level, "")
        msg = super().format(record)
        return f"{color}[{ts}] {level:<8}{self.RESET} {msg}"


logger = logging.getLogger("chat_api")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(ColorFormatter("%(message)s"))
logger.handlers.clear()
logger.addHandler(_handler)


# -------------
# FastAPI setup
# -------------

app = FastAPI(title="TIC Chat API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------
# Request/Response model
# ----------------------


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    chat_type: str = Field(..., pattern="^(ollama|groq|gemini)$", description="Model preference: ollama | groq | gemini")


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}
    result: Optional[str] = None


class ChatResponse(BaseModel):
    ok: bool
    model: Optional[str]
    chat_type: str
    answer: Optional[str]
    tool_calls: List[ToolCall] = []
    retries: Dict[str, int] = {}
    error: Optional[str] = None


# -----------------
# MCP tool helpers
# -----------------


def get_mcp_url() -> str:
    # Prefer explicit env var if present
    env_url = os.getenv("MCP_URL")
    if env_url:
        return env_url
    # Fallback to VS Code MCP config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".vscode", "mcp.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["servers"]["TIC"]["url"]
    except Exception:
        # Final fallback to common default
        return "http://127.0.0.1:8005/mcp"


async def list_mcp_tools(url: str) -> List[Dict[str, Any]]:
    logger.info(f"Listing MCP tools from {url}")
    async with Client(url) as client:
        tools = await client.list_tools()
        # Convert to serializable dicts
        out: List[Dict[str, Any]] = []
        for t in tools:
            out.append({
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.inputSchema or {},
            })
        return out


async def call_mcp_tool(url: str, name: str, arguments: Dict[str, Any]) -> str:
    logger.info(f"Calling MCP tool '{name}' with args: {arguments}")
    async with Client(url) as client:
        result = await client.call_tool_mcp(name=name, arguments=arguments or {})
        if result.structuredContent:
            try:
                return json.dumps(result.structuredContent, ensure_ascii=False)
            except Exception:
                pass
        # Fallback to first text content block
        if result.content:
            try:
                # result.content is List[ContentBlock]; try to extract text
                for block in result.content:
                    text = getattr(block, "text", None)
                    if text:
                        return str(text)
            except Exception:
                pass
        # Generic string
        return str(result)


# -----------------
# LLM initializers
# -----------------


def get_llm(name: str):
    name = name.lower()
    if name == "gemini":
        model_name = os.getenv("model_gemini")
        if not model_name:
            raise RuntimeError("Missing env var model_gemini")
        if ChatGemini is None:
            raise RuntimeError("ChatGemini (langchain_google_genai) not installed")
        return ChatGemini(model=model_name, temperature=0)
    if name == "groq":
        model_name = os.getenv("model_grok") or os.getenv("model_groq")
        if not model_name:
            raise RuntimeError("Missing env var model_grok")
        if ChatGroq is None:
            raise RuntimeError("ChatGroq (langchain_groq) not installed")
        return ChatGroq(model=model_name, temperature=0)
    if name == "ollama":
        model_name = os.getenv("model_local") or "llama3.1:8b-instruct-q4_K_M"
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        if base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost"):
            # Use direct Ollama client for local
            return OllamaLLM(model=model_name, base_url=base_url)
        else:
            # Use LangChain ChatOllama for remote
            if ChatOllama is None:
                raise RuntimeError("ChatOllama not installed")
            return ChatOllama(model=model_name, base_url=base_url, temperature=0)
    raise ValueError(f"Unknown chat model name: {name}")


# -------------------------
# Tool-planning via prompt
# -------------------------


def build_tool_planner_prompt(tools: List[Dict[str, Any]]) -> str:
    # Provide tool schema hints but keep concise
    parts = [
        "You may optionally call exactly one tool if required.",
        "Decide and output ONLY a strict JSON object with keys:",
        "{\"use_tool\": bool, \"tool_name\": string|null, \"arguments\": object|null, \"reason\": string}",
        "If use_tool is true, ensure arguments match the tool's input schema.",
        "Available tools:"
    ]
    for t in tools[:8]:
        name = t.get("name")
        desc = (t.get("description") or "").strip()
        schema = t.get("inputSchema") or {}
        props = list((schema.get("properties") or {}).keys())
        required = schema.get("required") or []
        parts.append(f"- {name}: {desc} | properties={props} required={required}")
    parts.append("Respond with JSON only. No extra text.")
    return "\n".join(parts)


async def plan_tool_usage(llm, user_message: str, tools: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], Dict[str, Any], str]:
    system = build_tool_planner_prompt(tools)
    logger.info("Requesting tool plan from LLM")
    msg = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user_message),
    ])
    raw = getattr(msg, "content", "")
    
    # Clean up markdown code blocks if present
    cleaned_raw = raw.strip()
    if cleaned_raw.startswith("```json"):
        cleaned_raw = cleaned_raw[7:]  # Remove ```json
    if cleaned_raw.startswith("```"):
        cleaned_raw = cleaned_raw[3:]   # Remove ```
    if cleaned_raw.endswith("```"):
        cleaned_raw = cleaned_raw[:-3]  # Remove trailing ```
    cleaned_raw = cleaned_raw.strip()
    
    try:
        data = json.loads(cleaned_raw)
        use_tool = bool(data.get("use_tool"))
        tool_name = data.get("tool_name") if use_tool else None
        arguments = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
        reason = str(data.get("reason", ""))
        logger.info(f"Planner response -> use_tool={use_tool} tool={tool_name}")
        return use_tool, tool_name, arguments, reason
    except Exception as e:
        logger.error(f"Failed to parse planner JSON: {e}; raw={raw!r}")
        raise


async def final_answer(llm, user_message: str, tool_name: Optional[str], tool_args: Dict[str, Any], tool_result: Optional[str]) -> str:
    system = (
        "You are a helpful assistant. If a tool result is provided, use it to answer succinctly."
    )
    context_parts = []
    if tool_name:
        context_parts.append(f"Tool used: {tool_name}")
        context_parts.append(f"Arguments: {json.dumps(tool_args, ensure_ascii=False)}")
    if tool_result is not None:
        context_parts.append(f"Tool result: {tool_result}")
    context = "\n".join(context_parts)
    logger.info("Requesting final answer from LLM")
    msg = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=f"Question: {user_message}\n{context}"),
    ])
    return str(getattr(msg, "content", ""))


# --------------
# Chat endpoint
# --------------


FALLBACK_ROUTE = ["gemini", "groq", "ollama"]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    logger.info(f"/chat received: chat_type={req.chat_type}")
    mcp_url = get_mcp_url()
    retries: Dict[str, int] = {"gemini": 0, "groq": 0, "ollama": 0}

    # Select provider route based on requested chat_type
    requested = (req.chat_type or "").strip().lower()
    if requested == "gemini":
        route = ["gemini", "groq", "ollama"]
    elif requested == "groq":
        route = ["groq", "ollama"]
    else:  # "ollama" or any other -> no fallback
        route = ["ollama"]

    # Follow selected route, retry each up to 3
    for provider in route:
        attempt = 0
        while attempt < 3:
            attempt += 1
            retries[provider] = attempt
            logger.info(f"Trying provider={provider}, attempt {attempt}/3")
            try:
                llm = get_llm(provider)
                tools = await list_mcp_tools(mcp_url)

                # Plan tool usage
                use_tool, tool_name, tool_args, _ = await plan_tool_usage(llm, req.message, tools)
                tool_calls: List[ToolCall] = []
                tool_result: Optional[str] = None

                if use_tool and tool_name:
                    try:
                        tool_result = await call_mcp_tool(mcp_url, tool_name, tool_args)
                        tool_calls.append(ToolCall(name=tool_name, arguments=tool_args, result=tool_result))
                    except Exception as te:
                        logger.error(f"Tool execution failed: {te}")
                        # Retry the same provider
                        continue

                # Get final answer
                answer = await final_answer(llm, req.message, tool_name, tool_args, tool_result)
                if not answer:
                    logger.warning("Empty answer from model; retrying provider")
                    continue

                logger.info(f"Success with provider={provider}")
                return ChatResponse(
                    ok=True,
                    model=provider,
                    chat_type=req.chat_type,
                    answer=answer,
                    tool_calls=tool_calls,
                    retries=retries,
                )
            except Exception as e:
                logger.error(f"Provider {provider} failed on attempt {attempt}: {e}")
                await asyncio.sleep(0.2)

        logger.warning(f"Provider {provider} exhausted retries; moving to fallback")

    # All providers failed
    logger.error("All providers failed after retries")
    return ChatResponse(
        ok=False,
        model=None,
        chat_type=req.chat_type,
        answer=None,
        tool_calls=[],
        retries=retries,
        error="All providers failed after 3 retries each",
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8088"))
    logger.info(f"Starting API at http://{host}:{port}")
    uvicorn.run("chat_server:app", host=host, port=port, reload=True, log_level="info")
