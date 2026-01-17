"""
Shared types for memory module.
"""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[float] = None


@dataclass
class ConversationSummary:
    """Stores summarized conversation context."""
    summary: str
    key_facts: List[str]
    user_preferences: List[str]
    last_updated: float
