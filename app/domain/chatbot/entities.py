from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

@dataclass
class Chatbot:
    """
    Domain entity representing a chatbot configuration.
    """
    name: str
    model_name: str
    llm_config: Dict[str, Any]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(self, name: Optional[str] = None, model_name: Optional[str] = None, llm_config: Optional[Dict[str, Any]] = None) -> None:
        if name:
            self.name = name
        if model_name:
            self.model_name = model_name
        if llm_config:
            self.llm_config = llm_config
        self.updated_at = datetime.now()
