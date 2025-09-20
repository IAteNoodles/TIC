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
        return "http://0.0.0.0:8005/mcp"


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
        output: Optional[str] = None
        if result.structuredContent:
            try:
                output = json.dumps(result.structuredContent, ensure_ascii=False)
            except Exception:
                output = None
        if output is None and result.content:
            try:
                for block in result.content:
                    text = getattr(block, "text", None)
                    if text:
                        output = str(text)
                        break
            except Exception:
                output = None
        if output is None:
            output = str(result)
        # Log tool output (truncated for readability)
        _preview = (output[:800] + "…") if len(output) > 800 else output
        logger.info(f"MCP tool '{name}' returned: {_preview}")
        return output


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
        model_name = os.getenv("model_local") or "amsaravi/medgemma-4b-it:q6"
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
    # Provide tool schema hints with multi-tool planning
    parts = [
        "Plan tool usage before answering. You may call zero, one, or multiple tools.",
        "If multiple tools are needed, plan their order and arguments.",
        "Respond with ONLY a single strict JSON object with keys:",
        "{\"use_tools\": bool, \"tool_plan\": [ {\"tool_name\": string, \"arguments\": object} ], \"reason\": string}",
        "Rules:",
        "- If no tool is needed, return {\"use_tools\": false, \"tool_plan\": [], \"reason\": \"...\"}",
        "- If tools are needed, include each step in order within tool_plan.",
        "- Match each step's arguments to the tool's input schema.",
        "- Return exactly ONE JSON object. No extra text. No multiple JSON objects.",
        "Available tools:"
    ]
    for t in tools[:8]:
        name = t.get("name")
        desc = (t.get("description") or "").strip()
        schema = t.get("inputSchema") or {}
        props = list((schema.get("properties") or {}).keys())
        required = schema.get("required") or []
        parts.append(f"- {name}: {desc} | properties={props} required={required}")
    parts.append("Respond with JSON only. No code fences.")
    return "\n".join(parts)


def _clean_json_like(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _extract_json_objects(text: str) -> List[str]:
    # Extract one or more top-level JSON objects or arrays from text
    objs: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        # find start of object/array
        while i < n and text[i] not in '{[':
            i += 1
        if i >= n:
            break
        start = i
        stack = [text[i]]
        i += 1
        in_str = False
        esc = False
        while i < n and stack:
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch in '{[':
                    stack.append(ch)
                elif ch in '}]':
                    if stack:
                        top = stack[-1]
                        if (top == '{' and ch == '}') or (top == '[' and ch == ']'):
                            stack.pop()
                        else:
                            # mismatched, break
                            stack = []
                            break
            i += 1
        end = i
        if end > start:
            objs.append(text[start:end].strip())
    return objs


def _parse_tool_plan_text(cleaned_raw: str) -> Tuple[List[Dict[str, Any]], str]:
    # Try direct JSON load
    try:
        data = json.loads(cleaned_raw)
    except Exception:
        # Try multiple JSON objects concatenated
        parts = _extract_json_objects(cleaned_raw)
        steps: List[Dict[str, Any]] = []
        reason = ""
        for p in parts:
            try:
                obj = json.loads(p)
                if isinstance(obj, dict):
                    # Legacy single-tool format
                    if "tool_name" in obj or "use_tool" in obj:
                        if obj.get("use_tool") and obj.get("tool_name"):
                            steps.append({
                                "tool_name": obj.get("tool_name"),
                                "arguments": obj.get("arguments") or {},
                            })
                        reason = str(obj.get("reason", reason))
                    # New format with plan list
                    for key in ("tool_plan", "steps", "calls", "tools"):
                        if isinstance(obj.get(key), list):
                            for s in obj[key]:
                                name = s.get("tool_name") or s.get("name")
                                if name:
                                    steps.append({
                                        "tool_name": name,
                                        "arguments": s.get("arguments") or {},
                                    })
                            reason = str(obj.get("reason", reason))
                elif isinstance(obj, list):
                    for s in obj:
                        name = s.get("tool_name") or s.get("name")
                        if name:
                            steps.append({
                                "tool_name": name,
                                "arguments": s.get("arguments") or {},
                            })
            except Exception:
                continue
        return steps, reason
    else:
        steps: List[Dict[str, Any]] = []
        reason = ""
        if isinstance(data, dict):
            # New multi-tool schema
            if isinstance(data.get("tool_plan"), list):
                for s in data["tool_plan"]:
                    name = s.get("tool_name") or s.get("name")
                    if name:
                        steps.append({"tool_name": name, "arguments": s.get("arguments") or {}})
                reason = str(data.get("reason", ""))
            # Legacy single-tool schema
            elif "use_tool" in data:
                if data.get("use_tool") and data.get("tool_name"):
                    steps.append({
                        "tool_name": data.get("tool_name"),
                        "arguments": data.get("arguments") or {},
                    })
                reason = str(data.get("reason", ""))
            # Other alias keys
            else:
                for key in ("steps", "calls", "tools"):
                    if isinstance(data.get(key), list):
                        for s in data[key]:
                            name = s.get("tool_name") or s.get("name")
                            if name:
                                steps.append({
                                    "tool_name": name,
                                    "arguments": s.get("arguments") or {},
                                })
                        reason = str(data.get("reason", ""))
                        break
        elif isinstance(data, list):
            for s in data:
                name = s.get("tool_name") or s.get("name")
                if name:
                    steps.append({"tool_name": name, "arguments": s.get("arguments") or {}})
        return steps, reason


async def plan_tool_usage(llm, user_message: str, tools: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    system = build_tool_planner_prompt(tools)
    logger.info("Requesting tool plan from LLM")
    msg = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user_message),
    ])
    raw = getattr(msg, "content", "")
    cleaned_raw = _clean_json_like(raw)
    steps, reason = _parse_tool_plan_text(cleaned_raw)
    if steps:
        logger.info(f"Planner response -> steps={len(steps)}")
    else:
        logger.info("Planner response -> no tool needed or unparseable; proceeding without tools")
    return steps, reason


async def final_answer(llm, user_message: str, tool_calls: List[ToolCall]) -> str:
    system = (
        "You are a helpful assistant. If tool results are provided, use them to answer succinctly."
    )
    context_lines: List[str] = []
    for i, tc in enumerate(tool_calls, start=1):
        context_lines.append(f"Tool {i}: {tc.name}")
        context_lines.append(f"Arguments: {json.dumps(tc.arguments, ensure_ascii=False)}")
        if tc.result is not None:
            context_lines.append(f"Result: {tc.result}")
    context = "\n".join(context_lines)
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

                # Plan tool usage (multi-step supported)
                steps, _ = await plan_tool_usage(llm, req.message, tools)
                tool_calls: List[ToolCall] = []
                # Execute steps sequentially
                for idx, step in enumerate(steps, start=1):
                    name = step.get("tool_name") or step.get("name")
                    args = step.get("arguments") or {}
                    if not name:
                        continue
                    try:
                        logger.info(f"Executing tool step {idx}/{len(steps)}: {name} with args={args}")
                        result = await call_mcp_tool(mcp_url, name, args)
                        tool_calls.append(ToolCall(name=name, arguments=args, result=result))
                    except Exception as te:
                        logger.error(f"Tool execution failed: {te}")
                        # Stop executing further tools for this attempt
                        tool_calls.append(ToolCall(name=name, arguments=args, result=None))
                        break

                # Get final answer
                answer = await final_answer(llm, req.message, tool_calls)
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
    import socket

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8088"))

    # Get local IP address for network access
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "localhost"

    logger.info(f"Starting API at http://{host}:{port} (network: http://{local_ip}:{port})")
    uvicorn.run("chat_server:app", host=host, port=port, reload=True, log_level="info")
