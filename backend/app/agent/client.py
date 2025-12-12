"""
Teftiş Agent - LangGraph Implementation
=======================================
Orchestrates the conversation flow:
1. Route User Input -> (Chitchat | RAG)
2. Chitchat -> Gemini 2.5 Flash Lite (Persona)
3. RAG -> Gemini 2.5 Flash + Tool Calling (Existing Service)
"""

from typing import Annotated, Literal, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.core.config import settings
from backend.app.services.rag_service import query_rag

# Initialize Models
# Lite for Router & Chitchat (Fast, Cheap)
llm_flash_lite = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", # Or closest available Lite
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3
)

# Flash for RAG (Smart)
# We already assume rag_service uses Flash internally, but we might wrap it here if needed.

class AgentState(TypedDict):
    """The state of the agent, holding the conversation history."""
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    sources: list[dict] # To hold RAG sources

# === NODES ===

def router_node(state: AgentState):
    """
    Analyzes the last message to decide correctly:
    - 'chitchat': Greetings, 'how are you', off-topic, identity questions.
    - 'search': Questions about banking, laws, regulations, definitions, etc.
    """
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Simple heuristic + lightweight LLM check could go here.
    # For speed, let's use a very focused prompt with Lite.
    
    router_prompt = f"""
    Sen bir yönlendirme asistanısın. Kullanıcı mesajını analiz et.
    Sadece iki sınıftan birini döndür: "chitchat" veya "search".
    
    KURALLAR:
    - "Merhaba", "Nasılsın", "Sen kimsin", "Adın ne" -> "chitchat"
    - "Kredi limiti nedir", "BDDK yönetmeliği", "Madde 8", "Faiz oranı", "Denetim süreci" -> "search"
    - Bankacılık, finans, hukuk, mevzuat ile ilgili her şey -> "search"
    
    MESAJ: {last_message}
    SINIF:"""
    
    try:
        response = llm_flash_lite.invoke(router_prompt)
        intent = response.content.strip().lower()
    except Exception as e:
        # Fallback to search if routing fails (often safer) or just log
        print(f"Router Error: {e}")
        # Check for 503 specifically
        if "503" in str(e):
             # Let it bubble up or handle? For now, let's treat it as chitchat or bubble up.
             # Actually, better to bubble up so frontend sees 503, OR return a special error message.
             raise e 
        return {"intent": "search"} # Default fallback
    
    if "search" in intent:
        return {"intent": "search"}
    return {"intent": "chitchat"}


def chitchat_node(state: AgentState):
    """Handles general conversation using the Persona."""
    messages = state["messages"]
    
    system_prompt = SystemMessage(content="""
    Sen "Teftiş Agent" adında bir yapay zeka asistanısın.
    Görevin: Banka müfettiş yardımcılarına ve denetçilere mevzuat konularında yardımcı olmak.
    Kişiliğin: Profesyonel, yardımsever, net ve güvenilir.
    
    Kullanıcı sana bankacılık dışı veya sohbet amaçlı yazdığında (merhaba, nasılsın vb.) bu kişiliğe uygun cevap ver.
    "Nasıl yardımcı olabilirim?", "Hangi mevzuatı araştırıyoruz?" gibi yönlendirici sorular sor.
    """)
    
    # Filter only last few messages for context window if needed
    response = llm_flash_lite.invoke([system_prompt] + messages[-5:])
    
    return {"messages": [response], "sources": []}


def retrieval_node(state: AgentState):
    """Executes RAG Pipeline for specific questions."""
    messages = state["messages"]
    query = messages[-1].content
    
    # Call existing RAG service
    # Note: query_rag returns a dict {answer, sources, context...}
    # We need to format this into an AI Message.
    
    result = query_rag(query, n_results=5)
    
    answer_text = result.get("answer", "Bir hata oluştu.")
    sources = result.get("sources", [])
    
    # Appending source info is already handled by Gemini in rag_service prompt mostly,
    # but let's Ensure distinct source list if UI needs it.
    # For now, we return the text result as the message.
    # In a full agent, we might return structured output.
    
    return {"messages": [AIMessage(content=answer_text)], "sources": sources}

# === GRAPH BUILDER ===

workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("chitchat", chitchat_node)
workflow.add_node("search", retrieval_node)

workflow.set_entry_point("router")

def route_decision(state: AgentState):
    return state["intent"]

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "chitchat": "chitchat",
        "search": "search"
    }
)

workflow.add_edge("chitchat", END)
workflow.add_edge("search", END)

app = workflow.compile()
