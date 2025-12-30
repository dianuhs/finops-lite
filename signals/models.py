from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Signal:
    id: str
    title: str
    severity: str  # info | warn | high
    confidence: str  # low | medium | high
    owner: str  # FinOps | Engineering | Shared
    evidence: Dict[str, Any]
    why_it_matters: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
