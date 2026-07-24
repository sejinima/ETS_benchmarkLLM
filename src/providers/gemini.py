from src.providers.base import BaseProvider
import os
from src.schemas import BenchmarkRecord, ClassificationResult
import time
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential


class GeminiProvider(BaseProvider):
    def __init__(self, model_name: str, prompt_path: str, input_price: float, output_price: float):
        super().__init__(model_name, prompt_path, input_price,output_price)
        self.api_key=os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def classify(self, record_id:str, text:str) -> BenchmarkRecord:
        final_prompt = self.prompt_text.replace("{{MESSAGE}}", text)

        start_time=time.perf_counter()

        response=self._call_api(final_prompt)  

        end_time=time.perf_counter()

        input_tokens = response.usage_metadata.prompt_token_count

        output_tokens = response.usage_metadata.candidates_token_count

        #çağrı bitince
        latency_ms=(end_time - start_time)*1000


        error_message=None
        parsed_result=None

        try:
            parsed_result=ClassificationResult.model_validate_json(response.text)
            schema_valid=True
        except Exception as e:
            schema_valid=False
            error_message=str(e)

        return BenchmarkRecord(
            record_id=record_id,
            model_name=self.model_name,
            prompt_hash=self.prompt_hash,
            raw_response=response.text,
            schema_valid=schema_valid,
            parsed=parsed_result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            error_message=error_message
        )

    @retry (stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))

    #api çağrısı
    def _call_api(self, final_prompt) :
        response=self.client.models.generate_content(
            model=self.model_name,
            contents=final_prompt ) 

        return response
