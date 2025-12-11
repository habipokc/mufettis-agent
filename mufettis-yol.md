## 1) Proje Vizyonu ve Hedefler (Kısa)

- Kullanıcının bankacılık denetim ve mevzuat PDF’lerini sorgulayabileceği bir web uygulaması.
- PDF’lerden structure-aware (tablo, madde, dipnot, formül ayrımı) chunk’lar oluşturulacak.
- İşlem hattı:
  - Embedding → Vector DB  
  - Hybrid retrieval (sparse + dense)  
  - Re-rank  
  - Model (gemini-2.5-flash) ile cevap üretimi
- Agent katmanı özellikleri:
  - Tablo okuma
  - Çapraz referans
  - Mevzuat açıklama
  - Compliance-check
- Başlangıçta ücretsiz araçlar kullanılacak; ileride ölçeklenebilir bulut hizmetlerine kolay geçiş sağlanacak.


## 2) Genel Mimari (Bileşenler)

[PDFs]  
   ↓ *extraction*  
[Extractor / Normaliser: unstructured | pdfminer | layoutparser]  
   ↓ *chunking*  
[Chunker (structure-aware)]  
   ↓ *embedding*  
[Gemini Embeddings] → [Vector DB (Chroma, local)]  
   ↓ *retrieval*  
[Retrieval + Reranker (flash-lite)]  
   ↓  
[RAG + Agent Layer: LangChain / LlamaIndex]  
   ↓  
[LLM: gemini-2.5-flash]  
   ↓  
[Backend API: FastAPI]  
   ↓  
[Frontend: Next.js] → **User**

**Ayrıca:**  
- CI/CD  
- Logging & Metrics (Prometheus veya basit logging)  
- Authentication (başta yok / basit token)  
- Privacy (PDF’ler local, public exposure yok)


## 3) Ön Koşullar — Neyi Hazır Etmelisin

- **Bilgisayar:**  
  - windows11

- **Python 3.10+**  
  - poetry ve uv birlikte 

- **Node.js (v18+)**

- **GitHub hesabı**  
  - Repository oluşturmak / versiyon kontrolü için
  - github desktop ile birlikte.

- **Google (Gemini) API erişimi**  
  - Free-tier için API anahtarı  
  - Eğer yoksa: open-source embedding için fallback mekanizması kullanılacak

- **Disk alanı:**  
  - PDF başına yaklaşık **25–30 MB × dosya sayısı**  
  - Yerel depolama yeterli


## 4) 12 Haftalık Yol Haritası  
Her hafta **Amaç**, **Adımlar / Görevler**, **Çıktı (Deliverable)** formatındadır.

---

### **Week 1 — Sprint 0: Hazırlık & İnceleme**

**Amaç:**  
Proje reposunu, geliştirme ortamını ve ilk örnek PDF’leri hazırlamak.  
Extraction kütüphanelerini deneyip ilk ham veri çıktısını almak.

**Adımlar / Görevler:**  
- GitHub’da proje reposu oluştur  
- Python virtualenv kur ve temel kütüphaneleri yükle  
- 3–5 örnek PDF seç  
  - Çeşitlilik: tablo, madde, dipnot, formül içeren dosyalar  
- `unstructured` / `pdfminer` ile temel extraction testleri yap  

**Çıktı (Deliverable):**  
- GitHub repo  
- `data/raw/` klasöründe örnek PDF’ler  
- `notebooks/pdf_extraction.ipynb` (veya eşdeğer `scripts/` altında bir script)  
- İlk text/json extraction çıktıları



### Week 2 — Sprint 1: Structure-aware Extraction & Baseline Parsing

**Amaç:**  
Tablo, madde, formül, dipnot gibi block-level segmentation yapabilen bir extraction pipeline kurmak.

**Adımlar / Görevler:**  
- `unstructured` veya `pdfplumber` / `pdfminer` ile block-level extraction  
- (Opsiyonel) `layoutparser` ile sayfa layout analizi dene  
- Çıktıları block-level **JSON** formatında kaydet  

**Çıktı (Deliverable):**  
- `data/parsed/` içinde JSON blok dosyaları  
- `scripts/parse_pdf.py`

---

### Week 3 — Sprint 2: Chunking Kurallarının Otomatikleştirilmesi

**Amaç:**  
Belirlenen kurallara göre chunker geliştirmek  
(tabı = tek chunk, madde = tek chunk, dipnot = low-priority chunk gibi).

**Adımlar / Görevler:**  
- `chunker.py` implementasyonu  
  - `block.type` tespiti (table / article / footnote / formula)  
  - chunk id oluşturma  
  - metadata ekleme  
  - source page bilgisinin eklenmesi  
- Lokal test: 10 PDF üzerinden chunk üretimi  

**Çıktı (Deliverable):**  
- `data/chunks/` içinde JSONL (her satır bir chunk)  
- `scripts/chunk_preview.ipynb`


### Week 4 — Sprint 3: Embedding Pipeline (Gemini Preferred, Fallback OSS)

**Amaç:**  
Chunk’ları embedding’e dönüştürmek ve vector DB’ye yüklemek (Chroma lokal).

**Adımlar / Görevler:**  
- Gemini embedding API çağrısı örneği (veya OSS BGE-m3/E5 fallback)  
- Chroma lokal kurulumu ve Python client ile bağlantı  
- Basit retrieval testi (cosine similarity)

**Çıktı (Deliverable):**  
- `vector_db/` (Chroma index)  
- `scripts/embed_and_index.py`

**Örnek Kod (pseudo):**

```python
# embed_and_index.py (özet)
from chromadb import Client
from gemini_api import embed_text

client = Client()
collection = client.create_collection("bank_mevzuat")

for chunk in load_chunks("data/chunks/*.jsonl"):
    emb = embed_text(chunk["content"])  # Gemini embeddings
    collection.add(
        documents=[chunk["content"]],
        metadatas=[chunk["meta"]],
        embeddings=[emb]
    )
```


### Week 5 — Sprint 4: Retrieval + Hybrid Search (Dense + Sparse)

**Amaç:**  
Dense retrieval (embeddings) ve basit BM25 sparse retrieval kombinasyonunu kurmak.

**Adımlar / Görevler:**  
- Basit BM25 kurulumu (Whoosh / rank_bm25)  
- Hybrid retriever implementasyonu:  
  - Sorgu → BM25 topK + Dense topK → union → rerank  
- Rerank için küçük model veya `gemini-flash-lite` kullanımı

**Çıktı (Deliverable):**  
- `scripts/hybrid_retriever.py`  
- Örnek query notebook

---

### Week 6 — Sprint 5: RAG Chain & Prompt Engineering

**Amaç:**  
Context packing, prompt template ve model çağrısı (`gemini-2.5-flash`) ile RAG cevap üretmek.

**Adımlar / Görevler:**  
- Context selection: topN chunks → context window packer (truncate smart)  
- Prompt templates: instruction + context + question  
- Safety / attribution: prompt içine sources ekle

**Çıktı (Deliverable):**  
- `scripts/rag_query.py`  
- Örnek promptlar

**Örnek Prompt Şablonu:**

```text
You are a compliance assistant. Use the context below (numbered) to answer precisely.

Context:
[1] <chunk 1>
[2] <chunk 2>
...

Question: <user question>
Answer briefly. At the end, list the sources as: (source: file_page_chunkid)
```

### Week 7 — Sprint 6: Agent Layer (LangChain / LlamaIndex)

**Amaç:**  
Basit agent’lar geliştirmek:  
- `explain_clause_agent`  
- `table_agent`  
- `xref_agent`

**Adımlar / Görevler:**  
- LangChain agent: tools tanımla (retriever, table_parser, cite_tool)  
- Test senaryoları:  
  - “Madde 56’yı sadeleştir”  
  - “Bu tabloda hangi tarihte ... ?”

**Çıktı (Deliverable):**  
- `agents/` klasörü  
- Örnek agent senaryoları

---

### Week 8 — Sprint 7: Backend API (FastAPI) + Local Deployment

**Amaç:**  
RAG + agent pipeline’ını FastAPI içine entegre etmek, temel auth ve rate limit eklemek.

**Adımlar / Görevler:**  
- FastAPI endpoint’leri:  
  - `/ask`, `/explain`, `/search`, `/upload-pdf` (opsiyonel)  
- Dockerfile yaz ve local test et  
- Logging (file + console)

**Çıktı (Deliverable):**  
- `backend/` (FastAPI app)  
- `Dockerfile`  
- `docker-compose.yml` (Chroma + backend)

**Örnek Endpoint:**

```python
@app.post("/ask")
async def ask(q: Query):
    retrieved = hybrid_retriever(q.text)
    answer = rag_chain(query=q.text, contexts=retrieved)
    return {"answer": answer, "sources": retrieved.meta}
```

### Week 9 — Sprint 8: Frontend MVP (Next.js)

**Amaç:**  
Kullanıcı arayüzü oluşturmak: sorgu kutusu, sonuç gösterimi ve kaynak gösterimi.

**Adımlar / Görevler:**  
- Next.js + Tailwind ile temel UI  
- Components:  
  - `QueryBox`  
  - `ResultsList`  
  - `SourcePanel`  
  - `UploadPage` (opsiyonel)  
- FastAPI ile bağlantı (fetch / Axios)

**Çıktı (Deliverable):**  
- `frontend/` içinde deploy edilebilir MVP

---

### Week 10 — Sprint 9: Test, UX Düzeltmeleri, Demo Hazırlığı

**Amaç:**  
Son kullanıcı akışlarını test etmek, hataları gidermek ve demo hazırlamak.

**Adımlar / Görevler:**  
- Backend unit tests (pytest)  
- Integration tests (Playwright / basic Selenium)  
- Kullanıcı senaryoları testleri:  
  - “Kanun maddesi sorgula”  
  - “Tabloyu getir”

**Çıktı (Deliverable):**  
- Test raporu  
- Demo video (30–60 s)

---

### Week 11 — Sprint 10: LinkedIn Lansman & Geri Bildirim Toplama

**Amaç:**  
MVP’yi LinkedIn’de paylaşmak, kullanıcılardan geri bildirim toplamak ve issue’ları önceliklendirmek.

**Adımlar / Görevler:**  
- Demo post hazırlama  
- Kısa video veya GIF  
- Kullanım örnekleri  
- Feedback form (Typeform / Google Forms)

**Çıktı (Deliverable):**  
- Paylaşım materyalleri  
- Toplanan geri bildirimler

---

### Week 12 — Sprint 11: Mobil Hazırlık & Roadmap Güncelleme

**Amaç:**  
Mobil kullanım için API optimizasyonu ve offline seçenek planlama.

**Adımlar / Görevler:**  
- Backend optimizasyon: caching (Redis), pagination  
- Mobil UI prototip (Figma / Flutter skeleton)  
- Mobil için Chroma → Pinecone / Weaviate geçiş planı (opsiyonel)

**Çıktı (Deliverable):**  
- Mobil tech spec  
- Önceliklendirilmiş task listesi


## 5) Her Aşama İçin Teknik Detaylar & Örnek Komutlar  
### (Windows + Poetry + UV uyumlu)

---

## 🔧 Ortam Kurulumu (Windows + Poetry + uv)

### ✔ Git Repo Oluşturma
```powershell
git init mufettis-agent
cd mufettis-agent

#Poetry ile proje başlat
poetry init -n

#Poetry sanal ortam oluşturma
poetry env use python

# uv ile paket yükleme 
uv pip install unstructured pdfminer.six chromadb fastapi uvicorn langchain openai requests
```

## unstructured ile basit extraction (örnek)
```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf(filename="data/raw/example.pdf")
# elements -> block-level items: Title, Table, List, etc.
```

## Chroma Local Quickstart (Python)
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection(name="bank_mevzuat")

collection.add(
    documents=["metin1", "metin2"],
    metadatas=[{"source": "a"}, {"source": "b"}],
    embeddings=[[0.1, ...], [0.2, ...]]
)
```

## Gemini Embedding (Pseudo / HTTP Çağrısı)
##### Not: Gerçek kullanacağın Google API SDK/endpoint’i farklı olabilir. Bu yalnızca iskelet.
```python
import requests

API_KEY = "YOUR_GEMINI_KEY"

def embed_text(text):
    resp = requests.post(
        "https://api.google.com/v1/embeddings",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "gemini-embedding-2.5",
            "input": text
        }
    )
    return resp.json()["data"][0]["embedding"]
```

## FastAPI Minimal Örnek
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    q: str

@app.post("/ask")
def ask(q: Query):
    # 1) retrieve
    # 2) rag chain
    # 3) return
    return {"answer": "sample", "sources": []}
```

## LangChain Agent – Örnek Araç Yapısı (Pseudo)
```python
from langchain import AgentExecutor, Tool

def table_tool(table_chunk):
    # parse table, run analytic, return string
    return "table summary"

tools = [
    Tool(
        name="table_tool",
        func=table_tool,
        description="Parses a table chunk"
    )
]

agent = AgentExecutor.from_tools_and_llm(tools, llm)
```

## 6) Chunking & Normalizasyon Kuralları (Detaylı) — Kopyala-Yapıştır Uygulanabilir

### A) Genel Sınıflar
- `table`
- `article` (madde, fıkra)
- `paragraph` (açıklayıcı normal paragraf)
- `formula` (formül / format)
- `footnote` (dipnot)
- `toc` (içindekiler) — **ignore edilir**

---

### B) Kurallar (Kod-Uygulama Mantığı)

#### 1) Tablo blokları
- Eğer blok bir **tablo** ise → **tek bir table chunk** oluştur.
- Metadata örneği:  
  `{"type": "table", "rows": n, "cols": m, "page": p}`

#### 2) Madde blokları (“MADDE X – (1) …”)
- Format regex: `^MADDE\s+\d+`
- Bu blok → **article chunk**
- Madde numarası ayrıca metadata’ya eklenir.

#### 3) Başlık + çok kısa satırlar (liste yapısı)
- Eğer blok:  
  - bir başlıktan oluşuyorsa  
  - altında 3–6 satır kısa maddeler varsa  
- → **paragraph chunk** ve gerektiğinde 3–6 satırlık bölümlere ayrılabilir.

#### 4) Dipnotlar
- Bir sayfada/alt bölümdeki tüm dipnotlar → **tek footnote chunk**
- Metadata: `{"type": "footnote", "priority": "low"}`

#### 5) İçindekiler (TOC)
- TOC blokları → **işleme dahil edilmez (skip)**

#### 6) Overlap Kuralları
- `paragraph` / `article` → **20 token overlap**
- `table` / `formula` → **0 overlap**

---

### C) Chunk JSON Örneği

```json
{
  "id": "pdf3_p12_chunk5",
  "type": "table",
  "title": "Yönetmeliğin Yayımlandığı Resmi Gazete Bilgileri",
  "content": [
    ["Tarih", "Sayısı"],
    ["1/11/2006", "26333"],
    ["9/6/2009", "27253"]
  ],
  "meta": { "source": "pdf3", "page": 12 }
}
```

## 7) Vector DB & Embedding Seçimi — Öneri ve Fallback

### Önerilen Kombinasyon (Ücretsiz / En Verimli)
- **Embeddings:** Gemini Embedding (free-tier, Türkçe için yüksek performans)
- **Vector DB:** ChromaDB (local, tamamen ücretsiz, hızlı prototipleme)

### Fallback (API yoksa / kota dolduysa)
- **Embedding:** E5 veya BGE-m3 (open-source modeller)
- **DB:** LanceDB veya lokal FAISS + basit metadata store

### Indexleme Stratejisi
- Her chunk → tek doküman (id, content, meta, embedding)
- Ek metadata:
  - `priority` (normal / high / low)
  - `type`
  - `date`
  - `file_id`
- Source attribution:
  - Sorgu yanıtında mutlaka kaynak listesi döndürülmeli.

---

## 8) Agent Katmanı — Görevler & Nasıl Kurulur

### Temel Agent’lar
- **ExplainAgent:** Madde/kanun sadeleştirme, örnek üretme  
- **TableAgent:** Tabloyu parse etme, özetleme, satır/kolon karşılaştırma  
- **XRefAgent:** Çapraz referans takibi (madde → başka madde)  
- **ComplianceAgent:** Basit check-list esaslı uygunluk kontrolü

### Nasıl Bağlanır? (Örnek Akış)
1. Kullanıcı soruyu gönderir  
2. Intent classifier (heuristic veya LLM) → ilgili agent seçilir  
3. Agent kendi retrieval çağrısını yapar  
4. Model çıktıyı işler  
5. Yanıt + kaynak listesi döner

---

## 9) Web MVP — Frontend & Backend Entegrasyonu (Detay)

### Backend (FastAPI) — Endpoints
- **POST /ask** → Soru alır, cevap + kaynaklar döner  
- **POST /upload** (opsiyonel) → PDF alır, parsing pipeline başlatır  
- **GET /status** → Health check

### Frontend (Next.js) — Sayfalar
- `/` → Giriş + arama kutusu  
- `/results` → Cevap + kaynaklar + open source view  
- `/upload` → PDF yükleme (opsiyonel)  
- `/demo` → Hazır demo senaryoları

### CORS / Güvenlik
- Local test: `CORS("*")` kabul edilebilir  
- Production: origin whitelist zorunlu

---

## 10) Test, Kalite Güvencesi ve Güvenlik Checklist’i

### Testler
- **Unit test:** chunker, embedding wrapper, retriever  
- **Integration test:** ask → retrieval → model → answer  
- **Manual user tests:** 20 farklı soru tipi  
  - tablo  
  - madde/fıkra  
  - dipnot  
  - cross-reference

### Güvenlik & GDPR Benzeri Önlemler
- PDF’leri public bir bucket’a koyma; yerel veya private storage kullan  
- Loglar: PII içermesin / maskeleme yap  
- API anahtarları `.env` dosyasında olmalı; repoya commit edilmemeli

---

## 11) LinkedIn Demo & Lansman Adımları (Kısa)

### Gerekenler
- Hazır demo screenshot’ı  
- 30 saniyelik demo videosu (sorgu → sonuç)  
- Kısa post  
- Demo link (kısıtlı erişim; demo hesap)

### Call to Action
- “Geri bildirim verin; hangi özellikler önemli?”

### Örnek LinkedIn Metni
Yeni bir side-project: Türkiye bankacılık mevzuatı üzerine RAG tabanlı bir arama motoru geliştirdim. PDF’leri yükleyip doğal dil ile sorup maddeleri, tabloları, dipnotları hızlıca bulabilirsiniz. Demo: [link]. Geri bildirim ve istekler için mesaj atın!

---

## 12) Mobil Geçiş — Mimari & Öncelikler

### Mimari
- Backend (FastAPI) aynı kalır → mobil sadece API tüketir.

### Teknoloji
- Flutter (tek kod tabanı iOS+Android)  
- Alternatif: React Native

### Gereksinimler
- **Offline:** küçük subset embedding + Chroma lokal on-device (zor, başlangıçta yok)  
- **Push Notifications:** sonuç güncellemeleri için  
- **UI:** Query, Results, Sources, Bookmark, Compare

---

## 13) Uzun Vadeli İyileştirme & Üretime Alma Notları

- Vector DB Cloud: Pinecone / Weaviate — ölçek ihtiyacında geçiş planı  
- Embedding & model maliyetleri artarsa:  
  - batch embedding  
  - caching  
  - token optimizasyonu  
- Monitoring:  
  - request latency  
  - error rate  
  - hallucination metric (manuel değerlendirme)  
- Hukuki uyumluluk:  
  - veri saklama süresi  
  - erişim loglaması


## 14) Ek — Proje Klasör Yapısı (Öneri)

```text
mufettis-agent/
├─ data/
│  ├─ raw/
│  ├─ parsed/
│  └─ chunks/
├─ backend/
│  ├─ app/
│  ├─ Dockerfile
│  └─ requirements.txt
├─ frontend/
│  └─ nextjs-app/
├─ agents/
├─ scripts/
│  ├─ parse_pdf.py
│  ├─ chunker.py
│  └─ embed_and_index.py
├─ notebooks/
├─ tests/
├─ README.md
└─ docs/
```