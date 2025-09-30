#!/usr/bin/env python3
"""
Chat Memory Demo CLI

This script demonstrates the chat memory functionality.
You can start new conversations, continue existing ones, and manage chat sessions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.assistant.main import (
    generate_chat_response, 
    generate_report, 
    get_chat_sessions, 
    get_chat_history,
    delete_chat_session,
    update_session_title
)
from backend.assistant.utils import create_vector_store, delete_vector_store
from backend.database.connection import create_tables

def print_separator():
    print("=" * 60)

def print_menu():
    print("\n🤖 AI Coaching Chat Memory Demo")
    print_separator()
    print("1. Start new chat")
    print("2. Continue existing chat")
    print("3. Generate report")
    print("4. List chat sessions")
    print("5. View chat history")
    print("6. Delete chat session")
    print("7. Update session title")
    print("8. Exit")
    print_separator()

def start_new_chat():
    print("\n🆕 Starting new chat...")
    
    # For demo purposes, we'll use a mock vector store ID
    # In real usage, you'd create this from uploaded documents
    print("📁 Enter bucket folder name for documents (or press Enter for demo):")
    bucket_folder = input("> ").strip()
    
    if bucket_folder:
        try:
            vector_store_id = create_vector_store(bucket_folder)
            print(f"✅ Created vector store: {vector_store_id}")
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
            print("Using demo vector store ID...")
            vector_store_id = "demo_vector_store_id"
    else:
        vector_store_id = "demo_vector_store_id"
    
    user_id = input("👤 Enter user ID (optional): ").strip() or None
    
    print("\n💬 Chat started! Type 'quit' to exit this chat.")
    print_separator()
    
    session_id = None
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        try:
            result = generate_chat_response(
                message=user_input,
                vector_store_id=vector_store_id,
                session_id=session_id,
                user_id=user_id
            )
            
            session_id = result["session_id"]
            print(f"\n🤖 Assistant: {result['response']}")
            print(f"\n📊 Session: {session_id} | Messages: {result['message_count']}")
            print_separator()
            
        except Exception as e:
            print(f"❌ Error: {e}")

def continue_existing_chat():
    print("\n🔄 Continue existing chat...")
    session_id = input("📝 Enter session ID: ").strip()
    
    if not session_id:
        print("❌ Session ID is required!")
        return
    
    try:
        # Get chat history to verify session exists
        history = get_chat_history(session_id)
        if not history:
            print("❌ Session not found!")
            return
        
        print(f"✅ Found session with {len(history)} messages")
        
        # Show recent history
        print("\n📜 Recent conversation:")
        print_separator()
        for msg in history[-6:]:  # Show last 6 messages
            role = "🤖" if msg["role"] == "assistant" else "👤"
            print(f"{role} {msg['role'].title()}: {msg['content'][:100]}...")
        
        print_separator()
        print("💬 Continue chatting! Type 'quit' to exit.")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            try:
                # We need a vector_store_id for the chat to work
                # In a real app, this would be stored with the session
                vector_store_id = "demo_vector_store_id"
                
                result = generate_chat_response(
                    message=user_input,
                    vector_store_id=vector_store_id,
                    session_id=session_id
                )
                
                print(f"\n🤖 Assistant: {result['response']}")
                print(f"\n📊 Session: {session_id} | Messages: {result['message_count']}")
                print_separator()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def list_chat_sessions():
    print("\n📋 Chat sessions...")
    user_id = input("👤 Enter user ID (leave empty for all): ").strip()
    
    if not user_id:
        print("❌ User ID is required for listing sessions in this demo")
        return
    
    try:
        sessions = get_chat_sessions(user_id)
        
        if not sessions:
            print("📭 No chat sessions found")
            return
        
        print_separator()
        for session in sessions:
            print(f"🆔 ID: {session['session_id']}")
            print(f"📝 Title: {session['title']}")
            print(f"📅 Created: {session['created_at']}")
            print(f"💬 Messages: {session['message_count']}")
            print(f"🔢 Tokens: {session['total_tokens_used']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def view_chat_history():
    print("\n📜 View chat history...")
    session_id = input("📝 Enter session ID: ").strip()
    
    if not session_id:
        print("❌ Session ID is required!")
        return
    
    try:
        history = get_chat_history(session_id)
        
        if not history:
            print("📭 No messages found")
            return
        
        print_separator()
        for msg in history:
            role_icon = "🤖" if msg["role"] == "assistant" else "👤" if msg["role"] == "user" else "⚙️"
            print(f"{role_icon} {msg['role'].title()} [{msg['timestamp']}]:")
            print(f"   {msg['content']}")
            if msg['message_type'] != 'chat':
                print(f"   📂 Type: {msg['message_type']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # Initialize database
    create_tables()
    
    print("🚀 Initializing AI Coaching Chat Memory System...")
    print("📊 Database initialized successfully!")
    
    while True:
        print_menu()
        choice = input("Select option (1-8): ").strip()
        
        if choice == "1":
            start_new_chat()
        elif choice == "2":
            continue_existing_chat()
        elif choice == "3":
            print("\n📊 Generate report feature - similar to chat but for reports")
            print("(Implementation would be similar to chat)")
        elif choice == "4":
            list_chat_sessions()
        elif choice == "5":
            view_chat_history()
        elif choice == "6":
            session_id = input("📝 Enter session ID to delete: ").strip()
            if session_id and delete_chat_session(session_id):
                print("✅ Session deleted!")
            else:
                print("❌ Failed to delete session")
        elif choice == "7":
            session_id = input("📝 Enter session ID: ").strip()
            title = input("📝 Enter new title: ").strip()
            if session_id and title and update_session_title(session_id, title):
                print("✅ Title updated!")
            else:
                print("❌ Failed to update title")
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()