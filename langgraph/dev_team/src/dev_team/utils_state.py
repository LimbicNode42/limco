from dataclasses import dataclass
from typing import Dict, Any, Optional
import base64
from datetime import datetime

@dataclass
class LangGraphImage:
    """Optimized for LangGraph state serialization"""
    name: str
    base64_data: str  # Serializable string
    format: str
    metadata: Dict[str, Any]
    created_at: str  # ISO format string for serialization
    created_by: str
    
    @classmethod
    def from_file(cls, name: str, file_path: str, created_by: str, **metadata):
        """Create from file path"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        base64_encoded = base64.b64encode(data).decode('utf-8')
        format_ext = file_path.split('.')[-1].lower()
        
        return cls(
            name=name,
            base64_data=base64_encoded,
            format=format_ext,
            metadata=metadata,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by
        )
    
    def to_bytes(self) -> bytes:
        """Convert back to bytes when needed"""
        return base64.b64decode(self.base64_data)
    
    def to_data_url(self) -> str:
        """For web display"""
        return f"data:image/{self.format};base64,{self.base64_data}"