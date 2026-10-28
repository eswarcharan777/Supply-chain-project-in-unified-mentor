"""Historical delay-risk model utilities for the dashboard and API."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURE_COLUMNS = [
    "Days for shipment (scheduled)", "Shipping Mode", "Market", "Order Region",
    "Customer Segment", "Category Name", "Order Item Discount Rate",
    "Order Item Product Price", "Order Item Quantity",
]
CATEGORICAL_COLUMNS = ["Shipping Mode", "Market", "Order Region", "Customer Segment", "Category Name"]
NUMERIC_COLUMNS = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_COLUMNS]


@dataclass
class DelayModel:
    pipeline: Pipeline
    accuracy: float
    roc_auc: float


def _feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    frame = data[FEATURE_COLUMNS].copy()
    for column in CATEGORICAL_COLUMNS:
        frame[column] = frame[column].fillna("Unknown").astype(str)
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    return frame


def train_delay_model(data: pd.DataFrame) -> DelayModel:
    """Train a non-leaking historical model using fields available before delivery."""
    features = _feature_frame(data)
    target = data["is_delayed"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    preprocessing = ColumnTransformer(
        [
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
            ("numbers", StandardScaler(), NUMERIC_COLUMNS),
        ]
    )
    pipeline = Pipeline(
        [("preprocessing", preprocessing), ("classifier", LogisticRegression(max_iter=300))]
    )
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    return DelayModel(
        pipeline=pipeline,
        accuracy=float(accuracy_score(y_test, predictions)),
        roc_auc=float(roc_auc_score(y_test, probabilities)),
    )


def prediction_input_defaults(data: pd.DataFrame) -> dict[str, object]:
    """Return safe defaults for the dashboard prediction form."""
    defaults: dict[str, object] = {}
    for column in CATEGORICAL_COLUMNS:
        values = data[column].dropna().astype(str)
        defaults[column] = values.mode().iloc[0] if not values.empty else "Unknown"
    for column in NUMERIC_COLUMNS:
        defaults[column] = float(pd.to_numeric(data[column], errors="coerce").median())
    return defaults


def predict_delay_probability(model: DelayModel, values: dict[str, object]) -> float:
    frame = _feature_frame(pd.DataFrame([values]))
    return float(model.pipeline.predict_proba(frame)[:, 1][0])
