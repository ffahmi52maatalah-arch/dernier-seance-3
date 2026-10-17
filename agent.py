import ast
import operator
import os

from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel

try:  # LangChain 1.x
    from langchain.agents import create_agent as _create_agent
except ImportError:  # older versions: use LangGraph's prebuilt ReAct agent
    from langgraph.prebuilt import create_react_agent as _create_agent

# Local model served by Ollama. It must support tool calling
# (e.g. llama3.1, llama3.2, qwen2.5, mistral-nemo). Pull it first: `ollama pull llama3.1`
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.1"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,
)

# ---- Tools -----------------------------------------------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression, e.g. '2 * (3 + 4) ** 2'."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


tools = [calculator]

# Web search is enabled only if a SerpAPI key is configured
if os.getenv("SERPAPI_API_KEY"):
    from langchain_community.utilities import SerpAPIWrapper

    _search = SerpAPIWrapper()

    @tool
    def web_search(query: str) -> str:
        """Search the web for current information."""
        return _search.run(query)

    tools.append(web_search)

# ---- Agent -----------------------------------------------------------------

_graph = _create_agent(llm, tools)


class AgentInput(BaseModel):
    input: str


class AgentOutput(BaseModel):
    output: str


def _run(inp) -> dict:
    text = inp["input"] if isinstance(inp, dict) else inp.input
    result = _graph.invoke({"messages": [("user", text)]})
    content = result["messages"][-1].content
    if isinstance(content, list):  # some models return content blocks
        content = "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    return {"output": content}


# Same interface as before: {"input": "..."} -> {"output": "..."}
agent = RunnableLambda(_run).with_types(input_type=AgentInput, output_type=AgentOutput)
