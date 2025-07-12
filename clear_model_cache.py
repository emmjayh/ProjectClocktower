#!/usr/bin/env python3
"""
Clear Whisper model cache to force fresh downloads
Useful for troubleshooting download issues
"""
import shutil
import sys
from pathlib import Path


def clear_whisper_cache():
    """Clear the Whisper model cache"""
    import os
    
    home = os.path.expanduser("~")
    cache_dir = Path(home) / ".cache" / "whisper"
    
    if cache_dir.exists():
        print(f"Clearing Whisper cache at: {cache_dir}")
        shutil.rmtree(cache_dir)
        print("✅ Whisper cache cleared")
    else:
        print("ℹ️ No Whisper cache found")
    
    # Also clear project models directory if it exists
    project_models = Path("models")
    if project_models.exists():
        print(f"Clearing project models at: {project_models}")
        shutil.rmtree(project_models)
        print("✅ Project models cleared")
    
    print("\n🔄 Next download will fetch fresh models")


if __name__ == "__main__":
    print("🧹 Blood on the Clocktower - Clear Model Cache")
    print("=" * 50)
    
    if "--force" in sys.argv:
        clear_whisper_cache()
    else:
        response = input("Clear all cached AI models? This will force fresh downloads next time. (y/N): ")
        if response.lower() in ["y", "yes"]:
            clear_whisper_cache()
        else:
            print("❌ Cache clearing cancelled")