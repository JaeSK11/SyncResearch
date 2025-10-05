# SyncResearch
This project implements a  Retrieval-Augmented Generation (RAG) system designed specifically for analyzing and comparing academic research papers. The system enables semantic querying across multiple papers, with special emphasis on comparative analysis between different research works.

### Core Capabilities
- **Document Processing**: Intelligent extraction from complex academic PDFs
- **Semantic Search**: Vector-based similarity search across research papers
- **Multi-Paper Analysis**: Comparative analysis between different papers
- **Self-Hosted LLM**: Complete data privacy with local inference
- **Scalable Storage**: Cloud-based document management via S3

### Key Innovation
The system solves the fundamental challenge of multi-paper comparison queries through a multi-agent architecture, where specialized agents handle paper-specific retrieval before synthesis.

## Project Architecture (ResearchRetrieval)

### System Components

```
┌─────────────────────────────────────────────────────┐
│                  User Interface Layer               │
│                    FastAPI Server                   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Multi-Agent Orchestrator               │
│                                                      │
│  ┌─────────────────────────────────────────┐       │
│  │     Agent 1: Query Decomposer           │       │
│  │     Model: Granite-3.0-8B               │       │
│  │     Role: Parse & structure queries     │       │
│  └─────────────────┬───────────────────────┘       │
│                    │                                │
│  ┌─────────────────▼───────────────────────┐       │
│  │  Agent 2 & 3: Paper Analyzers (Parallel)│       │
│  │  Model: Llama-3.1-8B                    │       │
│  │  Role: Paper-specific analysis          │       │
│  └─────────────────┬───────────────────────┘       │
│                    │                                │
│  ┌─────────────────▼───────────────────────┐       │
│  │    Agent 4: Comparison Synthesizer      │       │
│  │    Model: Llama-3.1-8B                  │       │
│  │    Role: Generate comparative analysis  │       │
│  └─────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                 Data Processing Layer               │
│                                                      │
│  ┌────────────────────────────────────────┐        │
│  │         Docling Engine                 │        │
│  │  - PDF parsing & structure extraction  │        │
│  │  - Table/figure detection              │        │
│  │  - Section hierarchy preservation      │        │
│  └────────────────────────────────────────┘        │
│                                                      │
│  ┌────────────────────────────────────────┐        │
│  │      LangChain Components              │        │
│  │  - Document chunking strategies        │        │
│  │  - Prompt template management          │        │
│  │  - Chain orchestration                 │        │
│  └────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  Storage Layer                      │
│                                                      │
│  ┌────────────────────────────────────────┐        │
│  │           AWS S3 Buckets               │        │
│  │  /raw-papers     - Original PDFs       │        │
│  │  /processed      - Docling outputs     │        │
│  │  /embeddings     - Vector cache        │        │
│  │  /metadata       - Paper metadata      │        │
│  └────────────────────────────────────────┘        │
│                                                      │
│  ┌────────────────────────────────────────┐        │
│  │       ChromaDB Vector Store            │        │
│  │  - Paper-specific collections          │        │
│  │  - Semantic search indices             │        │
│  │  - Metadata filtering                  │        │
│  └────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

## Data Flow Pipeline

### Document Ingestion Flow

```
1. PDF Upload
   └─> S3 Raw Storage
       └─> Docling Processing
           ├─> Structure Extraction
           ├─> Section Detection
           ├─> Table/Figure Extraction
           └─> Metadata Generation
               └─> JSON Output
                   └─> S3 Processed Storage
2. Vectorization Pipeline
   └─> Load Processed JSON
       └─> Chunking Strategy
           ├─> Hierarchical Chunks
           ├─> Semantic Chunks
           └─> Overlap Management
               └─> Embedding Generation
                   ├─> Batch Processing
                   └─> Vector Creation
                       └─> ChromaDB Storage
                           ├─> Collection Creation
                           └─> Metadata Indexing
```

### Query Processing Flow

```
1. User Query Reception
   └─> FastAPI Endpoint
       └─> Request Validation
           └─> Correlation ID Assignment
2. Multi-Agent Processing
   └─> Query Decomposer (Granite)
       ├─> Intent Classification
       ├─> Paper Identification
       └─> Task Structuring
           └─> Parallel Paper Analysis
               ├─> Paper X Analyzer (Llama)
               │   ├─> Vector Search
               │   ├─> Context Assembly
               │   └─> Analysis Generation
               │
               └─> Paper Y Analyzer (Llama)
                   ├─> Vector Search
                   ├─> Context Assembly
                   └─> Analysis Generation
                       └─> Comparison Synthesizer (Llama)
                           ├─> Analysis Integration
                           ├─> Difference Identification
                           └─> Final Response Generation
3. Response Delivery
   └─> JSON Formatting
       └─> Source Attribution
           └─> Client Response
```

### Chunking Strategy

Respects paper structure - chunks by section (abstract, methodology, results)
Adds bidirectional context - includes preview/review text
Section-aware sizing - abstracts stay together, results are smaller chunks
Special handling - tables, figures, equations get dedicated chunks
Metadata-rich - enables "search only in methodology" type queries

Prevents
Lost context: Breaks mid-argument or mid-explanation
Section boundaries: Doesn't respect paper structure
Reference confusion: Splits text from its citations

```python
# Hierarchical Structure
Paper
├── Overview Chunk (500 tokens)
│   └── Title, Abstract, Authors
├── Section Chunks (1000 tokens)
│   ├── Introduction
│   ├── Methodology
│   ├── Results
│   └── Conclusion
├── Subsection Chunks (500 tokens)
│   └── Detailed content
└── Special Chunks
    ├── Table Chunks
    ├── Figure Captions
    └── Reference Chunks
```

---

## Library Stack & Justification

### Core Libraries

#### 1. **vLLM** (LLM Inference Engine)
- **Purpose**: High-performance local LLM inference
- **Why**: 
  - PagedAttention for 24x higher throughput than HuggingFace
  - Optimized for RTX 3090's memory constraints
  - OpenAI-compatible API for easy integration
- **Benefits**:
  - Automatic batching for multiple requests
  - Continuous batching for optimal GPU utilization
  - Memory-efficient KV cache management

#### 2. **Docling** (Document Processing)
- **Purpose**: Academic paper structure extraction
- **Why**:
  - Specifically designed for complex academic layouts
  - Preserves document hierarchy and relationships
  - Handles tables, figures, equations effectively
- **Benefits**:
  - Better than PyPDF2/pdfplumber for research papers
  - Structured JSON output ready for vectorization
  - Maintains citation and reference integrity

#### 3. **LangChain** (RAG Framework)
- **Purpose**: RAG pipeline orchestration
- **Why**:
  - Extensive ecosystem of document loaders
  - Built-in chunking strategies
  - Seamless vector store integration
- **Benefits**:
  - Reduces boilerplate code by 70%
  - Standardized interfaces for components
  - Active community and documentation

#### 4. **ChromaDB** (Vector Database)
- **Purpose**: Semantic similarity search
- **Why**:
  - Simple local deployment
  - No external dependencies
  - Good performance for <1M vectors
- **Benefits**:
  - Zero configuration setup
  - Metadata filtering capabilities
  - Persistent storage to disk
  - Free and open source

#### 5. **FastAPI** (Web Framework)
- **Purpose**: REST API server
- **Why**:
  - Native async/await support
  - Automatic API documentation
  - High performance (Starlette + Pydantic)
- **Benefits**:
  - Type validation at runtime
  - Interactive docs at `/docs`
  - WebSocket support for streaming
  - Easy deployment with Docker

#### 6. **HuggingFace Embeddings** (Text Vectorization)
- **Purpose**: Convert text to semantic vectors
- **Why**:
  - Local execution (no API costs)
  - BAAI/bge models optimized for retrieval
  - CUDA acceleration on RTX 3090
- **Benefits**:
  - Complete data privacy
  - No rate limits
  - Consistent performance
  - Free to use

### Supporting Libraries

#### 7. **Boto3** (AWS SDK)
- **Purpose**: S3 interaction
- **Why**: Native AWS integration
- **Benefits**: Reliable, well-documented, handles retries

#### 8. **Pydantic** (Data Validation)
- **Purpose**: Request/response validation
- **Why**: Type safety and automatic validation
- **Benefits**: Prevents runtime errors, auto-generates schemas

#### 9. **Pandas** (Data Manipulation)
- **Purpose**: Parquet file handling
- **Why**: Efficient columnar data operations
- **Benefits**: Fast filtering, aggregation for chunk metadata

#### 10. **Structlog** (Logging)
- **Purpose**: Structured JSON logging
- **Why**: Essential for multi-agent tracing
- **Benefits**: Correlation IDs, performance metrics, error tracking

---

## Design Decisions & Rationale

### 1. Multi-Agent Architecture

**Problem**: Single-query embeddings cannot effectively capture multi-paper comparison requests.

**Solution**: Decompose queries into paper-specific sub-queries, process in parallel, then synthesize.

**Rationale**:
- Eliminates semantic confusion in vector search
- Enables focused retrieval per paper
- Supports complex comparative analysis
- Scales to N papers without architectural changes

### 2. Hybrid Model Strategy

**Decision**: Use Granite for decomposition, Llama for analysis.

**Rationale**:
- Granite: Conservative, structured output ideal for parsing
- Llama: Superior reasoning for research comprehension
- Task-optimized model selection
- Efficient resource utilization

### 3. Parquet Over Pickle

**Decision**: Store processed chunks in Parquet format.

**Rationale**:
- Security: No code execution risks (unlike pickle)
- Compatibility: Works across Python versions
- Performance: Columnar storage for efficient queries
- Compression: 50-70% smaller than JSON
- Schema evolution: Add fields without breaking

### 4. Local Embeddings

**Decision**: Self-host embeddings instead of OpenAI API.

**Rationale**:
- Privacy: Papers never leave your infrastructure
- Cost: No per-token charges
- Control: Consistent model availability
- Performance: No network latency

### 5. Hierarchical Chunking

**Decision**: Multi-level chunking with metadata preservation.

**Rationale**:
- Maintains document structure
- Enables section-aware retrieval
- Supports both broad and specific queries
- Preserves context boundaries

### 6. S3 for Document Storage

**Decision**: Use S3 instead of local filesystem.

**Rationale**:
- Scalability: Unlimited storage capacity
- Durability: 11 nines reliability
- Accessibility: Access from any compute node
- Versioning: Track document changes
- Cost: Pay only for what you use

---