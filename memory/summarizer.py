"""
Conversation summarizer for long-term memory management.
"""

from typing import List
from llm.ollama_client import OllamaClient
from memory.types import Message


class ConversationSummarizer:
    """Handles summarization of conversation history."""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client
    
    def summarize_conversation(self, messages: List[Message]) -> tuple[str, List[str], List[str]]:
        """
        Summarize a conversation to extract key information.
        
        Returns:
            Tuple of (summary, key_facts, user_preferences)
        """
        if not messages:
            return "", [], []
        
        # Build conversation text
        conversation_text = "\n".join([
            f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
            for msg in messages
        ])
        
        # Create summarization prompt
        prompt = f"""
Please summarize the following conversation in under 200 tokens.
Extract:
1. Main summary of the conversation
2. Key facts mentioned
3. User preferences or interests expressed

Conversation:
{conversation_text}

Format your response as:
SUMMARY: [brief summary]
FACTS: [comma-separated list of key facts]
PREFERENCES: [comma-separated list of user preferences or interests]

Keep each section concise.
"""
        
        response = self.llm.generate(
            prompt=prompt,
            system="You are a helpful assistant that summarizes conversations concisely.",
            temperature=0.3
        )
        
        # Parse the response
        summary = ""
        facts = []
        preferences = []
        
        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith('SUMMARY:'):
                summary = line[len('SUMMARY:'):].strip()
            elif line.startswith('FACTS:'):
                facts_str = line[len('FACTS:'):].strip()
                if facts_str:
                    facts = [fact.strip() for fact in facts_str.split(',')]
            elif line.startswith('PREFERENCES:'):
                prefs_str = line[len('PREFERENCES:'):].strip()
                if prefs_str:
                    preferences = [pref.strip() for pref in prefs_str.split(',')]
        
        return summary, facts, preferences