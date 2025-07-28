"""Simple data processing for ML pipeline."""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

class DataProcessor:
    """Handles data loading, cleaning, and basic ML operations."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    def load_data(self, filepath):
        """Load CSV data."""
        return pd.read_csv(filepath)
    
    def clean_data(self, data):
        """Remove missing values."""
        return data.dropna()
    
    def split_features_target(self, data, target_col='target'):
        """Split data into features and target."""
        X = data.drop(columns=[target_col])
        y = data[target_col]
        return X, y
    
    def prepare_data(self, X, y, test_size=0.3):
        """Scale features and split data."""
        X_scaled = self.scaler.fit_transform(X)
        # Convert back to DataFrame to preserve column names
        X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        return train_test_split(X_scaled_df, y, test_size=test_size, random_state=42)
    
    def train_model(self, X_train, y_train):
        """Train a simple model."""
        self.model.fit(X_train, y_train)
        return self.model.score(X_train, y_train)
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance."""
        return self.model.score(X_test, y_test)