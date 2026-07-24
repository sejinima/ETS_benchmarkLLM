from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class Intent (str, Enum): #intent olarak 10 geçerli cevap var, bunların dışı hata
    NEW_RESERVATION = "NEW_RESERVATION"
    CANCEL_RESERVATION = "CANCEL_RESERVATION"
    CHANGE_RESERVATION = "CHANGE_RESERVATION"
    REFUND ="REFUND"
    PAYMENT_PROBLEM = "PAYMENT_PROBLEM"
    HOTEL_INFORMATION = "HOTEL_INFORMATION"
    TRANSPORT_INFORMATION = "TRANSPORT_INFORMATION" 
    COMPLAINT = "COMPLAINT"
    TECHNICAL_PROBLEM = "TECHNICAL_PROBLEM"
    OTHER = "OTHER"

class Urgency(str,Enum):
    LOW = "HIGH"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

#model bana ne döndürcek, json
class ClassificationResult(BaseModel):
    intent: Intent
    urgency: Urgency
    requiresHumanHandoff: bool

    model_config = {
        "extra": "forbid"
    }

class DatasetRecord(BaseModel): #benim hazırladığım goldlabel verinin şekli
    id: str
    text: str
    expected_intent: Intent
    expected_urgency: Urgency
    expected_handoff: bool
 
    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text boş olamaz")
        return v #ekstra guvenlik icin

class BenchmarkRecord(BaseModel):
    record_id: str            # DatasetRecord.id ile eşleşir
    model_name: str           # ör. "gemini-2.0-flash"
    prompt_hash: str          # prompts/classification-v1.txt sha256
 
    raw_response: str         # modelden gelen ham metin
    schema_valid: bool        # ClassificationResult parse edilebildi mi
    parsed: Optional[ClassificationResult] = None  # parse başarılıysa dolu
 
    input_tokens: int
    output_tokens: int
    latency_ms: float
 
    timestamp: datetime = Field(default_factory=datetime.utcnow)
 
    error_message: Optional[str] = None  # parse hatası vb. varsa mesajı tut

class CostBreakdown(BaseModel):
    model_name: str
    input_tokens_total: int
    output_tokens_total: int
    input_price_per_million: float
    output_price_per_million: float
 
    @property
    def input_cost(self) -> float:
        return self.input_tokens_total / 1_000_000 * self.input_price_per_million
 
    @property
    def output_cost(self) -> float:
        return self.output_tokens_total / 1_000_000 * self.output_price_per_million
 
    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost