# SyncResearch

A self-hosted RAG (Retrieval-Augmented Generation) system for analyzing and querying academic research papers locally with complete data privacy.

## ✨ Features

- 📄 **PDF Analysis** - Upload and query research papers using natural language
- 🔍 **Semantic Search** - Vector-based similarity search across documents
- 🤖 **Local LLM** - Self-hosted Llama 3.1 8B via vLLM (no API costs)
- 🔒 **Complete Privacy** - All data and processing stays on your hardware
- 💾 **Persistent Storage** - MinIO (S3-compatible) + ChromaDB vector database
- 🌐 **Modern UI** - Clean React interface with real-time health monitoring

## 🚀 Quick Start

### Prerequisites

- NVIDIA GPU (tested on RTX 3090, 24GB VRAM)
- Docker with NVIDIA Container Runtime
- Node.js 20+
- Python 3.10+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/SyncResearch.git
cd SyncResearch
```

2. **Set up Python environment**
```bash
python -m venv rrenv
source rrenv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your MinIO credentials
```

4. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

### Running the System

**Start all services:**

```bash
# 1. Start vLLM server (loads Llama 3.1 8B)
cd vllm-server
make llama31

# 2. Start FastAPI backend (in new terminal)
cd ..
source rrenv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080

# 3. Start React frontend (in new terminal)
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8080/docs
- vLLM: http://localhost:8000

## 📖 Usage

1. **Upload a research paper** - Click "Upload PDF" and select a paper
2. **Wait for processing** - The system extracts structure and creates embeddings
3. **Ask questions** - Type queries like:
   - "What is the main contribution of this paper?"
   - "Explain the methodology used"
   - "What are the key results?"
4. **View sources** - See which paper sections informed the answer

## 🛠️ Tech Stack

**Backend:**
- [vLLM](https://github.com/vllm-project/vllm) - High-performance LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Docling](https://github.com/DS4SD/docling) - PDF structure extraction
- [MinIO](https://min.io/) - S3-compatible object storage

**Frontend:**
- [React](https://react.dev/) - UI framework
- [Vite](https://vitejs.dev/) - Build tool
- [Lucide](https://lucide.dev/) - Icons

**Models:**
- Llama 3.1 8B Instruct (LLM)
- BAAI/bge-base-en-v1.5 (Embeddings)

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │
└────────┬────────┘
         │
┌────────▼────────┐      ┌──────────────┐
│  FastAPI Server │◄────►│ MinIO Storage│
└────────┬────────┘      └──────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ChromaDB│ │vLLM     │
│Vectors │ │Llama 3.1│
└────────┘ └─────────┘
```

## 📁 Project Structure

```
SyncResearch/
├── api/                  # FastAPI backend
│   ├── routes/          # API endpoints
│   └── models/          # Pydantic schemas
├── frontend/            # React application
├── document_processing/ # PDF parsing & chunking
├── embeddings_module/   # Vector generation
├── vectordb/           # ChromaDB operations
├── storage/            # MinIO client
├── rag_pipeline/       # RAG implementation
└── vllm-server/        # LLM inference setup
```

## 🔮 Roadmap

### ✅ Current (v1.0)
- [x] Single-paper RAG queries
- [x] PDF upload and processing
- [x] Local LLM inference
- [x] Web interface
- [x] Source attribution

### 🚧 Phase 2 (Multi-Agent)
- [ ] Query decomposition with Granite 3.0
- [ ] Parallel paper analysis
- [ ] Multi-paper comparison
- [ ] Advanced comparison synthesis

### 📋 Phase 3 (Advanced)
- [ ] Citation network analysis
- [ ] GPU-accelerated embeddings
- [ ] Graph RAG implementation
- [ ] Figure/diagram processing

## ⚙️ Configuration

Key environment variables (`.env`):

```bash
# MinIO Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=research-papers

# vLLM
VLLM_URL=http://localhost:8000

# App
DEBUG_MODE=False
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific component
pytest tests/test_rag.py -v
```

## 📊 Performance

- **Query Latency:** ~2.5s end-to-end
- **LLM Speed:** 25-30 tokens/second
- **Embedding:** ~45 chunks/second (CPU)
- **Concurrent Users:** 1-5 (single GPU)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with [vLLM](https://github.com/vllm-project/vllm) for efficient LLM inference
- PDF processing powered by [Docling](https://github.com/DS4SD/docling)
- Inspired by research in retrieval-augmented generation

## 📮 Contact

Questions? Open an issue or reach out:
- GitHub Issues: [Project Issues](https://github.com/yourusername/SyncResearch/issues)
- Email: your.email@example.com

---

**Note:** Requires NVIDIA GPU. For CPU-only inference, see the [CPU deployment guide](docs/cpu-deployment.md).