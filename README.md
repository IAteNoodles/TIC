# TIC (Technology in Healthcare) - Comprehensive Healthcare AI Platform

## 🏥 Project Overview

TIC is a comprehensive healthcare AI platform that integrates multiple cutting-edge technologies to revolutionize healthcare delivery in India. The platform addresses critical challenges in Indian healthcare including physician burnout, resource constraints, data privacy concerns, and accessibility issues through innovative AI-powered solutions.

## 🎯 Vision & Mission

**Vision:** To create a unified healthcare ecosystem that leverages AI, speech recognition, and intelligent automation to improve healthcare quality and accessibility across India.

**Mission:** Address healthcare challenges through:
- **Physician Burnout Reduction:** AI-powered clinical decision support and automated documentation
- **Digital Infrastructure:** Cloud-based solutions for resource-deficient areas
- **Data Privacy & Security:** ABDM-compliant secure data handling
- **Accessibility:** Multi-modal interfaces including voice and traditional inputs

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIC Healthcare Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Layer                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Patient    │  │   Doctor    │  │   Chat      │             │
│  │ Dashboard   │  │ Assistant   │  │ Interface   │             │
│  │ (Streamlit) │  │ (Streamlit) │  │ (Streamlit) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway & Services Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Chat     │  │ Traditional │  │     LLM     │             │
│  │   Server    │  │   Server    │  │   Server    │             │
│  │ (FastAPI)   │  │ (FastAPI)   │  │   (MCP)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  AI & Processing Layer                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Whisper   │  │  LangGraph  │  │    Redis    │             │
│  │Speech-to-Text│  │Multi-Agent │  │    Cache    │             │
│  │   Server    │  │  Workflow   │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  Data & Integration Layer                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Neo4j    │  │    ABDM     │  │  External   │             │
│  │  Database   │  │Integration  │  │     APIs    │             │
│  │             │  │             │  │(Gemini,Groq)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
TIC/
├── 📊 graphs.ipynb                 # Healthcare analytics and visualizations
├── 🔧 .env                        # Environment configuration
├── 📖 README_streamlit.md         # Streamlit chat client documentation
├── 
├── 🍜 Noodles/                    # Core platform services
│   ├── 💬 chat_server.py          # Multi-provider chat API with MCP tools
│   ├── 🏥 patient_app.py          # Patient health dashboard
│   ├── 🎤 whisper_server.py       # Speech-to-text service
│   ├── 🧠 llm_server.py           # LLM inference server (MCP)
│   ├── 🗄️ traditional_server.py   # Backend data services
│   ├── ⚡ redis_cache.py          # Caching layer
│   ├── 💬 streamlit_chat.py       # Chat interface
│   ├── 📋 requirements_*.txt      # Dependencies
│   └── 🌐 frontend/               # React frontend components
│
├── 👨‍⚕️ Anugrah/                    # Doctor assistant module
│   ├── doctor_assistant/          # Multi-agent AI assistant
│   │   ├── 🤖 agents/             # LangGraph agents
│   │   ├── 🔗 connectors/         # External service adapters
│   │   ├── 🛠️ tools/              # Reusable utilities
│   │   ├── 🎨 frontend/           # Streamlit doctor interface
│   │   ├── 📈 graph.py            # LangGraph workflow
│   │   └── 📋 requirements.txt    # Dependencies
│   └── 🌐 frontend/               # React doctor dashboard
│
├── 👥 Abhishek/                   # Team member contributions
├── 🧑‍💻 Sankalp/                   # Team member contributions
└── ⚙️ .vscode/                    # VS Code configuration
```

## 🚀 Core Features

### 1. 🏥 **Patient Health Dashboard**
- **Comprehensive Health Monitoring:** Real-time patient data visualization
- **Multi-Disease Prediction:** AI-powered risk assessment for cardiovascular disease, diabetes
- **Medical History Integration:** ABDM-compliant patient record management
- **Interactive Analytics:** Dynamic charts and health trend analysis

### 2. 👨‍⚕️ **AI Doctor Assistant**
- **Multi-Agent Architecture:** LangGraph-powered intelligent workflow
- **Clinical Decision Support:** Evidence-based diagnostic recommendations
- **Real-time Insights:** Streaming analysis with live status updates
- **Intent Recognition:** Natural language query understanding
- **CDSS Integration:** Clinical Decision Support System connectivity

### 3. 🎤 **Voice-Enabled Interface**
- **Whisper Integration:** OpenAI Whisper speech-to-text with 7 model variants
- **Multi-Language Support:** Optimized for English with multilingual capabilities
- **Real-time Transcription:** Live audio processing and documentation
- **Voice Commands:** Hands-free interaction for clinical workflows

### 4. 💬 **Intelligent Chat System**
- **Multi-Provider Support:** Gemini, Groq, Ollama LLM integration
- **MCP Tool Integration:** Model Context Protocol for enhanced capabilities
- **Fallback Mechanisms:** Robust error handling and provider switching
- **Tool Calling:** Dynamic function execution and API integration

### 5. 📊 **Healthcare Analytics**
- **Comprehensive Visualizations:** Jupyter notebook with 15+ healthcare metrics
- **Problem-Solution Mapping:** Current challenges vs. AI-powered solutions
- **Statistical Analysis:** Data-driven insights on Indian healthcare
- **Interactive Graphs:** Matplotlib-powered charts and comparisons

## 🛠️ Technology Stack

### **Backend Services**
- **FastAPI:** High-performance async API framework
- **LangGraph:** Multi-agent workflow orchestration
- **Neo4j:** Graph database for complex medical relationships
- **Redis:** High-performance caching and session management
- **PostgreSQL:** Relational data storage

### **AI & Machine Learning**
- **OpenAI Whisper:** Speech recognition and transcription
- **LangChain:** LLM application framework
- **Google Gemini:** Advanced language model integration
- **Groq:** High-speed LLM inference
- **Ollama:** Local LLM deployment
- **MCP (Model Context Protocol):** Standardized AI tool integration

### **Frontend Technologies**
- **Streamlit:** Rapid prototype and dashboard development
- **React:** Modern web application framework
- **TypeScript:** Type-safe frontend development
- **Tailwind CSS:** Utility-first styling framework

### **Data & Integration**
- **ABDM (Ayushman Bharat Digital Mission):** National health ID integration
- **Pandas:** Data manipulation and analysis
- **Matplotlib:** Data visualization and charts
- **Jupyter:** Interactive data science environment

## 🏃‍♂️ Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** (for React frontends)
- **Redis Server**
- **Neo4j Database**
- **CUDA-capable GPU** (optional, for local AI models)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/IAteNoodles/TIC.git
cd TIC

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install core dependencies
pip install -r Noodles/requirements_streamlit.txt
pip install -r Noodles/requirements_whisper.txt
pip install -r Anugrah/doctor_assistant/requirements.txt
```

### 2. Environment Configuration

Create `.env` file in project root:
```env
# LLM API Keys
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
MISTRAL_API_KEY=your_mistral_api_key

# Model Configuration
model_gemini="gemini-2.5-flash-lite"
model_groq="llama-3.3-70b-versatile"
model_ollama="llama3-groq-tool-use:8b"

# Service URLs
OLLAMA_BASE_URL="http://127.0.0.1:11434"
MCP_URL="http://localhost:8005/mcp"

# Database Configuration
AURA_USER=your_neo4j_user
AURA_PASSWORD=your_neo4j_password
```

### 3. Start Core Services

#### Backend Services (Terminal 1-4)
```bash
# Terminal 1: Traditional Backend
cd Noodles
python traditional_server.py

# Terminal 2: LLM Server (MCP)
python llm_server.py

# Terminal 3: Chat API Server
python chat_server.py

# Terminal 4: Whisper Speech Server
python whisper_server.py --server --model base.en
```

#### Frontend Applications (Terminal 5-7)
```bash
# Terminal 5: Patient Dashboard
cd Noodles
streamlit run patient_app.py

# Terminal 6: Chat Interface
streamlit run streamlit_chat.py

# Terminal 7: Doctor Assistant
cd Anugrah/doctor_assistant
streamlit run frontend/app.py
```

### 4. Access the Applications

| Service | URL | Description |
|---------|-----|-------------|
| Patient Dashboard | http://localhost:8501 | Comprehensive health monitoring |
| Chat Interface | http://localhost:8502 | AI-powered chat system |
| Doctor Assistant | http://localhost:8503 | Clinical decision support |
| Traditional API | http://localhost:5002 | Backend data services |
| Chat API | http://localhost:8088 | Multi-provider chat API |
| Whisper API | http://localhost:8006 | Speech-to-text service |
| LLM Server | http://localhost:1234 | MCP-enabled LLM service |

## 📋 Detailed Component Guide

### 🏥 Patient Dashboard (`patient_app.py`)

**Features:**
- Real-time health metrics visualization
- Multi-disease risk prediction (cardiovascular, diabetes)
- Medical history timeline
- Appointment scheduling
- Lab result integration via OCR

**API Endpoints:**
- `CARDIO_API`: Cardiovascular risk prediction
- `DIABETES_API`: Diabetes risk assessment
- `BACKEND_API`: Patient data retrieval
- `LLM_API`: AI-powered health insights

### 👨‍⚕️ Doctor Assistant

**Architecture:**
- **Main Agent:** Workflow orchestration
- **Intent Agent:** Query classification and routing
- **Diagnosis Agent:** Medical analysis and recommendations
- **Information Retrieval:** Patient data aggregation

**Workflow:**
1. **Query Input:** Natural language medical queries
2. **Intent Analysis:** Classify as information retrieval or diagnosis
3. **Data Gathering:** Fetch relevant patient information
4. **AI Analysis:** Generate clinical insights and recommendations
5. **Report Generation:** Structured medical documentation

### 🎤 Whisper Speech Service

**Supported Models:**
- **English-only:** `tiny.en`, `base.en`, `small.en`, `medium.en`
- **Multilingual:** `tiny`, `base`, `small`, `medium`, `large`, `large-v2`, `large-v3`

**Features:**
- Real-time transcription
- Batch file processing
- Word-level timestamps
- Multiple audio format support
- Dynamic model loading/unloading

### 💬 Chat System

**Provider Support:**
- **Gemini:** Google's advanced language model
- **Groq:** High-speed inference platform
- **Ollama:** Local model deployment

**MCP Integration:**
- Dynamic tool discovery
- Function calling capabilities
- Structured response handling
- Error recovery and fallbacks

## 🔧 Configuration & Customization

### Model Configuration

Edit `Anugrah/doctor_assistant/config/parameters.txt`:
```
model_name=gemini-2.5-flash-lite
temperature=0.1
max_tokens=2048
top_p=0.9
```

### API Endpoints

Modify service URLs in respective configuration files:
- `Noodles/patient_app.py`: Dashboard API endpoints
- `Noodles/chat_server.py`: Chat service configuration
- `Anugrah/doctor_assistant/connectors/`: External service adapters

### Database Configuration

**Neo4j Setup:**
```python
# In traditional_server.py
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"
```

**Redis Configuration:**
```python
# In redis_cache.py
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
```

## 📊 Healthcare Analytics

The `graphs.ipynb` notebook provides comprehensive visualizations of:

### Current Healthcare Challenges
- **Physician Burnout:** 50% of doctors experiencing burnout
- **Infrastructure Gaps:** Only 21% of rural PHCs have computers
- **Data Privacy Concerns:** 81% view privacy as significant concern
- **Manual Processes:** <40% EHR adoption rate

### AI-Powered Solutions
- **Time Savings:** 90% reduction in documentation time
- **Accuracy Improvements:** >99% OCR accuracy for lab reports
- **Error Reduction:** <5% diagnostic error rate with AI assistance
- **Accessibility:** 95% cost reduction for rural CDSS deployment

### Key Metrics Visualized
1. **Patient Data Collection:** Registration time, accuracy, history availability
2. **Diagnostic Support:** Query response time, uncertainty handling, interactivity
3. **EHR Automation:** Documentation time, error rates, update lag
4. **OCR Integration:** Transcription speed, accuracy, data structuring
5. **Auto-Transcription:** Documentation burden, workday impact, standardization

## 🔒 Security & Compliance

### ABDM Integration
- **ABHA ID Support:** National health identifier integration
- **Consent Management:** Patient-controlled data sharing
- **Interoperability:** Seamless data exchange across systems
- **Privacy Protection:** End-to-end encryption and secure APIs

### Data Security
- **Authentication:** Multi-factor authentication support
- **Authorization:** Role-based access control
- **Encryption:** Data at rest and in transit
- **Audit Logs:** Comprehensive activity tracking

## 🧪 Testing & Development

### Running Tests
```bash
# Doctor Assistant Tests
cd Anugrah/doctor_assistant
python test_complete_workflow.py
python test_streaming.py
python test_realtime_insights.py

# Individual Component Tests
python test_backend_connector.py
python test_diagnosis_agent.py
python test_mcp_integration.py
```

### Development Tools
- **Logging:** Centralized logging with rotation
- **Debugging:** Environment-based log levels
- **Monitoring:** Real-time service health checks
- **Documentation:** Auto-generated API docs via FastAPI

## 🚀 Deployment

### Production Checklist
- [ ] Configure production environment variables
- [ ] Set up SSL certificates for HTTPS
- [ ] Configure database backups
- [ ] Set up monitoring and alerting
- [ ] Implement load balancing
- [ ] Configure auto-scaling policies

### Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale chat-server=3
```

### Cloud Deployment Options
- **AWS:** ECS, Lambda, RDS, ElastiCache
- **Google Cloud:** Cloud Run, Cloud SQL, Memorystore
- **Azure:** Container Instances, SQL Database, Redis Cache

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Code Standards
- **Python:** Follow PEP 8 style guidelines
- **TypeScript:** Use ESLint and Prettier configurations
- **Documentation:** Update README and inline comments
- **Testing:** Add tests for new functionality

### Project Structure Guidelines
- **Modularity:** Keep components loosely coupled
- **Reusability:** Create reusable tools and utilities
- **Scalability:** Design for horizontal scaling
- **Maintainability:** Write clean, documented code

## 📚 Additional Resources

### Documentation
- [Streamlit Chat Client](README_streamlit.md)
- [Whisper API Guide](Noodles/README_whisper.md)
- [Doctor Assistant Documentation](Anugrah/doctor_assistant/README.md)
- [Project Planning](Anugrah/doctor_assistant/project_plan.md)

### External APIs & Services
- [ABDM Documentation](https://abdm.gov.in/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Neo4j Graph Database](https://neo4j.com/docs/)

## 📞 Support & Contact

### Issues & Bug Reports
- **GitHub Issues:** [Create an issue](https://github.com/IAteNoodles/TIC/issues)
- **Discussion:** [GitHub Discussions](https://github.com/IAteNoodles/TIC/discussions)

### Team
- **Project Lead:** Souvik (IAteNoodles)
- **AI/ML Engineer:** Anugrah Singh
- **Contributors:** Abhishek, Sankalp

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Impact & Vision

TIC represents a paradigm shift in healthcare technology, addressing critical challenges in the Indian healthcare system through innovative AI solutions. By reducing physician burnout, improving diagnostic accuracy, and increasing accessibility, TIC aims to transform healthcare delivery for millions of patients across India.

**Key Impact Areas:**
- **Physician Welfare:** Reducing administrative burden and burnout
- **Patient Care:** Improving diagnostic accuracy and treatment outcomes
- **Healthcare Accessibility:** Extending quality care to rural and underserved areas
- **System Efficiency:** Streamlining workflows and reducing costs
- **Data-Driven Insights:** Enabling evidence-based healthcare decisions

The platform's modular architecture ensures scalability and adaptability, making it suitable for deployment across diverse healthcare settings from rural PHCs to urban hospitals.

---

*Last Updated: December 2024*
*Version: 1.0.0*