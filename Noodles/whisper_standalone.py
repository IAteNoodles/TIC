#!/usr/bin/env python3
"""
Standalone Whisper Speech-to-Text Script
Self-contained script that runs Whisper on CUDA with all dependencies handled.
No server required - just run and transcribe!

Usage:
    python whisper_standalone.py audio_file.mp3
    python whisper_standalone.py audio_file.wav --model turbo --language en
"""

import os
import sys
import argparse
import warnings
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Union, List

# Suppress common warnings
warnings.filterwarnings("ignore", message=".*Failed to launch Triton kernels.*")
warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class WhisperStandalone:
    """Self-contained Whisper transcription class"""
    
    def __init__(self):
        self.device = None
        self.model = None
        self.model_name = None
        
    def check_dependencies(self) -> bool:
        """Check and install required dependencies"""
        required_packages = {
            'torch': 'torch',
            'whisper': 'openai-whisper', 
            'librosa': 'librosa',
            'numpy': 'numpy'
        }
        
        missing = []
        for package, pip_name in required_packages.items():
            try:
                __import__(package)
            except ImportError:
                missing.append(pip_name)
        
        if missing:
            logger.error(f"Missing packages: {', '.join(missing)}")
            logger.info("Install with: pip install " + " ".join(missing))
            return False
        
        return True
    
    def setup_device(self) -> str:
        """Setup and return the best available device"""
        try:
            import torch
            
            if torch.cuda.is_available():
                self.device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"🚀 Using CUDA GPU: {gpu_name}")
                logger.info(f"   CUDA Version: {torch.version.cuda}")
                logger.info(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                self.device = "cpu"
                logger.warning("⚠️  CUDA not available, using CPU (will be slower)")
                
        except Exception as e:
            logger.warning(f"Error detecting device: {e}")
            self.device = "cpu"
            
        return self.device
    
    def load_model(self, model_name: str = "base") -> bool:
        """Load Whisper model"""
        try:
            import whisper
            
            # Available models with info
            models_info = {
                "tiny": "39 MB, ~32x realtime, lowest accuracy",
                "tiny.en": "39 MB, ~32x realtime, English-only",
                "base": "74 MB, ~16x realtime, good balance", 
                "base.en": "74 MB, ~16x realtime, English-only",
                "small": "244 MB, ~6x realtime, better accuracy",
                "small.en": "244 MB, ~6x realtime, English-only", 
                "medium": "769 MB, ~2x realtime, high accuracy",
                "medium.en": "769 MB, ~2x realtime, English-only",
                "large": "1550 MB, ~1x realtime, highest accuracy",
                "large-v2": "1550 MB, ~1x realtime, improved large",
                "large-v3": "1550 MB, ~1x realtime, latest large",
                "turbo": "809 MB, ~8x realtime, fast and accurate"
            }
            
            if model_name not in models_info:
                logger.error(f"Unknown model '{model_name}'. Available: {list(models_info.keys())}")
                return False
            
            logger.info(f"📚 Loading model '{model_name}': {models_info[model_name]}")
            self.model = whisper.load_model(model_name, device=self.device)
            self.model_name = model_name
            logger.info(f"✅ Model loaded successfully on {self.device}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def transcribe_file(
        self, 
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        temperature: float = 0.0,
        word_timestamps: bool = False,
        verbose: bool = False
    ) -> Optional[dict]:
        """Transcribe audio file"""
        
        audio_path = Path(audio_path)
        
        # Validate file
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return None
            
        if not audio_path.suffix.lower() in {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm'}:
            logger.error(f"Unsupported file type: {audio_path.suffix}")
            return None
        
        file_size = audio_path.stat().st_size / 1024 / 1024  # MB
        logger.info(f"🎵 Processing: {audio_path.name} ({file_size:.1f} MB)")
        
        try:
            # Load audio with librosa for reliability
            import librosa
            import numpy as np
            
            logger.info("📊 Loading audio...")
            audio_array, sr = librosa.load(str(audio_path), sr=16000, mono=True)
            duration = len(audio_array) / sr
            logger.info(f"   Duration: {duration:.1f}s, Sample rate: {sr}Hz, Samples: {len(audio_array):,}")
            
            # Transcription parameters
            transcribe_params = {
                "temperature": temperature,
                "word_timestamps": word_timestamps,
                "verbose": verbose
            }
            
            # Set language for multilingual models
            if language and not self.model_name.endswith('.en'):
                transcribe_params["language"] = language
            elif not self.model_name.endswith('.en'):
                transcribe_params["language"] = "en"  # Default to English
            
            logger.info(f"🔄 Transcribing with {self.model_name} on {self.device}...")
            result = self.model.transcribe(audio_array, **transcribe_params)
            
            logger.info(f"✅ Transcription complete! ({len(result['text'])} characters)")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def format_result(self, result: dict, show_segments: bool = False) -> str:
        """Format transcription result for display"""
        if not result:
            return "❌ No transcription result"
        
        output = []
        output.append("=" * 60)
        output.append("📝 TRANSCRIPTION RESULT")
        output.append("=" * 60)
        output.append("")
        output.append(result["text"].strip())
        output.append("")
        
        if "language" in result:
            output.append(f"🌍 Language: {result['language']}")
        if "duration" in result:
            output.append(f"⏱️  Duration: {result['duration']:.1f}s")
        
        if show_segments and "segments" in result:
            output.append("\n📍 SEGMENTS:")
            output.append("-" * 40)
            for i, segment in enumerate(result["segments"][:10]):  # Show first 10
                start = segment.get("start", 0)
                end = segment.get("end", 0) 
                text = segment.get("text", "").strip()
                output.append(f"{i+1:2d}. [{start:6.1f}s - {end:6.1f}s] {text}")
            
            if len(result["segments"]) > 10:
                output.append(f"    ... and {len(result['segments']) - 10} more segments")
        
        output.append("=" * 60)
        return "\n".join(output)


# FastAPI Server Components (only imported when server mode is used)
def create_server_app(whisper_instance: WhisperStandalone):
    """Create FastAPI server application"""
    try:
        from fastapi import FastAPI, File, UploadFile, HTTPException, Query
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
    except ImportError:
        logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn python-multipart")
        return None
    
    # Pydantic models
    class TranscriptionResponse(BaseModel):
        text: str
        model_used: str
        language: str
        segments: Optional[List[dict]] = None
        duration: Optional[float] = None
    
    class HealthResponse(BaseModel):
        status: str
        device: str
        model_loaded: Optional[str] = None
        cuda_available: bool
        models_available: List[str]
    
    # Create FastAPI app
    app = FastAPI(
        title="Whisper Standalone API",
        description="Self-contained Whisper speech-to-text API",
        version="1.0.0"
    )
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/", response_model=dict)
    async def root():
        return {
            "message": "Whisper Standalone API",
            "version": "1.0.0",
            "docs": "/docs",
            "device": whisper_instance.device,
            "model_loaded": whisper_instance.model_name
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health():
        import torch
        models_available = ["tiny", "tiny.en", "base", "base.en", "small", "small.en", 
                           "medium", "medium.en", "large", "large-v2", "large-v3", "turbo"]
        
        return HealthResponse(
            status="healthy",
            device=whisper_instance.device or "unknown",
            model_loaded=whisper_instance.model_name,
            cuda_available=torch.cuda.is_available(),
            models_available=models_available
        )
    
    @app.post("/transcribe", response_model=TranscriptionResponse)
    async def transcribe_audio(
        file: UploadFile = File(...),
        model: str = Query("base", description="Whisper model to use"),
        language: Optional[str] = Query(None, description="Audio language (en, es, fr, etc.)"),
        temperature: float = Query(0.0, description="Sampling temperature 0.0-1.0"),
        include_segments: bool = Query(False, description="Include word-level timestamps")
    ):
        """Transcribe uploaded audio file"""
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(allowed_extensions)}"
            )
        
        # Load model if different from current
        if not whisper_instance.model or whisper_instance.model_name != model:
            logger.info(f"Loading model: {model}")
            if not whisper_instance.load_model(model):
                raise HTTPException(status_code=500, detail=f"Failed to load model: {model}")
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            unique_id = str(uuid.uuid4())[:8]
            temp_filename = f"whisper_{unique_id}{file_extension}"
            temp_file_path = Path(temp_dir) / temp_filename
            
            # Write uploaded content
            content = await file.read()
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Processing uploaded file: {file.filename} ({len(content)} bytes)")
            
            # Transcribe
            result = whisper_instance.transcribe_file(
                temp_file_path,
                language=language,
                temperature=temperature,
                word_timestamps=include_segments,
                verbose=False
            )
            
            if not result:
                raise HTTPException(status_code=500, detail="Transcription failed")
            
            # Prepare response
            response_data = {
                "text": result["text"].strip(),
                "model_used": model,
                "language": result.get("language", "unknown"),
                "duration": result.get("duration")
            }
            
            if include_segments and "segments" in result:
                response_data["segments"] = result["segments"]
            
            return TranscriptionResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        finally:
            # Clean up temp file
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                    logger.info(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
    
    @app.post("/transcribe-text", response_model=dict)
    async def transcribe_text_only(
        file: UploadFile = File(...),
        model: str = Query("base", description="Whisper model to use"),
        language: Optional[str] = Query(None, description="Audio language")
    ):
        """Simple text-only transcription endpoint"""
        
        # Call main transcribe endpoint
        result = await transcribe_audio(file, model, language, 0.0, False)
        return {"text": result.text, "model": result.model_used}
    
    @app.post("/load-model")
    async def load_model(model_name: str = Query(..., description="Model to load")):
        """Pre-load a specific model"""
        if whisper_instance.load_model(model_name):
            return {"message": f"Model {model_name} loaded successfully", "device": whisper_instance.device}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to load model: {model_name}")
    
    return app


def run_server(whisper_instance: WhisperStandalone, host: str = "0.0.0.0", port: int = 8006):
    """Run the FastAPI server"""
    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn not installed. Install with: pip install uvicorn")
        return False
    
    app = create_server_app(whisper_instance)
    if not app:
        return False
    
    print(f"\n🚀 Starting Whisper API Server")
    print(f"📡 Server URL: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🖥️  Device: {whisper_instance.device}")
    print(f"📝 Model: {whisper_instance.model_name or 'None loaded'}")
    print("=" * 50)
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
        return True
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        return False


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description="Standalone Whisper Speech-to-Text Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CLI Examples:
  python whisper_standalone.py audio.mp3
  python whisper_standalone.py song.wav --model turbo --segments
  python whisper_standalone.py video.mp4 --model large --language en --output result.txt

Server Examples:
  python whisper_standalone.py --server
  python whisper_standalone.py --server --model turbo --port 8007
        """
    )
    
    # Mode selection
    parser.add_argument("--server", action="store_true", help="Run as web API server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host [default: 0.0.0.0]")
    parser.add_argument("--port", type=int, default=8006, help="Server port [default: 8006]")
    
    # File input (for CLI mode)
    parser.add_argument("audio_file", nargs="?", help="Path to audio file (CLI mode only)")
    
    # Whisper options
    parser.add_argument("--model", "-m", default="base", 
                       help="Whisper model (tiny, base, small, medium, large, turbo) [default: base]")
    parser.add_argument("--language", "-l", default=None,
                       help="Audio language (en, es, fr, etc.) [default: auto-detect]")
    parser.add_argument("--temperature", "-t", type=float, default=0.0,
                       help="Sampling temperature 0.0-1.0 [default: 0.0]")
    parser.add_argument("--segments", "-s", action="store_true",
                       help="Show word-level timestamps")
    parser.add_argument("--output", "-o", help="Save transcription to file")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output during transcription")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.server and not args.audio_file:
        parser.error("Either provide an audio file for CLI mode or use --server flag")
    
    # Header
    if args.server:
        print("🎤 Whisper Standalone API Server")
    else:
        print("🎤 Whisper Standalone Transcription Tool")
    print("=" * 50)
    
    # Initialize Whisper
    whisper_tool = WhisperStandalone()
    
    # Check dependencies
    if not whisper_tool.check_dependencies():
        if args.server:
            logger.info("Additional server dependencies: pip install fastapi uvicorn python-multipart")
        return 1
    
    # Setup device
    whisper_tool.setup_device()
    
    # Server mode
    if args.server:
        # Pre-load model for server
        if not whisper_tool.load_model(args.model):
            logger.warning(f"Failed to pre-load model {args.model}, will load on first request")
        
        # Run server
        if not run_server(whisper_tool, args.host, args.port):
            return 1
        return 0
    
    # CLI mode
    if not whisper_tool.load_model(args.model):
        return 1
    
    # Transcribe file
    result = whisper_tool.transcribe_file(
        args.audio_file,
        language=args.language,
        temperature=args.temperature,
        word_timestamps=args.segments,
        verbose=args.verbose
    )
    
    if not result:
        return 1
    
    # Format and display result
    formatted_result = whisper_tool.format_result(result, show_segments=args.segments)
    print(formatted_result)
    
    # Save to file if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_result)
            logger.info(f"💾 Saved transcription to: {args.output}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)