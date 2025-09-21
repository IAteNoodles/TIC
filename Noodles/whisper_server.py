"""
FastAPI backend for OpenAI Whisper speech-to-text conversion
Supports multiple Whisper models with English language fixed
"""

import os
import tempfile
import logging
import uuid
import shutil
import warnings
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import whisper
import uvicorn
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress Triton warnings on Windows (CUDA toolkit not needed for inference)
warnings.filterwarnings("ignore", message=".*Failed to launch Triton kernels.*")

# Initialize FastAPI app
app = FastAPI(
    title="Whisper Speech-to-Text API",
    description="OpenAI Whisper API for converting audio to text with model selection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available Whisper models
AVAILABLE_MODELS = [
    "tiny",      # 39 MB, ~32x realtime speed
    "tiny.en",   # 39 MB, English-only, faster
    "base",      # 74 MB, ~16x realtime speed  
    "base.en",   # 74 MB, English-only, faster
    "small",     # 244 MB, ~6x realtime speed
    "small.en",  # 244 MB, English-only, faster
    "medium",    # 769 MB, ~2x realtime speed
    "medium.en", # 769 MB, English-only, faster
    "large",     # 1550 MB, ~1x realtime speed
    "large-v2",  # 1550 MB, improved version
    "large-v3",  # 1550 MB, latest version
    "turbo"      # 809 MB, ~8x realtime speed, latest fast model
]

# Cache for loaded models
loaded_models = {}

# Pydantic models for request/response
class TranscriptionResponse(BaseModel):
    text: str
    model_used: str
    language: str
    segments: Optional[List[dict]] = None
    duration: Optional[float] = None

class ModelInfo(BaseModel):
    name: str
    size: str
    speed: str
    vram: str
    description: str

class HealthResponse(BaseModel):
    status: str
    available_models: List[str]
    loaded_models: List[str]
    device: str
    cuda_available: bool
    ffmpeg_available: bool
    ffmpeg_path: Optional[str] = None


def ensure_ffmpeg_available() -> Optional[str]:
    """Ensure ffmpeg is available on PATH; try to provide via imageio-ffmpeg on Windows.

    Returns the absolute path to the ffmpeg executable if available, else None.
    """
    # First, check if ffmpeg is already on PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # Try to use imageio-ffmpeg to supply a bundled ffmpeg binary
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.exists(ffmpeg_exe):
            bin_dir = os.path.dirname(ffmpeg_exe)
            # Prepend directory to PATH for current process so subprocess can find it
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            # Also expose explicit path some libraries look for
            os.environ["FFMPEG_BINARY"] = ffmpeg_exe
            logger.info(f"Configured ffmpeg from imageio-ffmpeg: {ffmpeg_exe}")
            return ffmpeg_exe
    except Exception as e:
        logger.warning(f"imageio-ffmpeg not available or failed to configure ffmpeg: {e}")

    logger.warning("ffmpeg not found. Please install ffmpeg and ensure it is on PATH.")
    return None

def get_model_info():
    """Get information about available Whisper models"""
    model_info = {
        "tiny": {"size": "39 MB", "speed": "~10x realtime", "vram": "~1 GB", "description": "Fastest multilingual model"},
        "tiny.en": {"size": "39 MB", "speed": "~12x realtime", "vram": "~1 GB", "description": "Fastest English-only model"},
        "base": {"size": "74 MB", "speed": "~7x realtime", "vram": "~1 GB", "description": "Good balance multilingual"},
        "base.en": {"size": "74 MB", "speed": "~8x realtime", "vram": "~1 GB", "description": "Good balance English-only"},
        "small": {"size": "244 MB", "speed": "~4x realtime", "vram": "~2 GB", "description": "Better accuracy multilingual"},
        "small.en": {"size": "244 MB", "speed": "~5x realtime", "vram": "~2 GB", "description": "Better accuracy English-only"},
        "medium": {"size": "769 MB", "speed": "~2x realtime", "vram": "~5 GB", "description": "High accuracy multilingual"},
        "medium.en": {"size": "769 MB", "speed": "~2.5x realtime", "vram": "~5 GB", "description": "High accuracy English-only"},
        "large": {"size": "1550 MB", "speed": "~1x realtime", "vram": "~10 GB", "description": "Highest accuracy multilingual"},
        "large-v2": {"size": "1550 MB", "speed": "~1x realtime", "vram": "~10 GB", "description": "Improved large multilingual"},
        "large-v3": {"size": "1550 MB", "speed": "~1x realtime", "vram": "~10 GB", "description": "Latest multilingual model"},
        "turbo": {"size": "809 MB", "speed": "~8x realtime", "vram": "~6 GB", "description": "Latest fast multilingual model"}
    }
    return model_info

def load_whisper_model(model_name: str):
    """Load a Whisper model, caching it for reuse"""
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{model_name}' not available. Choose from: {', '.join(AVAILABLE_MODELS)}"
        )
    
    if model_name not in loaded_models:
        try:
            logger.info(f"Loading Whisper model: {model_name}")
            
            # Try to use CUDA if available, fallback to CPU
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            model = whisper.load_model(model_name, device=device)
            loaded_models[model_name] = model
            logger.info(f"Successfully loaded model: {model_name} on {device}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model {model_name}: {str(e)}"
            )
    
    return loaded_models[model_name]

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Whisper Speech-to-Text API",
        "version": "1.0.0",
        "docs": "/docs",
        "available_models": AVAILABLE_MODELS
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ffmpeg_path = ensure_ffmpeg_available()
    
    return HealthResponse(
        status="healthy",
        available_models=AVAILABLE_MODELS,
        loaded_models=list(loaded_models.keys()),
        device=device,
        cuda_available=torch.cuda.is_available(),
        ffmpeg_available=bool(ffmpeg_path),
        ffmpeg_path=ffmpeg_path
    )

@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """Get information about available Whisper models"""
    model_info = get_model_info()
    return [
        ModelInfo(
            name=name,
            size=info["size"],
            speed=info["speed"],
            vram=info["vram"],
            description=info["description"]
        )
        for name, info in model_info.items()
    ]

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Query("base", description="Whisper model to use"),
    include_segments: bool = Query(False, description="Include word-level timestamps"),
    temperature: float = Query(0.0, description="Temperature for sampling (0.0 = deterministic)")
):
    """
    Transcribe audio file to text using Whisper
    
    - **file**: Audio file (mp3, wav, m4a, etc.)
    - **model**: Whisper model to use (tiny, base, small, medium, large, large-v2, large-v3)
    - **include_segments**: Whether to include word-level timestamps
    - **temperature**: Sampling temperature (0.0 for deterministic output)
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm', '.ogg', '.flac'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(allowed_extensions)}"
        )
    
    # Load the specified model
    whisper_model = load_whisper_model(model)
    
    # Save uploaded file temporarily
    temp_file_path = None
    try:
        # Create a more reliable temp file approach for Windows
        import uuid
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"whisper_{unique_id}{file_extension}"
        temp_file_path = os.path.join(temp_dir, temp_filename)
        
        # Write file directly
        content = await file.read()
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Processing audio file: {file.filename} with model: {model}")
        logger.info(f"Temp file created: {temp_file_path}")
        
        # Verify file exists and has content before processing
        if not os.path.exists(temp_file_path):
            raise Exception(f"Temporary file not found: {temp_file_path}")
        
        file_size = os.path.getsize(temp_file_path)
        if file_size == 0:
            raise Exception(f"Temporary file is empty: {temp_file_path}")
        
        logger.info(f"Temp file size: {file_size} bytes")
        
        # Small delay to ensure file is fully written (Windows filesystem quirk)
        import time
        time.sleep(0.1)
        
        # Build common transcribe params
        transcribe_params = {
            "temperature": temperature,
            "word_timestamps": include_segments,
            "verbose": False
        }
        if not model.endswith('.en'):
            transcribe_params["language"] = "en"

        # Use librosa for reliable audio decoding on Windows
        try:
            import librosa
            import numpy as np
            
            # Load and resample to 16kHz mono
            audio_array, sr = librosa.load(temp_file_path, sr=16000, mono=True)
            logger.info(f"Transcribing via librosa decode: sr=16000, samples={audio_array.shape[0]}")
            result = whisper_model.transcribe(audio_array, **transcribe_params)
        except Exception as lib_err:
            logger.error(f"librosa decode failed: {lib_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio decoding failed: {str(lib_err)}. Install librosa: pip install librosa"
            )
        
        # Prepare response
        response_data = {
            "text": result["text"].strip(),
            "model_used": model,
            "language": "english",
            "duration": result.get("duration")
        }
        
        # Include segments if requested
        if include_segments and "segments" in result:
            response_data["segments"] = result["segments"]
        
        logger.info(f"Successfully transcribed audio: {len(result['text'])} characters")
        return TranscriptionResponse(**response_data)
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        logger.error(f"Working directory: {os.getcwd()}")
        logger.error(f"Temp file absolute path: {os.path.abspath(temp_file_path) if temp_file_path else 'None'}")
        raise HTTPException(
            status_code=500,
            detail=f"File access error: {str(e)}. This might be a Windows permissions issue."
        )
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Temp file path: {temp_file_path}")
        logger.error(f"File exists: {os.path.exists(temp_file_path) if temp_file_path else 'No temp file'}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")

@app.post("/transcribe-url", response_model=TranscriptionResponse)
async def transcribe_from_url(
    url: str,
    model: str = Query("base", description="Whisper model to use"),
    include_segments: bool = Query(False, description="Include word-level timestamps"),
    temperature: float = Query(0.0, description="Temperature for sampling")
):
    """
    Transcribe audio from URL using Whisper
    
    - **url**: URL to audio file
    - **model**: Whisper model to use
    - **include_segments**: Whether to include word-level timestamps
    - **temperature**: Sampling temperature
    """
    
    # Load the specified model
    whisper_model = load_whisper_model(model)
    
    try:
        logger.info(f"Processing audio from URL: {url} with model: {model}")
        
        # Transcribe directly from URL
        # For English-only models (.en), don't specify language parameter
        transcribe_params = {
            "temperature": temperature,
            "word_timestamps": include_segments
        }
        
        # Only add language parameter for multilingual models
        if not model.endswith('.en'):
            transcribe_params["language"] = "en"
        
        result = whisper_model.transcribe(url, **transcribe_params)
        
        # Prepare response
        response_data = {
            "text": result["text"].strip(),
            "model_used": model,
            "language": "english",
            "duration": result.get("duration")
        }
        
        # Include segments if requested
        if include_segments and "segments" in result:
            response_data["segments"] = result["segments"]
        
        logger.info(f"Successfully transcribed audio from URL: {len(result['text'])} characters")
        return TranscriptionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error during URL transcription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"URL transcription failed: {str(e)}"
        )

@app.delete("/models/{model_name}")
async def unload_model(model_name: str):
    """Unload a specific model from memory"""
    if model_name in loaded_models:
        del loaded_models[model_name]
        logger.info(f"Unloaded model: {model_name}")
        return {"message": f"Model {model_name} unloaded successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_name} is not currently loaded"
        )

@app.delete("/models")
async def unload_all_models():
    """Unload all models from memory"""
    count = len(loaded_models)
    loaded_models.clear()
    logger.info(f"Unloaded {count} models")
    return {"message": f"All {count} models unloaded successfully"}

if __name__ == "__main__":
    # Configuration
    HOST = "0.0.0.0"
    PORT = 8006
    
    # Check CUDA availability
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cuda_info = f"✅ CUDA Available (GPU: {torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else "⚠️ CUDA Not Available (CPU only)"
    ffmpeg_path = ensure_ffmpeg_available()
    ffmpeg_info = f"✅ FFMPEG Available: {ffmpeg_path}" if ffmpeg_path else "⚠️ FFMPEG Not Found (install or add to PATH)"
    
    print(f"🎤 Starting Whisper API server on http://{HOST}:{PORT}")
    print(f"📚 API Documentation: http://{HOST}:{PORT}/docs")
    print(f"🔧 Available models: {', '.join(AVAILABLE_MODELS)}")
    print(f"🖥️ Device: {device.upper()}")
    print(f"🚀 {cuda_info}")
    print(f"🎬 {ffmpeg_info}")
    print("=" * 60)
    
    uvicorn.run(
        "whisper_server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )