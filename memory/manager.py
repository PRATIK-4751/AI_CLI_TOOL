"""
Memory manager for handling conversation history and context.
Manages short-term memory (recent messages) and long-term memory (summaries).
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import asdict
from .types import Message, ConversationSummary
from .summarizer import ConversationSummarizer
from llm.ollama_client import OllamaClient


class MemoryManager:
    """Manages conversation memory with short-term and long-term storage."""
    
    def __init__(self, memory_dir: Path = None, llm_client: OllamaClient = None):
        if memory_dir is None:
            memory_dir = Path(__file__).parent.parent / "memory"
        
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(exist_ok=True)
        
        # Initialize LLM client if not provided
        self.llm_client = llm_client
        if self.llm_client is None:
            self.llm_client = OllamaClient()
        
        # Initialize summarizer
        self.summarizer = ConversationSummarizer(self.llm_client)
        
        # Short-term memory (RAM)
        self.session_buffer: List[Message] = []
        self.max_short_term_messages = 10
        
        # Long-term memory (files)
        self.session_file = self.memory_dir / "session.json"
        self.summary_file = self.memory_dir / "summary.json"
        
        # Load existing session
        self._load_session()
    
    def add_message(self, role: str, content: str):
        """Add a message to short-term memory."""
        message = Message(role=role, content=content)
        self.session_buffer.append(message)
        
        # Check if we need to summarize
        if len(self.session_buffer) > self.max_short_term_messages:
            self._summarize_and_archive()
    
    def get_recent_context(self, n: int = 5) -> List[Message]:
        """Get recent messages from short-term memory."""
        return self.session_buffer[-n:] if self.session_buffer else []
    
    def get_summary(self) -> Optional[ConversationSummary]:
        """Load conversation summary from long-term memory."""
        if not self.summary_file.exists():
            return None
            
        try:
            with open(self.summary_file, 'r') as f:
                data = json.load(f)
                return ConversationSummary(**data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def save_summary(self, summary: str, key_facts: List[str], user_preferences: List[str]):
        """Save conversation summary to long-term memory."""
        conv_summary = ConversationSummary(
            summary=summary,
            key_facts=key_facts,
            user_preferences=user_preferences,
            last_updated=0.0  # TODO: Add proper timestamp
        )
        
        with open(self.summary_file, 'w') as f:
            json.dump(asdict(conv_summary), f, indent=2)
    
    def clear_session(self):
        """Clear current session memory."""
        self.session_buffer.clear()
        if self.session_file.exists():
            self.session_file.unlink()
    
    def _load_session(self):
        """Load previous session from file."""
        if not self.session_file.exists():
            return
            
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                self.session_buffer = [Message(**msg) for msg in data]
        except (json.JSONDecodeError, KeyError):
            self.session_buffer = []
    
    def _save_session(self):
        """Save current session to file."""
        with open(self.session_file, 'w') as f:
            json.dump([asdict(msg) for msg in self.session_buffer], f, indent=2)
    
    def _summarize_and_archive(self):
        """Summarize older messages and move them to long-term memory."""
        # Keep recent messages in short-term
        recent_messages = self.session_buffer[-5:]
        
        # Archive older messages for summarization
        archived_messages = self.session_buffer[:-5]
        
        if archived_messages:
            # Summarize the archived messages and update the long-term memory
            summary, facts, preferences = self.summarizer.summarize_conversation(archived_messages)
            self.save_summary(summary, facts, preferences)
        
        # Update session buffer
        self.session_buffer = recent_messages
        self._save_session()
