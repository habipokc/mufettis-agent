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

# Initialize Model Factory
def create_llm_lite(api_key: str):
    """Create LLM client with user provided key."""
    if not api_key:
        raise ValueError("API Key is missing")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.2,
        timeout=30
    )


class AgentState(TypedDict, total=False):
    """The state of the agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    sources: list[dict]
    api_key: str # User provided API Key


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
    "greeting": "Merhaba! Ben Müfettiş Agent. Bankacılık mevzuatı, BDDK düzenlemeleri ve denetim süreçleri hakkında size nasıl yardımcı olabilirim?",
    "thanks": "Rica ederim! Başka bir sorunuz olursa yardımcı olmaktan memnuniyet duyarım.",
    "identity": "Ben Müfettiş Agent, banka müfettiş yardımcıları için geliştirilmiş bir yapay zeka asistanıyım. Mevzuat sorularınızı yanıtlayabilirim.",
    "help": "Size şu konularda yardımcı olabilirim:\n• Bankacılık mevzuatı (kanunlar, yönetmelikler)\n• BDDK ve TCMB düzenlemeleri\n• Denetim süreçleri\n• Finansal terimler ve hesaplamalar\n\nSorunuzu yazmanız yeterli!",
    "howru": "İyiyim, teşekkür ederim! Bankacılık mevzuatı hakkında sorularınızı yanıtlamaya hazırım. Size nasıl yardımcı olabilirim?",
    "goodbye": "Görüşmek üzere! Başka sorularınız olduğunda yine beklerim.",
    "capability": "Ben bankacılık mevzuatı konusunda uzmanlaşmış bir yapay zeka asistanıyım. BDDK yönetmelikleri, kanunlar, tebliğler ve denetim süreçleri hakkında sorularınızı yanıtlayabilirim."
}


def get_static_response(text: str) -> str | None:
    """Return static response if applicable, None otherwise."""
    lower = text.lower().strip()
    words = lower.split()
    
    # Greetings (short messages only)
    if any(g in lower for g in ["merhaba", "selam", "günaydın", "iyi günler", "iyi akşamlar"]):
        if len(words) <= 4:
            return STATIC_RESPONSES["greeting"]
    
    # How are you questions
    if any(h in lower for h in ["nasılsın", "nasıl gidiyor", "naber", "ne haber", "iyi misin"]):
        return STATIC_RESPONSES["howru"]
    
    # Thanks
    if any(t in lower for t in ["teşekkür", "sağol", "eyvallah"]):
        return STATIC_RESPONSES["thanks"]
    
    # Identity questions
    if any(i in lower for i in ["kimsin", "adın ne", "sen ne", "ne yaparsın", "nesin"]):
        return STATIC_RESPONSES["identity"]
    
    # Capability questions
    if any(c in lower for c in ["neler yapabilirsin", "ne bilirsin", "yeteneklerin"]):
        return STATIC_RESPONSES["capability"]
    
    # Goodbye
    if any(b in lower for b in ["hoşça kal", "görüşürüz", "bye", "güle güle"]):
        return STATIC_RESPONSES["goodbye"]
    
    # Help
    if lower in ["yardım", "help", "?"]:
        return STATIC_RESPONSES["help"]
    
    return None


# === NODES ===

def router_node(state: AgentState):
    """Fast routing with keyword matching, LLM only as fallback."""
    messages = state["messages"]
    last_message = messages[-1].content
    api_key = state.get("api_key", settings.GEMINI_API_KEY) # Fallback to settings if empty
    
    # 1. Try fast keyword-based routing
    intent = fast_route(last_message)
    
    if intent != "unknown":
        print(f"[Router] Fast route: {intent}")
        return {"intent": intent}
    
    # 2. Fallback: Use LLM for ambiguous cases (rare)
    print("[Router] Using LLM fallback...")
    try:
        llm = create_llm_lite(api_key)
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
    api_key = state.get("api_key", settings.GEMINI_API_KEY)

    # 1. Try static response first (instant, no API call)
    static = get_static_response(last_message)
    if static:
        print("[Chitchat] Using static response")
        return {"messages": [AIMessage(content=static)], "sources": []}
    
    # 2. Use LLM for complex chitchat (rare)
    print("[Chitchat] Using LLM")
    try:
        llm = create_llm_lite(api_key)
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
    api_key = state.get("api_key", settings.GEMINI_API_KEY)
    
    print(f"[RAG] Processing query: {query[:50]}...")
    
    # Pass api_key to RAG service
    result = query_rag(query, api_key=api_key, n_results=5)
    
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
