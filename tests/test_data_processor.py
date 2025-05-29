"""Tests for DataProcessor."""

import pytest
import pandas as pd
import numpy as np
from src.data_processor import DataProcessor

class TestDataProcessor:
    
    def setup_method(self):
        self.processor = DataProcessor()
        self.sample_data = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 4, 6, 8, 10],
            'target': [0, 0, 1, 1, 1]
        })
    
    def test_clean_data(self):
        """Test data cleaning removes NaN values."""
        dirty_data = self.sample_data.copy()
        dirty_data.loc[0, 'feature1'] = np.nan
        
        cleaned = self.processor.clean_data(dirty_data)
        assert len(cleaned) == 4
        assert not cleaned.isnull().any().any()
    
    def test_split_features_target(self):
        """Test feature/target splitting."""
        X, y = self.processor.split_features_target(self.sample_data)
        
        assert X.shape == (5, 2)
        assert len(y) == 5
        assert 'target' not in X.columns
    
    def test_prepare_data(self):
        """Test data preparation and splitting."""
        X, y = self.processor.split_features_target(self.sample_data)
        X_train, X_test, y_train, y_test = self.processor.prepare_data(X, y)
        
        assert len(X_train) == 3  # 70% of 5
        assert len(X_test) == 2   # 30% of 5
        assert X_train.shape[1] == 2  # 2 features
    
    def test_train_model(self):
        """Test model training."""
        X, y = self.processor.split_features_target(self.sample_data)
        X_train, X_test, y_train, y_test = self.processor.prepare_data(X, y)
        
        accuracy = self.processor.train_model(X_train, y_train)
        assert 0 <= accuracy <= 1
    
    def test_full_pipeline(self):
        """Test complete pipeline."""
        # Clean data
        clean_data = self.processor.clean_data(self.sample_data)
        
        # Split features/target
        X, y = self.processor.split_features_target(clean_data)
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.processor.prepare_data(X, y)
        
        # Train and evaluate
        train_acc = self.processor.train_model(X_train, y_train)
        test_acc = self.processor.evaluate_model(X_test, y_test)
        
        assert 0 <= train_acc <= 1
        assert 0 <= test_acc <= 1
