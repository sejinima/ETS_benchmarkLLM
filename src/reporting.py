import pandas as pd
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix


load_dotenv()
model_a_name = os.getenv("MODEL_A")
model_b_name = os.getenv("MODEL_B")

dataset_df = pd.read_csv("data/development-set.csv")
results_df = pd.read_json("output/raw/results.jsonl", lines=True)
dataset_df["id"] = dataset_df["id"].astype(str)
results_df["record_id"] = results_df["record_id"].astype(str)

merged_df = pd.merge(dataset_df, results_df, left_on="id", right_on="record_id")

merged_df["predicted_intent"] = merged_df["parsed"].apply(lambda x: x["intent"] if x else None)
merged_df["predicted_urgency"] = merged_df["parsed"].apply(lambda x: x["urgency"] if x else None)
merged_df["predicted_handoff"] = merged_df["parsed"].apply(lambda x: x["requiresHumanHandoff"] if x else None)

merged_df["intent_correct"] = merged_df["expected_intent"] == merged_df["predicted_intent"]
merged_df["urgency_correct"] = merged_df["expected_urgency"] == merged_df["predicted_urgency"]
merged_df["handoff_correct"] = merged_df["expected_handoff"] == merged_df["predicted_handoff"]

os.makedirs("report/charts", exist_ok=True)

accuracy_by_model = merged_df.groupby("model_name")[["intent_correct", "urgency_correct", "handoff_correct"]].mean()

accuracy_by_model.plot(kind="bar", figsize=(8, 5), title="Model Accuracy Karşılaştırması")
plt.ylabel("Accuracy")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("report/charts/accuracy_comparison.png")
plt.close()

latency_stats_by_model = merged_df.groupby("model_name")["latency_ms"].agg(
    latency_avg="mean",
    latency_p50=lambda x: x.quantile(0.50),
    latency_p95=lambda x: x.quantile(0.95),
    latency_min="min",
    latency_max="max",
)

latency_stats_by_model[["latency_p50", "latency_p95"]].plot(kind="bar", figsize=(8, 5), title="Model Latency Karşılaştırması (p50 / p95)")
plt.ylabel("Latency (ms)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("report/charts/latency_comparison.png")
plt.close()

model_a_rows = merged_df[merged_df["model_name"] == model_a_name]
model_b_rows = merged_df[merged_df["model_name"] == model_b_name]

intent_labels = sorted(dataset_df["expected_intent"].unique())
confusion_a = confusion_matrix(model_a_rows["expected_intent"], model_a_rows["predicted_intent"], labels=intent_labels)
confusion_b = confusion_matrix(model_b_rows["expected_intent"], model_b_rows["predicted_intent"], labels=intent_labels)


fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(confusion_a, cmap="Blues")

ax.set_xticks(range(len(intent_labels)))
ax.set_yticks(range(len(intent_labels)))
ax.set_xticklabels(intent_labels, rotation=45, ha="right")
ax.set_yticklabels(intent_labels)
ax.set_xlabel("Tahmin Edilen Intent")
ax.set_ylabel("Gerçek Intent")
ax.set_title(f"Confusion Matrix - {model_a_name}")

for i in range(len(intent_labels)):
    for j in range(len(intent_labels)):
        ax.text(j, i, confusion_a[i, j], ha="center", va="center")

plt.tight_layout()
plt.savefig("report/charts/confusion_matrix_model_a.png")
plt.close()



fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(confusion_b, cmap="Blues")

ax.set_xticks(range(len(intent_labels)))
ax.set_yticks(range(len(intent_labels)))
ax.set_xticklabels(intent_labels, rotation=45, ha="right")
ax.set_yticklabels(intent_labels)
ax.set_xlabel("Tahmin Edilen Intent")
ax.set_ylabel("Gerçek Intent")
ax.set_title(f"Confusion Matrix - {model_b_name}")

for i in range(len(intent_labels)):
    for j in range(len(intent_labels)):
        ax.text(j, i, confusion_b[i, j], ha="center", va="center")

plt.tight_layout()
plt.savefig("report/charts/confusion_matrix_model_b.png")
plt.close()

model_a_input_price = float(os.getenv("INPUT_PRICE_PER_MILLION_A"))
model_a_output_price = float(os.getenv("OUTPUT_PRICE_PER_MILLION_A"))
model_b_input_price = float(os.getenv("INPUT_PRICE_PER_MILLION_B"))
model_b_output_price = float(os.getenv("OUTPUT_PRICE_PER_MILLION_B"))

token_totals_by_model = merged_df.groupby("model_name").agg(
    input_tokens_total=("input_tokens", "sum"),
    output_tokens_total=("output_tokens", "sum"),
    input_tokens_avg=("input_tokens", "mean"),
    output_tokens_avg=("output_tokens", "mean"),
    input_tokens_max=("input_tokens", "max"),
    output_tokens_max=("output_tokens", "max")
)

from schemas import CostBreakdown

cost_a = CostBreakdown(
    model_name=model_a_name,
    input_tokens_total=token_totals_by_model.loc[model_a_name, "input_tokens_total"],
    output_tokens_total=token_totals_by_model.loc[model_a_name, "output_tokens_total"],
    input_price_per_million=model_a_input_price,
    output_price_per_million=model_a_output_price
)

cost_b = CostBreakdown(
    model_name=model_b_name,
    input_tokens_total=token_totals_by_model.loc[model_b_name, "input_tokens_total"],
    output_tokens_total=token_totals_by_model.loc[model_b_name, "output_tokens_total"],
    input_price_per_million=model_b_input_price,
    output_price_per_million=model_b_output_price
)

plt.figure(figsize=(8, 5))
plt.bar([model_a_name, model_b_name], [cost_a.total_cost, cost_b.total_cost], color=["steelblue", "darkorange"])
plt.ylabel("Toplam Maliyet ($)")
plt.title("Model Bazında Benchmark Maliyeti")
plt.tight_layout()
plt.savefig("report/charts/cost_comparison.png")
plt.close()