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
from src.providers.gemini import GeminiProvider
import pandas as pd
from src.schemas import DatasetRecord
import json
import time

HARD_RECORD_IDS = ["31", "32", "33", "34", "35", "36", "37", 
                   "38", "49", "50", "51", "52", "53", "57", "59"]

load_dotenv()
model_a_name=os.getenv("MODEL_A")
model_b_name=os.getenv("MODEL_B")
model_a_input_price= float(os.getenv("INPUT_PRICE_PER_MILLION_A"))
model_a_output_price= float(os.getenv("OUTPUT_PRICE_PER_MILLION_A"))
model_b_input_price= float(os.getenv("INPUT_PRICE_PER_MILLION_B"))
model_b_output_price= float(os.getenv("OUTPUT_PRICE_PER_MILLION_B"))

model_a_object = GeminiProvider(
    model_name = model_a_name,
    prompt_path= "prompts/classification-v1.txt",
    input_price= model_a_input_price,
    output_price= model_a_output_price
)

model_b_object = GeminiProvider(
    model_name= model_b_name,
    prompt_path= "prompts/classification-v1.txt",
    input_price= model_b_input_price,
    output_price= model_b_output_price
)

os.makedirs("output/raw", exist_ok=True)
df = pd.read_csv("data/development-set.csv")
df["id"] = df["id"].astype(str)

providers=[model_a_object, model_b_object]





processed = set()
if os.path.exists("output/raw/results.jsonl"):
    with open("output/raw/results.jsonl", "r") as f:
        for line in f:
            data = json.loads(line)
            key= data["record_id"] + "_" + data["model_name"]
            processed.add(key)

for index, row in df.iterrows():
    record = DatasetRecord(
        id=str(row["id"]),
        text=row["text"],
        expected_intent=row["expected_intent"],
        expected_urgency=row["expected_urgency"],
        expected_handoff=row["expected_handoff"]
    )

    for provider in providers:
        key = record.id+"_"+provider.model_name 
        if key in processed:
            continue

        result=provider.classify(record_id=record.id, text=record.text)

        with open ("output/raw/results.jsonl", "a") as f:
            f.write(result.model_dump_json()+ "\n")
            processed.add(key)

        time.sleep(5)

print("main run done. \n")


os.makedirs("output/raw", exist_ok=True)
 
consistency_processed = set()
if os.path.exists("output/raw/consistency.jsonl"):
    with open("output/raw/consistency.jsonl", "r") as f:
        for line in f:
            data = json.loads(line)
            # anahtar: record_id + model_name + repetition numarası
            key = data["record_id"] + "_" + data["model_name"] + "_" + str(data["repetition"])
            consistency_processed.add(key)


for hard_id in HARD_RECORD_IDS:
    matching_row = df[df["id"]==hard_id]


    if len(matching_row)==0:
        print(f"uyarı!!!!!!: {hard_id} idsi olan kayırlar bu datasette yok, atlıyoruz")
        continue

    hard_text = matching_row.iloc[0]["text"]

    for provider in providers:
        for repetition in [1, 2, 3]:
            key = hard_id + "_" + provider.model_name + "_" + str(repetition)
            if key in consistency_processed:
                continue
 
            result = provider.classify(record_id=hard_id, text=hard_text)

            result_dict = json.loads(result.model_dump_json())
            result_dict["repetition"] = repetition
 
            with open("output/raw/consistency.jsonl", "a") as f:
                f.write(json.dumps(result_dict) + "\n")
                consistency_processed.add(key)
 
            time.sleep(5)

print("consistency run done.\n")

