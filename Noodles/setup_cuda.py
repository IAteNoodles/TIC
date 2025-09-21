"""
CUDA Setup Helper for Whisper Server
This script helps install PyTorch with CUDA support for GPU acceleration
"""

import subprocess
import sys
import platform

def check_cuda():
    """Check if CUDA is available"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA is available!")
            print(f"   - Device: {torch.cuda.get_device_name(0)}")
            print(f"   - CUDA Version: {torch.version.cuda}")
            print(f"   - PyTorch Version: {torch.__version__}")
            return True
        else:
            print("❌ CUDA is not available")
            return False
    except ImportError:
        print("❌ PyTorch is not installed")
        return False

def install_pytorch_cuda():
    """Install PyTorch with CUDA support"""
    print("🚀 Installing PyTorch with CUDA support...")
    
    # CUDA 11.8 is widely compatible
    cuda_command = [
        sys.executable, "-m", "pip", "install", 
        "torch", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/cu118"
    ]
    
    try:
        subprocess.run(cuda_command, check=True)
        print("✅ PyTorch with CUDA installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PyTorch with CUDA: {e}")
        return False

def install_pytorch_cpu():
    """Install PyTorch CPU-only version"""
    print("🔧 Installing PyTorch (CPU-only)...")
    
    cpu_command = [
        sys.executable, "-m", "pip", "install", 
        "torch", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/cpu"
    ]
    
    try:
        subprocess.run(cpu_command, check=True)
        print("✅ PyTorch (CPU) installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PyTorch: {e}")
        return False

def main():
    print("🎤 Whisper Server - CUDA Setup Helper")
    print("=" * 50)
    
    # Check current status
    if check_cuda():
        print("\n🎉 CUDA is already working! No setup needed.")
        print("Your Whisper server will use GPU acceleration.")
        return
    
    print("\n🤔 CUDA Setup Options:")
    print("1. Install PyTorch with CUDA support (GPU acceleration)")
    print("2. Install PyTorch CPU-only (no GPU acceleration)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            if install_pytorch_cuda():
                print("\n🔄 Verifying CUDA installation...")
                if check_cuda():
                    print("\n🎉 CUDA setup complete!")
                    print("Restart your Whisper server to use GPU acceleration.")
                else:
                    print("\n⚠️ CUDA installation may not be working properly.")
                    print("You might need to install CUDA drivers separately.")
            break
            
        elif choice == "2":
            if install_pytorch_cpu():
                print("\n✅ CPU-only PyTorch installed!")
                print("Whisper will run on CPU (slower but compatible).")
            break
            
        elif choice == "3":
            print("👋 Exiting setup...")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def print_cuda_info():
    """Print CUDA installation information"""
    print("\n📋 CUDA Installation Guide:")
    print("=" * 40)
    print("For GPU acceleration, you need:")
    print("1. NVIDIA GPU with CUDA Compute Capability 3.5+")
    print("2. NVIDIA drivers (latest recommended)")
    print("3. CUDA Toolkit (optional, PyTorch includes CUDA runtime)")
    print()
    print("🔗 Useful Links:")
    print("- NVIDIA Drivers: https://www.nvidia.com/Download/index.aspx")
    print("- CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
    print("- PyTorch Installation: https://pytorch.org/get-started/locally/")
    print()
    print("💡 Tips:")
    print("- CUDA 11.8 is recommended for compatibility")
    print("- GPU acceleration is 5-10x faster than CPU")
    print("- Larger models (medium/large) benefit most from GPU")

if __name__ == "__main__":
    try:
        main()
        print_cuda_info()
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
    
    input("\nPress Enter to exit...")