'''benchmark görevi, projenin yöneticisidir. csvyi okuyup her satırı iki modele de gönderip
sonuçları diske yazar. genel akış:
1) .env oku (api key, model isimleri, fiyatlar)
2) iki geminiprovider nesnesi oluştur model a ve model b için
3) datasetcsvyi oku her satırı datasetrecord ile doğrular
4) checkpoint, daha önce işlenmiş kayıtları tespit et ve atla
5) her kayıt için iki provider çağır
6) sonuçları (benchmarkrecord) diske yaz (her çağrıdan sonra hemen sonra yazcan, yarıda kesilirse veri kaybolmasın diye)
'''

from dotenv import load_dotenv
import os
from src.providers.gemini import GeminiProviderProvider



load_dotenv()
model_a_name=os.getenv("MODEL_A")
model_b_name=os.getenv("MODEL_B")
model_a_input_price= float(os.getenv("INPUT_PRICE_PER_MILLION_A"))
model_a_output_price= float(os.getenv("OUTPUT_PRICE_PER_MILLION_A"))
model_b_input_price= float(os.getenv("INPUT_PRICE_PER_MILLION_B"))
model_b_output_price= float(os.getenv("OUTPUT_PRICE_PER_MILLION_B"))

model_a_object = GeminiProvider(
    model_name: gemini-2.0-flash
    prompt_path: prompts/classification-v1.txt
    input_price:
    output_price:
)

model_b_object = GeminiProvider(
    model_name: gemini-2.0-pro
    prompt_path: prompts/classification-v1.txt
    input_price:
    output_price:
)

