'''metrics.py görev tanımı:
results.jsonl oku ve datasetteki doğru cevaplarla karşılaştırıp 3 veri hesaplanıcak:
1) json validity rate
2) maliyet
3) accuracy'''

import pandas as pd
import json
from schemas import CostBreakdown
import os
from dotenv import load_dotenv


load_dotenv()
model_a_name = os.getenv("MODEL_A")
model_b_name = os.getenv("MODEL_B")
model_a_input_price = float(os.getenv("INPUT_PRICE_PER_MILLION_A"))
model_a_output_price = float(os.getenv("OUTPUT_PRICE_PER_MILLION_A"))
model_b_input_price = float(os.getenv("INPUT_PRICE_PER_MILLION_B"))
model_b_output_price = float(os.getenv("OUTPUT_PRICE_PER_MILLION_B"))



dataset_df = pd.read_csv("data/development-set.csv")
results_df = pd.read_json("output/raw/results.jsonl", lines=True)
dataset_df["id"] = dataset_df["id"].astype(str)
results_df["record_id"] = results_df["record_id"].astype(str)

merged_df = pd.merge(dataset_df, results_df, left_on="id", right_on="record_id")

merged_df["predicted_intent"] = merged_df["parsed"].apply(lambda x: x["intent"] if x else None)

merged_df["predicted_urgency"] = merged_df["parsed"].apply(lambda x: x["urgency"] if x else None)

merged_df["predicted_handoff"] = merged_df["parsed"].apply(lambda x: x["requiresHumanHandoff"] if x else None)

#accuracy hesaplama
merged_df["intent_correct"] = merged_df["expected_intent"] == merged_df["predicted_intent"]
merged_df["urgency_correct"] = merged_df["expected_urgency"] == merged_df["predicted_urgency"]
merged_df["handoff_correct"] = merged_df["expected_handoff"] == merged_df["predicted_handoff"]

accuracy_by_model = merged_df.groupby("model_name")[["intent_correct", "urgency_correct", "handoff_correct"]].mean()
print(accuracy_by_model)

#json validity rate
validity_by_model = merged_df.groupby("model_name")[["schema_valid"]].mean()
print(validity_by_model)

#maaliyet
token_totals_by_model = merged_df.groupby("model_name")[["input_tokens", "output_tokens"]].sum()
print(token_totals_by_model)

cost_a = CostBreakdown(
    model_name = model_a_name,
    input_tokens_total = token_totals_by_model.loc[model_a_name, "input_tokens"],
    output_tokens_total = token_totals_by_model.loc[model_a_name, "output_tokens"],
    input_price_per_million = model_a_input_price,
    output_price_per_million = model_a_output_price
)

cost_b = CostBreakdown(
    model_name = model_b_name,
    input_tokens_total = token_totals_by_model.loc[model_b_name, "input_tokens"],
    output_tokens_total = token_totals_by_model.loc[model_b_name, "output_tokens"],
    input_price_per_million = model_b_input_price,
    output_price_per_million = model_b_output_price
)

