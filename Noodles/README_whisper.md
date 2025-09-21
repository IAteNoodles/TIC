# 🎤 Whisper Speech-to-Text API

A FastAPI backend for OpenAI Whisper with model selection and English language support.

## 🚀 Features

- **Multiple Whisper Models**: Choose from 7 different models (tiny to large-v3)
- **Fixed English Language**: Optimized for English speech recognition
- **File Upload**: Support for various audio formats (MP3, WAV, M4A, etc.)
- **URL Transcription**: Transcribe audio directly from URLs
- **Word-level Timestamps**: Optional detailed timing information
- **Model Management**: Load/unload models dynamically
- **Web Interface**: Simple HTML frontend for testing
- **RESTful API**: Complete OpenAPI documentation

## 📋 Available Models

### 🚀 English-Only Models (Recommended for English)
| Model | Size | Speed | VRAM | Description |
|-------|------|-------|------|-------------|
| tiny.en | 39 MB | ~12x realtime | ~1 GB | Fastest English-only |
| base.en | 74 MB | ~8x realtime | ~1 GB | **Recommended** balance |
| small.en | 244 MB | ~5x realtime | ~2 GB | Better accuracy English-only |
| medium.en | 769 MB | ~2.5x realtime | ~5 GB | High accuracy English-only |

### 🌍 Multilingual Models
| Model | Size | Speed | VRAM | Description |
|-------|------|-------|------|-------------|
| tiny | 39 MB | ~10x realtime | ~1 GB | Fastest multilingual |
| base | 74 MB | ~7x realtime | ~1 GB | Good balance multilingual |
| small | 244 MB | ~4x realtime | ~2 GB | Better accuracy multilingual |
| medium | 769 MB | ~2x realtime | ~5 GB | High accuracy multilingual |
| turbo | 809 MB | ~8x realtime | ~6 GB | **Latest fast model** |
| large | 1550 MB | ~1x realtime | ~10 GB | Highest accuracy |
| large-v2 | 1550 MB | ~1x realtime | ~10 GB | Improved large model |
| large-v3 | 1550 MB | ~1x realtime | ~10 GB | Latest multilingual |

### 💡 Model Selection Tips
- **For English speech**: Use `.en` models (faster and more accurate)
- **For multilingual**: Use regular models
- **For production**: `base.en` or `turbo` offer best speed/accuracy balance
- **For highest quality**: `large-v3` for multilingual, `medium.en` for English-only

## 🛠️ Installation

### 1. Install Requirements

```bash
# Install OpenAI Whisper (already done)
pip install openai-whisper

# Install FastAPI and dependencies
pip install fastapi uvicorn[standard] python-multipart

# Optional: Install additional audio processing libraries
pip install ffmpeg-python
```

### 2. Install FFmpeg (Required for audio processing)

**Windows:**
- Download from: https://ffmpeg.org/download.html
- Add to PATH environment variable

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🏃‍♂️ Running the Server

### Option 1: Direct Run
```bash
python whisper_server.py
```

### Option 2: Using Startup Script
```bash
python start_whisper.py
```

### Option 3: Manual Uvicorn
```bash
uvicorn whisper_server:app --host 0.0.0.0 --port 8006 --reload
```

## 🌐 API Endpoints

### Base URL: `http://localhost:8006`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check and status |
| `/models` | GET | List available models |
| `/transcribe` | POST | Transcribe uploaded file |
| `/transcribe-url` | POST | Transcribe from URL |
| `/models/{model_name}` | DELETE | Unload specific model |
| `/models` | DELETE | Unload all models |
| `/docs` | GET | Interactive API documentation |

## 📝 Usage Examples

### 1. Using the Web Interface
- Open `whisper_frontend.html` in your browser
- Select an audio file
- Choose a Whisper model
- Click "Transcribe Audio"

### 2. Using Python Client
```python
from whisper_client import WhisperClient

client = WhisperClient()

# Check API status
status = client.health_check()
print(status)

# Transcribe a file
result = client.transcribe_file("audio.mp3", model="base")
print(result['text'])
```

### 3. Using cURL
```bash
# Upload and transcribe a file
curl -X POST "http://localhost:8006/transcribe?model=base" \
     -F "file=@audio.mp3"

# Transcribe from URL
curl -X POST "http://localhost:8006/transcribe-url" \
     -d "url=https://example.com/audio.mp3&model=base"
```

### 4. Using JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append('file', audioFile);

const response = await fetch('http://localhost:8006/transcribe?model=base', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(result.text);
```

## 📊 Response Format

```json
{
  "text": "Transcribed speech content here",
  "model_used": "base",
  "language": "english",
  "duration": 10.5,
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "First segment"
    }
  ]
}
```

## 🎛️ Configuration Options

### Model Selection
- Choose model based on accuracy vs speed requirements
- Models are cached after first load
- Larger models require more VRAM/RAM

### Parameters
- **model**: Whisper model to use
- **include_segments**: Include word-level timestamps
- **temperature**: Sampling temperature (0.0 = deterministic)

### Supported Audio Formats
- MP3, WAV, M4A, MP4, MPEG, MPGA, WEBM, OGG, FLAC

## 🔧 Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   - Install FFmpeg and add to PATH
   - Restart terminal/IDE after installation

2. **"CUDA out of memory"**
   - Use smaller model (tiny/base instead of large)
   - Reduce batch size or use CPU inference

3. **"Model download failed"**
   - Check internet connection
   - Models are downloaded on first use (~1.5GB for large models)

4. **"Slow transcription"**
   - Use GPU if available (CUDA/Metal)
   - Choose smaller model for faster processing
   - Reduce audio file length

### Performance Tips

- **GPU Usage**: Whisper automatically uses GPU if available
- **Model Caching**: Models stay loaded in memory for faster subsequent use
- **File Size**: Larger audio files take longer to process
- **Model Choice**: Balance accuracy vs speed based on your needs

## 🔌 Integration Examples

### With Streamlit
```python
import streamlit as st
import requests

uploaded_file = st.file_uploader("Choose audio file")
if uploaded_file:
    files = {"file": uploaded_file}
    response = requests.post("http://localhost:8006/transcribe", files=files)
    result = response.json()
    st.write(result['text'])
```

### With Flask
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    files = {"file": audio_file}
    response = requests.post("http://localhost:8006/transcribe", files=files)
    return jsonify(response.json())
```

## 📈 Server Monitoring

- Health endpoint: `GET /health`
- Check loaded models and memory usage
- Monitor API response times
- Use `/models` DELETE endpoints to free memory

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Client App    │────│  FastAPI     │────│   Whisper       │
│  (Web/Mobile)   │    │   Server     │    │   Models        │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                       ┌──────────────┐
                       │   Model      │
                       │   Cache      │
                       └──────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

This project uses OpenAI Whisper under MIT License.

## 🆘 Support

- Check `/docs` endpoint for interactive API documentation
- Use the test client (`whisper_client.py`) for debugging
- Monitor server logs for error details
- Check Whisper GitHub issues for model-specific problems