"""
Chat mode handler for conversational interactions.
Handles chat-specific prompts and memory management.
"""

from typing import List, Optional
from memory.manager import MemoryManager
from memory.types import Message
from llm.ollama_client import OllamaClient
from llm.prompts import BASE_SYSTEM_PROMPT


class ChatModeHandler:
    """Handles chat mode conversations with memory management."""
    
    def __init__(self, llm_client: OllamaClient, memory_manager: MemoryManager):
        self.llm = llm_client
        self.memory = memory_manager
        
        # Chat-specific system prompt
        self.chat_system_prompt = f"""{BASE_SYSTEM_PROMPT}

You are now in CHAT MODE. You can engage in general conversation with the user.

CHAT MODE RULES:
- You can discuss any topic the user wants
- You can answer questions, explain concepts, or have casual conversation
- You are still Pratik's local AI agent, but you're being conversational
- Be helpful, friendly, and informative
- You can reference previous conversation context when relevant

Remember: You're having a conversation, not executing coding tasks.
""".strip()
    
    def process_chat(self, user_input: str) -> str:
        """Process a chat message and return response."""
        # Add user message to memory
        self.memory.add_message("user", user_input)
        
        # Build context-aware prompt
        prompt = self._build_chat_prompt(user_input)
        
        # Generate response
        response = self.llm.generate(
            prompt=prompt,
            system=self.chat_system_prompt,
            temperature=0.7  # More creative for chat
        )
        
        # Add assistant response to memory
        self.memory.add_message("assistant", response)
        
        return response
    
    def _build_chat_prompt(self, user_input: str) -> str:
        """Build a context-aware prompt for chat mode."""
        # Get recent conversation history
        recent_messages = self.memory.get_recent_context(n=8)
        
        # Get long-term summary
        summary = self.memory.get_summary()
        
        # Build prompt with context
        prompt_parts = []
        
        # Add summary context if available
        if summary:
            prompt_parts.append("CONVERSATION CONTEXT:")
            prompt_parts.append(f"Summary: {summary.summary}")
            if summary.user_preferences:
                prompt_parts.append(f"User preferences: {', '.join(summary.user_preferences)}")
            if summary.key_facts:
                prompt_parts.append(f"Key facts: {', '.join(summary.key_facts)}")
            prompt_parts.append("")
        
        # Add recent conversation
        if recent_messages:
            prompt_parts.append("RECENT CONVERSATION:")
            for msg in recent_messages:
                if msg.role == "user":
                    prompt_parts.append(f"User: {msg.content}")
                else:
                    prompt_parts.append(f"Assistant: {msg.content}")
            prompt_parts.append("")
        
        # Add current user input
        prompt_parts.append(f"User: {user_input}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def clear_chat_history(self):
        """Clear the current chat session."""
        self.memory.clear_session()
