import sys
import numpy as np
import lightgbm as lgb

x_train = np.load(
    sys.argv[1],
    mmap_mode="r",
    allow_pickle=False
)

y_train = np.load(
    sys.argv[2],
    mmap_mode="r",
    allow_pickle=False
)

x_valid = np.load(
    sys.argv[3],
    mmap_mode="r",
    allow_pickle=False
)

if x_train.ndim != 2 or x_valid.ndim != 2:
    raise RuntimeError("Invalid matrix dimensions")

if x_train.shape[1] != x_valid.shape[1]:
    raise RuntimeError("Feature count mismatch")

if len(y_train) != len(x_train):
    raise RuntimeError("Label count mismatch")

if not np.isin(y_train, [0.0, 1.0]).all():
    raise RuntimeError("Invalid binary labels")

print(
    "  [WORKER] Train:", x_train.shape,
    "Val:", x_valid.shape,
    "X dtype:", x_train.dtype,
    "y dtype:", y_train.dtype,
    flush=True
)

model = lgb.LGBMClassifier(
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=31,
    subsample_for_bin=50000,
    colsample_bytree=0.8,
    subsample=0.8,
    min_child_samples=100,
    random_state=42,
    n_jobs=1,
    force_col_wise=True,
    histogram_pool_size=64,
    verbose=-1,
)

model.fit(x_train, y_train)

pred = model.predict_proba(x_valid)[:, 1]

if not np.isfinite(pred).all():
    raise RuntimeError("Invalid predictions")

np.save(
    sys.argv[4],
    pred.astype(np.float64),
    allow_pickle=False
)

print(
    "  [WORKER PASS]",
    len(pred),
    "predictions saved",
    flush=True
)
