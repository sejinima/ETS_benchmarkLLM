'''metrics.py görev tanımı:
results.jsonl oku ve datasetteki doğru cevaplarla karşılaştırıp 3 veri hesaplanıcak:
1) json validity rate
2) maliyet
3) accuracy
4) precision recall f1
5) intent confusion matrix
6) latency (ortalama p50 p95 min max)
7) token stats (sum, mean, max)'''

import pandas as pd
import json
from schemas import CostBreakdown
import os
from dotenv import load_dotenv
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


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
#print(merged_df.columns)

merged_df["predicted_intent"] = merged_df["parsed"].apply(lambda x: x["intent"] if x else None)
merged_df["predicted_urgency"] = merged_df["parsed"].apply(lambda x: x["urgency"] if x else None)
merged_df["predicted_handoff"] = merged_df["parsed"].apply(lambda x: x["requiresHumanHandoff"] if x else None)

model_a_rows = merged_df[merged_df["model_name"] == model_a_name]
model_b_rows = merged_df[merged_df["model_name"] == model_b_name]

#print(f"model a = \n{model_a_rows} , \nmodel b = \n{model_b_rows}")

#accuracy hesaplama
merged_df["intent_correct"] = merged_df["expected_intent"] == merged_df["predicted_intent"]
merged_df["urgency_correct"] = merged_df["expected_urgency"] == merged_df["predicted_urgency"]
merged_df["handoff_correct"] = merged_df["expected_handoff"] == merged_df["predicted_handoff"]

accuracy_by_model = merged_df.groupby("model_name")[["intent_correct", "urgency_correct", "handoff_correct"]].mean()
print("1) ACCURACY")
print(accuracy_by_model)

#json validity rate
validity_by_model = merged_df.groupby("model_name")[["schema_valid"]].mean()
print("\n\n2) JSON VALIDITY RATE")
print(validity_by_model)

#maaliyet
token_totals_by_model = merged_df.groupby("model_name").agg(
    input_tokens_total=("input_tokens", "sum"),
    output_tokens_total=("output_tokens", "sum"),
    input_tokens_avg=("input_tokens", "mean"),
    output_tokens_avg=("output_tokens", "mean"),
    input_tokens_max=("input_tokens", "max"),
    output_tokens_max=("output_tokens", "max")
)

print("\n\n3) TOKEN STATS")
print(token_totals_by_model)

latency_stats_by_model = merged_df.groupby("model_name")["latency_ms"].agg(
    latency_avg="mean",
    latency_p50=lambda x: x.quantile(0.50),
    latency_p95=lambda x: x.quantile(0.95),
    latency_min="min",
    latency_max="max",
)
print("\n\n4) LATENCY İSTATİSTİKLERİ (ms)")
print(latency_stats_by_model)



cost_a = CostBreakdown(
    model_name = model_a_name,
    input_tokens_total = token_totals_by_model.loc[model_a_name, "input_tokens_total"],
    output_tokens_total = token_totals_by_model.loc[model_a_name, "output_tokens_total"],
    input_price_per_million = model_a_input_price,
    output_price_per_million = model_a_output_price
)

cost_b = CostBreakdown(
    model_name = model_b_name,
    input_tokens_total = token_totals_by_model.loc[model_b_name, "input_tokens_total"],
    output_tokens_total = token_totals_by_model.loc[model_b_name, "output_tokens_total"],
    input_price_per_million = model_b_input_price,
    output_price_per_million = model_b_output_price
)

print("\n\n5) TOTAL COST")
print(f"{model_a_name}: input = ${cost_a.input_cost:.4f}  output = ${cost_a.output_cost:.4f}  toplam = ${cost_a.total_cost:.4f}")
print(f"{model_b_name}: input = ${cost_b.input_cost:.4f}  output = ${cost_b.output_cost:.4f}  toplam = ${cost_b.total_cost:.4f}")


n_records_a = len(merged_df[merged_df["model_name"] == model_a_name])
n_records_b = len(merged_df[merged_df["model_name"] == model_b_name])
 
monthly_cost_a = (cost_a.total_cost / n_records_a) * 100_000
monthly_cost_b = (cost_b.total_cost / n_records_b) * 100_000

print("\n\n6) 100K MESAJ ICIN TAHMINI COST")
print(f"{model_a_name}: ${monthly_cost_a:.2f}")
print(f"{model_b_name}: ${monthly_cost_b:.2f}")



precision = precision_score(model_a_rows["expected_handoff"], model_a_rows["predicted_handoff"])
recall = recall_score(model_a_rows["expected_handoff"], model_a_rows["predicted_handoff"])
f1= f1_score(model_a_rows["expected_handoff"], model_a_rows["predicted_handoff"])
precisionb = precision_score(model_b_rows["expected_handoff"], model_b_rows["predicted_handoff"])
recallb = recall_score(model_b_rows["expected_handoff"], model_b_rows["predicted_handoff"])
f1b= f1_score(model_b_rows["expected_handoff"], model_b_rows["predicted_handoff"])


print("\n\n7) PRECISION RECALL F1 CALCULATIONS")
print()
print(f"Precision score for Model A: {precision:.2f}")
print(f"Recall score for Model A: {recall:.2f}")
print(f"F1 score for Model A: {f1:.2f}")
print()
print(f"Precision score for Model B: {precisionb:.2f}")
print(f"Recall score for Model B: {recallb:.2f}")
print(f"F1 score for Model B: {f1b:.2f}")

#intent confusion matrix

intent_labels = sorted(dataset_df["expected_intent"].unique())
confusion_a= confusion_matrix(model_a_rows["expected_intent"], model_a_rows["predicted_intent"], labels=intent_labels)
confusion_b = confusion_matrix(model_b_rows["expected_intent"], model_b_rows["predicted_intent"], labels=intent_labels)
confusion_a_df = pd.DataFrame(confusion_a, index=intent_labels, columns=intent_labels)
confusion_b_df = pd.DataFrame(confusion_b, index=intent_labels, columns=intent_labels)

print("\n\n8) CONFUSION MATRIX")
print(f"Confusion Matrix for Model A: \n{confusion_a_df}")
print()
print(f"Confusion Matrix for Model B: \n{confusion_b_df}")

