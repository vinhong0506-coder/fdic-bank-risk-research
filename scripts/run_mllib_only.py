from pathlib import Path
import pandas as pd
from fdic_pipeline.model import run_spark_mllib_demo

feature_file = Path("data_processed/features_pit_spark.parquet")
out_dir = Path("artifacts/model")
out_dir.mkdir(parents=True, exist_ok=True)

dictionary_file = Path(
    "artifacts/features/feature_dictionary.csv"
)

if not feature_file.exists():
    raise FileNotFoundError(feature_file)

dictionary = pd.read_csv(dictionary_file)

base_features = dictionary["feature"].tolist()

feature_cols = [
    col
    for feature in base_features
    for col in (feature + "_isna", feature)
]

print("Feature count:", len(feature_cols), flush=True)
print("Starting Spark MLlib...", flush=True)

run_spark_mllib_demo(
    feature_file,
    feature_cols,
    out_dir
)

result = pd.read_csv(out_dir / "spark_mllib_demo.csv")

print("\n=== SPARK MLLIB RESULTS ===")
print(result.to_string(index=False))

if "Status" in result.columns:
    raise RuntimeError("Spark MLlib was skipped or failed.")

print("\nSPARK MLLIB: PASS")
