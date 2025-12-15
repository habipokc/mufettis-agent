"""
Teftiş Agent - LangGraph Implementation (Optimized)
====================================================
Performance optimized version:
- Fast keyword-based routing (no LLM for obvious cases)
- Reduced latency with static responses
- Better error handling
"""

from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.core.config import settings
from backend.app.services.rag_service import query_rag
import re

# Initialize Model - Only when needed (lazy loading concept)
# Using 2.0-flash-lite for faster routing
_llm_lite = None

def get_llm_lite():
    """Lazy load the LLM to avoid startup delays."""
    global _llm_lite
    if _llm_lite is None:
        _llm_lite = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",  # Faster, cheaper model
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            timeout=30  # 30 second timeout
        )
    return _llm_lite


class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    sources: list[dict]


# === KEYWORD PATTERNS FOR FAST ROUTING ===

CHITCHAT_PATTERNS = [
    "merhaba", "selam", "günaydın", "iyi günler", "iyi akşamlar",
    "nasılsın", "naber", "kimsin", "adın ne", "ne yaparsın",
    "teşekkür", "sağol", "eyvallah", "hoşça kal", "görüşürüz",
    "yardım et", "help"
]

SEARCH_KEYWORDS = [
    "madde", "kanun", "yönetmelik", "tebliğ", "bddk", "tcmb", "spk",
    "banka", "kredi", "mevduat", "sermaye", "risk", "denetim",
    "müfettiş", "teftiş", "audit", "compliance", "uyum",
    "faiz", "kur", "swap", "türev", "aktif", "pasif",
    "likidite", "syr", "nedir", "nasıl", "açıkla", "tanımla",
    "hesapla", "oran", "limit"
]


def fast_route(text: str) -> str:
    """
    Fast keyword-based routing without LLM call.
    Returns: 'chitchat', 'search', or 'unknown'
    """
    lower_text = text.lower().strip()
    words = lower_text.split()
    
    # Very short messages with greetings = chitchat
    if len(words) <= 3:
        for pattern in CHITCHAT_PATTERNS:
            if pattern in lower_text:
                return "chitchat"
    
    # Any banking/law keyword = search
    for keyword in SEARCH_KEYWORDS:
        if keyword in lower_text:
            return "search"
    
    # Question marks with more than 3 words likely a search
    if "?" in text and len(words) > 3:
        return "search"
    
    # Default for longer messages without clear intent
    if len(words) > 5:
        return "search"  # Assume it's a question
    
    return "unknown"


# === STATIC RESPONSES ===

STATIC_RESPONSES = {
    "greeting": "Merhaba! Ben Teftiş Agent. Bankacılık mevzuatı, BDDK düzenlemeleri ve denetim süreçleri hakkında size nasıl yardımcı olabilirim?",
    "thanks": "Rica ederim! Başka bir sorunuz olursa yardımcı olmaktan memnuniyet duyarım.",
    "identity": "Ben Teftiş Agent, banka müfettiş yardımcıları için geliştirilmiş bir yapay zeka asistanıyım. Mevzuat sorularınızı yanıtlayabilirim.",
    "help": "Size şu konularda yardımcı olabilirim:\n• Bankacılık mevzuatı (kanunlar, yönetmelikler)\n• BDDK ve TCMB düzenlemeleri\n• Denetim süreçleri\n• Finansal terimler ve hesaplamalar\n\nSorunuzu yazmanız yeterli!"
}


def get_static_response(text: str) -> str | None:
    """Return static response if applicable, None otherwise."""
    lower = text.lower().strip()
    
    # Greetings
    if any(g in lower for g in ["merhaba", "selam", "günaydın", "iyi günler", "iyi akşamlar"]):
        if len(lower.split()) <= 4:
            return STATIC_RESPONSES["greeting"]
    
    # Thanks
    if any(t in lower for t in ["teşekkür", "sağol", "eyvallah"]):
        return STATIC_RESPONSES["thanks"]
    
    # Identity questions
    if any(i in lower for i in ["kimsin", "adın ne", "sen ne"]):
        return STATIC_RESPONSES["identity"]
    
    # Help
    if lower in ["yardım", "help", "?"]:
        return STATIC_RESPONSES["help"]
    
    return None


# === NODES ===

def router_node(state: AgentState):
    """Fast routing with keyword matching, LLM only as fallback."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 1. Try fast keyword-based routing
    intent = fast_route(last_message)
    
    if intent != "unknown":
        print(f"[Router] Fast route: {intent}")
        return {"intent": intent}
    
    # 2. Fallback: Use LLM for ambiguous cases (rare)
    print("[Router] Using LLM fallback...")
    try:
        llm = get_llm_lite()
        router_prompt = f"""Classify this message as "chitchat" or "search".
chitchat = greetings, small talk, off-topic
search = banking, laws, regulations, financial terms

Message: {last_message}
Class:"""
        
        response = llm.invoke(router_prompt)
        result = response.content.strip().lower()
        intent = "search" if "search" in result else "chitchat"
        print(f"[Router] LLM decided: {intent}")
        return {"intent": intent}
        
    except Exception as e:
        print(f"[Router] Error: {e}, defaulting to search")
        return {"intent": "search"}


def chitchat_node(state: AgentState):
    """Handle chitchat with static responses when possible."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 1. Try static response first (instant, no API call)
    static = get_static_response(last_message)
    if static:
        print("[Chitchat] Using static response")
        return {"messages": [AIMessage(content=static)], "sources": []}
    
    # 2. Use LLM for complex chitchat (rare)
    print("[Chitchat] Using LLM")
    try:
        llm = get_llm_lite()
        system = SystemMessage(content="""Sen "Teftiş Agent" adında profesyonel bir asistansın.
Bankacılık mevzuatı konusunda uzmanlaşmışsın. Kısa ve net cevaplar ver.""")
        
        response = llm.invoke([system, messages[-1]])
        return {"messages": [response], "sources": []}
        
    except Exception as e:
        print(f"[Chitchat] Error: {e}")
        return {
            "messages": [AIMessage(content="Şu an yoğunluk var. Mevzuat sorunuzu yazarsanız yanıtlamaya hazırım.")],
            "sources": []
        }


def retrieval_node(state: AgentState):
    """Execute RAG pipeline."""
    messages = state["messages"]
    query = messages[-1].content
    
    print(f"[RAG] Processing query: {query[:50]}...")
    
    result = query_rag(query, n_results=5)
    
    answer = result.get("answer", "Bir hata oluştu.")
    sources = result.get("sources", [])
    
    print(f"[RAG] Got {len(sources)} sources")
    
    return {"messages": [AIMessage(content=answer)], "sources": sources}


# === GRAPH ===

workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("chitchat", chitchat_node)
workflow.add_node("search", retrieval_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    lambda state: state["intent"],
    {"chitchat": "chitchat", "search": "search"}
)

workflow.add_edge("chitchat", END)
workflow.add_edge("search", END)

app = workflow.compile()
