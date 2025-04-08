"""
Script to clear various Python and pip caches within a virtual environment.
Run this script from your project directory.
"""
import os
import shutil
import subprocess
import sys
import site

def clear_pip_cache():
    """Clear pip download cache"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], check=True)
        print("✅ Pip cache cleared")
    except subprocess.CalledProcessError:
        print("❌ Failed to clear pip cache")

def clear_streamlit_cache():
    """Clear Streamlit cache"""
    cache_dir = os.path.expanduser("~/.streamlit/cache")
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ Streamlit cache cleared: {cache_dir}")
        except Exception as e:
            print(f"❌ Failed to clear Streamlit cache: {e}")
    else:
        print("ℹ️ No Streamlit cache found")

def clear_python_cache():
    """Clear Python __pycache__ directories"""
    count = 0
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                count += 1
            except Exception as e:
                print(f"❌ Failed to clear {pycache_path}: {e}")
    
    if count > 0:
        print(f"✅ Cleared {count} __pycache__ directories")
    else:
        print("ℹ️ No __pycache__ directories found")

def clear_torch_cache():
    """Clear PyTorch cache if available"""
    try:
        import torch
        torch.cuda.empty_cache()
        print("✅ PyTorch CUDA cache cleared")
    except (ImportError, AttributeError):
        print("ℹ️ PyTorch CUDA cache not available")

if __name__ == "__main__":
    print("🧹 Starting cache cleanup...\n")
    
    clear_pip_cache()
    clear_streamlit_cache()
    clear_python_cache()
    clear_torch_cache()
    
    print("\n✨ Cache cleanup complete. You may need to restart your application.")
    print("💡 To fully clear all caches, you might also want to reinstall packages:")
    print("   pip install -r requirements.txt --force-reinstall")
