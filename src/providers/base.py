from abc import ABC, abstractmethod
from hashlib import sha256
from src.schemas import BenchmarkRecord

class BaseProvider(ABC):
    def __init__(self, model_name:str, prompt_path:str, input_price:float, output_price:float):
        self.model_name=model_name
        self.prompt_path=prompt_path
        self.input_price=input_price
        self.output_price=output_price

        with open(self.prompt_path, 'r') as f:
            self.prompt_text = f.read()

        self.prompt_hash=sha256(self.prompt_text.encode()).hexdigest()

    @abstractmethod
    def classify(self, record_id:str, text:str) -> BenchmarkRecord:
        pass



