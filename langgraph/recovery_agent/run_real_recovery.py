#!/usr/bin/env python3
"""
Real Recovery Agent Runner
Run this to perform actual recovery on your SD card.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

def check_server():
    """Check if the LangGraph server is running."""
    try:
        response = requests.get("http://127.0.0.1:2024/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_recovery():
    """Start the recovery process."""
    thread_id = f"sd_card_recovery_{int(time.time())}"
    
    print("🔧 Recovery Agent - REAL MODE")
    print("=" * 50)
    print("⚠️  WARNING: This will perform REAL drive operations!")
    print("🔒 SAFETY: All operations work on clones - your original SD card stays safe")
    print()
    
    if not check_server():
        print("❌ LangGraph server not running!")
        print("Start it with: langgraph dev")
        return
    
    print("✅ Server is running")
    
    # Confirm user wants to proceed
    confirm = input("\n🔍 Ready to detect and analyze your SD card? (yes/no): ").lower()
    if confirm not in ['yes', 'y']:
        print("👋 Recovery cancelled. Your SD card is safe.")
        return
    
    # Start the workflow
    print("\n🚀 Starting recovery workflow...")
    
    url = f"http://127.0.0.1:2024/threads/{thread_id}/invoke"
    payload = {
        "input": {},
        "config": {},
        "stream_mode": "updates"
    }
    
    try:
        # Initial request
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        print("✅ Workflow started!")
        print("\n" + "="*60)
        print("🌐 Continue in your web browser:")
        print(f"https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
        print("="*60)
        print()
        print("📋 In the Studio UI:")
        print("1. Look for your thread (starts with 'sd_card_recovery_')")
        print("2. You'll see drive detection results")
        print("3. Select your SD card from the list")
        print("4. Review the LLM analysis of corruption")
        print("5. Approve or reject the recovery plan")
        print("6. Monitor the recovery process")
        print()
        print("🔒 Remember: Everything happens on a clone - your original SD card is safe!")
        
        # Open browser
        import webbrowser
        webbrowser.open(f"https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
        
    except Exception as e:
        print(f"❌ Error starting recovery: {e}")

def main():
    print("""
🔧 SD Card Recovery Agent
========================

This will run the REAL recovery process on your connected SD card.

SAFETY FEATURES:
✅ Creates bit-for-bit clone before any analysis
✅ All recovery operations happen on the clone only  
✅ Original SD card remains completely untouched
✅ Human approval required at each critical step
✅ Claude 3.5 Sonnet provides intelligent analysis

PREREQUISITES:
1. SD card is connected to your computer
2. LangGraph server is running (langgraph dev)
3. You have sufficient disk space for cloning
4. Running with appropriate permissions

""")
    
    proceed = input("Ready to start recovery? (yes/no): ").lower()
    if proceed in ['yes', 'y']:
        start_recovery()
    else:
        print("👋 Come back when you're ready!")

if __name__ == "__main__":
    main()
