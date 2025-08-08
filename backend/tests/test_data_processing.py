import unittest
import pandas as pd
import numpy as np
from django.test import TestCase
from django.contrib.auth.models import User
from api.models import Survey, ProcessingJob, SurveyColumn
from data_processing.algorithms import (
    ImputationEngine, 
    OutlierDetectionEngine, 
    RuleValidationEngine, 
    WeightApplicationEngine
)


class ImputationEngineTestCase(TestCase):
    """Test cases for missing value imputation algorithms."""
    
    def setUp(self):
        self.engine = ImputationEngine()
        
        # Create test dataframe with missing values
        self.df = pd.DataFrame({
            'numeric_col': [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0],
            'categorical_col': ['A', 'B', None, 'A', 'B', None, 'C'],
            'mixed_col': [1, 2, None, 4, None, 6, 7]
        })
    
    def test_mean_imputation(self):
        """Test mean imputation for numeric columns."""
        config = {'numeric_col': {'method': 'mean'}}
        result_df, stats = self.engine.impute_missing_values(self.df, config)
        
        # Check that missing values are filled with mean
        expected_mean = self.df['numeric_col'].mean()
        self.assertFalse(result_df['numeric_col'].isnull().any())
        
        # Check statistics
        self.assertIn('columns_processed', stats)
        self.assertEqual(stats['total_missing_before'], 2)
        self.assertEqual(stats['total_missing_after'], 0)
    
    def test_median_imputation(self):
        """Test median imputation for numeric columns."""
        config = {'numeric_col': {'method': 'median'}}
        result_df, stats = self.engine.impute_missing_values(self.df, config)
        
        expected_median = self.df['numeric_col'].median()
        filled_values = result_df['numeric_col'].dropna()
        
        self.assertFalse(result_df['numeric_col'].isnull().any())
        self.assertGreater(len(stats['columns_processed']), 0)
    
    def test_mode_imputation(self):
        """Test mode imputation for categorical columns."""
        config = {'categorical_col': {'method': 'mode'}}
        result_df, stats = self.engine.impute_missing_values(self.df, config)
        
        self.assertFalse(result_df['categorical_col'].isnull().any())
        self.assertEqual(len(stats['columns_processed']), 1)
    
    def test_knn_imputation(self):
        """Test KNN imputation."""
        config = {'numeric_col': {'method': 'knn', 'n_neighbors': 3}}
        result_df, stats = self.engine.impute_missing_values(self.df, config)
        
        self.assertFalse(result_df['numeric_col'].isnull().any())
        self.assertIn('numeric_col', [col['column'] for col in stats['columns_processed']])
    
    def test_suggest_imputation_method(self):
        """Test imputation method suggestion."""
        # Test numeric column
        suggestion = self.engine.suggest_imputation_method(self.df, 'numeric_col')
        self.assertIn('method', suggestion)
        self.assertIn('reason', suggestion)
        
        # Test categorical column
        suggestion = self.engine.suggest_imputation_method(self.df, 'categorical_col')
        self.assertEqual(suggestion['method'], 'mode')
        
        # Test non-existent column
        suggestion = self.engine.suggest_imputation_method(self.df, 'nonexistent')
        self.assertIsNone(suggestion['method'])


class OutlierDetectionEngineTestCase(TestCase):
    """Test cases for outlier detection algorithms."""
    
    def setUp(self):
        self.engine = OutlierDetectionEngine()
        
        # Create test dataframe with outliers
        np.random.seed(42)
        normal_data = np.random.normal(10, 2, 100)
        outliers = [50, 60, -20, -30]  # Clear outliers
        
        self.df = pd.DataFrame({
            'data': np.concatenate([normal_data, outliers]),
            'categorical': ['A'] * 50 + ['B'] * 50 + ['C'] * 4
        })
    
    def test_iqr_outlier_detection(self):
        """Test IQR-based outlier detection."""
        config = {'data': {'method': 'iqr', 'action': 'flag', 'iqr_multiplier': 1.5}}
        result_df, stats = self.engine.detect_outliers(self.df, config)
        
        # Check that outliers are flagged
        self.assertIn('data_outlier_flag', result_df.columns)
        outlier_count = result_df['data_outlier_flag'].sum()
        self.assertGreater(outlier_count, 0)
        
        # Check statistics
        self.assertIn('columns_processed', stats)
        self.assertGreater(stats['total_outliers_detected'], 0)
    
    def test_zscore_outlier_detection(self):
        """Test Z-score based outlier detection."""
        config = {'data': {'method': 'zscore', 'action': 'flag', 'zscore_threshold': 3}}
        result_df, stats = self.engine.detect_outliers(self.df, config)
        
        self.assertIn('data_outlier_flag', result_df.columns)
        self.assertGreater(stats['total_outliers_detected'], 0)
    
    def test_outlier_removal(self):
        """Test outlier removal action."""
        original_len = len(self.df)
        config = {'data': {'method': 'iqr', 'action': 'remove', 'iqr_multiplier': 1.5}}
        result_df, stats = self.engine.detect_outliers(self.df, config)
        
        # Should have fewer rows after removing outliers
        self.assertLess(len(result_df), original_len)
    
    def test_suggest_outlier_method(self):
        """Test outlier method suggestion."""
        suggestion = self.engine.suggest_outlier_method(self.df, 'data')
        self.assertIn('method', suggestion)
        self.assertIn('reason', suggestion)
        
        # Test non-numeric column
        suggestion = self.engine.suggest_outlier_method(self.df, 'categorical')
        self.assertIsNone(suggestion['method'])


class RuleValidationEngineTestCase(TestCase):
    """Test cases for rule-based validation."""
    
    def setUp(self):
        self.engine = RuleValidationEngine()
        
        self.df = pd.DataFrame({
            'age': [25, 30, -5, 150, 40],  # Invalid: negative age, age > 120
            'income': [30000, 50000, 40000, 60000, 35000],
            'expenses': [25000, 60000, 30000, 45000, 30000],  # Invalid: expenses > income
            'email': ['a@b.com', 'invalid-email', 'c@d.org', 'e@f.net', 'bad-format']
        })
    
    def test_range_check(self):
        """Test range validation rule."""
        config = {
            'rules': [{
                'type': 'range_check',
                'name': 'age_range',
                'params': {
                    'column': 'age',
                    'min_value': 0,
                    'max_value': 120
                }
            }]
        }
        
        result_df, stats = self.engine.validate_data(self.df, config)
        
        # Check violations
        self.assertIn('age_range_violation', result_df.columns)
        violations = result_df['age_range_violation'].sum()
        self.assertEqual(violations, 2)  # -5 and 150 are invalid
        
        self.assertIn('rules_applied', stats)
        self.assertEqual(len(stats['rules_applied']), 1)
    
    def test_consistency_check(self):
        """Test consistency validation rule."""
        config = {
            'rules': [{
                'type': 'consistency_check',
                'name': 'income_expense_check',
                'params': {
                    'primary_column': 'income',
                    'related_column': 'expenses',
                    'relationship': 'greater_than'
                }
            }]
        }
        
        result_df, stats = self.engine.validate_data(self.df, config)
        
        self.assertIn('income_expense_check_violation', result_df.columns)
        violations = result_df['income_expense_check_violation'].sum()
        self.assertGreater(violations, 0)  # Should find expenses > income cases
    
    def test_format_check(self):
        """Test format validation rule."""
        config = {
            'rules': [{
                'type': 'format_check',
                'name': 'email_format',
                'params': {
                    'column': 'email',
                    'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                }
            }]
        }
        
        result_df, stats = self.engine.validate_data(self.df, config)
        
        self.assertIn('email_format_violation', result_df.columns)
        violations = result_df['email_format_violation'].sum()
        self.assertGreater(violations, 0)  # Invalid emails should be flagged
    
    def test_suggest_validation_rules(self):
        """Test validation rule suggestions."""
        suggestions = self.engine.suggest_validation_rules(self.df)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest age range validation
        age_rules = [s for s in suggestions if 'age' in s.get('name', '')]
        self.assertGreater(len(age_rules), 0)


class WeightApplicationEngineTestCase(TestCase):
    """Test cases for survey weight application."""
    
    def setUp(self):
        self.engine = WeightApplicationEngine()
        
        # Create test data with weights
        np.random.seed(42)
        self.df = pd.DataFrame({
            'income': np.random.normal(50000, 15000, 100),
            'age': np.random.normal(40, 12, 100),
            'weight': np.random.uniform(0.5, 2.0, 100),
            'employment': np.random.choice([0, 1], 100, p=[0.3, 0.7])
        })
    
    def test_weight_validation(self):
        """Test weight validation."""
        # Add some invalid weights
        invalid_weights = self.df['weight'].copy()
        invalid_weights.iloc[0] = -1  # Negative weight
        invalid_weights.iloc[1] = np.nan  # Missing weight
        
        cleaned_weights = self.engine._validate_weights(invalid_weights)
        
        # Should not have negative weights
        self.assertGreaterEqual(cleaned_weights.min(), 0)
        # Should not have missing weights
        self.assertFalse(cleaned_weights.isnull().any())
    
    def test_weighted_estimation(self):
        """Test weighted statistical estimation."""
        config = {
            'weight_column': 'weight',
            'estimates': [
                {
                    'variable': 'income',
                    'statistic': 'mean',
                    'confidence_level': 0.95
                },
                {
                    'variable': 'employment',
                    'statistic': 'proportion',
                    'confidence_level': 0.95
                }
            ]
        }
        
        results = self.engine.apply_weights(self.df, config)
        
        # Check structure
        self.assertIn('weighted', results)
        self.assertIn('unweighted', results)
        self.assertIn('weight_statistics', results)
        
        # Check estimates
        self.assertIn('income_mean', results['weighted'])
        self.assertIn('employment_proportion', results['weighted'])
        
        # Check that we have confidence intervals
        income_result = results['weighted']['income_mean']
        self.assertIn('confidence_interval', income_result)
        self.assertIn('margin_of_error', income_result)
    
    def test_design_effect_calculation(self):
        """Test design effect calculation."""
        variable = self.df['income']
        weights = self.df['weight']
        
        design_effect = self.engine.calculate_design_effect(variable, weights)
        
        self.assertIsInstance(design_effect, float)
        self.assertGreater(design_effect, 0)
    
    def test_estimates_summary(self):
        """Test estimates comparison summary."""
        # First create estimates
        config = {
            'weight_column': 'weight',
            'estimates': [
                {
                    'variable': 'income',
                    'statistic': 'mean',
                    'confidence_level': 0.95
                }
            ]
        }
        
        estimates = self.engine.apply_weights(self.df, config)
        summary = self.engine.create_estimates_summary(estimates)
        
        self.assertIn('estimates_comparison', summary)
        self.assertIn('weight_effectiveness', summary)


class IntegrationTestCase(TestCase):
    """Integration tests for the complete data processing pipeline."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test survey
        self.survey = Survey.objects.create(
            name='Test Survey',
            description='Test survey for integration testing',
            survey_type='household',
            uploaded_by=self.user,
            file_type='csv',
            file_size=1024,
            total_rows=100,
            total_columns=5,
            has_weights=True,
            weight_column='survey_weight'
        )
        
        # Create survey columns
        columns_data = [
            {'name': 'respondent_id', 'data_type': 'numeric', 'position': 0},
            {'name': 'age', 'data_type': 'numeric', 'position': 1},
            {'name': 'income', 'data_type': 'numeric', 'position': 2},
            {'name': 'survey_weight', 'data_type': 'numeric', 'position': 3, 'is_weight': True},
            {'name': 'region', 'data_type': 'categorical', 'position': 4}
        ]
        
        for col_data in columns_data:
            SurveyColumn.objects.create(survey=self.survey, **col_data)
    
    def test_processing_job_creation(self):
        """Test creating and configuring a processing job."""
        job = ProcessingJob.objects.create(
            survey=self.survey,
            user=self.user,
            configuration={
                'imputation': {
                    'age': {'method': 'mean'},
                    'income': {'method': 'median'}
                },
                'outliers': {
                    'income': {'method': 'iqr', 'action': 'flag'}
                },
                'validation': {
                    'rules': [{
                        'type': 'range_check',
                        'name': 'age_range',
                        'params': {'column': 'age', 'min_value': 0, 'max_value': 120}
                    }]
                }
            }
        )
        
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.survey, self.survey)
        self.assertEqual(job.user, self.user)
        
        # Add processing steps
        steps = [
            'Data Validation',
            'Data Cleaning', 
            'Missing Value Imputation',
            'Outlier Detection',
            'Rule-based Validation',
            'Weight Application',
            'Statistical Estimation',
            'Report Generation'
        ]
        
        for i, step_name in enumerate(steps):
            job.add_step(step_name, f"Step {i+1}: {step_name}")
        
        self.assertEqual(job.steps.count(), 8)
    
    def test_data_processing_pipeline(self):
        """Test the complete data processing pipeline."""
        # Create test data
        np.random.seed(42)
        test_data = pd.DataFrame({
            'respondent_id': range(1, 101),
            'age': np.random.normal(40, 15, 100),
            'income': np.random.normal(50000, 20000, 100),
            'survey_weight': np.random.uniform(0.5, 2.0, 100),
            'region': np.random.choice(['North', 'South', 'East', 'West'], 100)
        })
        
        # Introduce some missing values and outliers
        test_data.loc[5:10, 'age'] = np.nan
        test_data.loc[15:20, 'income'] = np.nan
        test_data.loc[0, 'age'] = -5  # Invalid age
        test_data.loc[1, 'income'] = 500000  # Outlier income
        
        # Test imputation
        imputation_engine = ImputationEngine()
        imputation_config = {
            'age': {'method': 'mean'},
            'income': {'method': 'median'}
        }
        
        cleaned_data, imp_stats = imputation_engine.impute_missing_values(
            test_data, imputation_config
        )
        
        self.assertEqual(imp_stats['total_missing_after'], 0)
        
        # Test outlier detection
        outlier_engine = OutlierDetectionEngine()
        outlier_config = {
            'income': {'method': 'iqr', 'action': 'flag', 'iqr_multiplier': 1.5}
        }
        
        flagged_data, out_stats = outlier_engine.detect_outliers(
            cleaned_data, outlier_config
        )
        
        self.assertGreater(out_stats['total_outliers_detected'], 0)
        
        # Test validation
        validation_engine = RuleValidationEngine()
        validation_config = {
            'rules': [{
                'type': 'range_check',
                'name': 'age_validation',
                'params': {
                    'column': 'age',
                    'min_value': 0,
                    'max_value': 120
                }
            }]
        }
        
        validated_data, val_stats = validation_engine.validate_data(
            flagged_data, validation_config
        )
        
        self.assertIn('rules_applied', val_stats)
        
        # Test weight application
        weight_engine = WeightApplicationEngine()
        weight_config = {
            'weight_column': 'survey_weight',
            'estimates': [
                {
                    'variable': 'age',
                    'statistic': 'mean',
                    'confidence_level': 0.95
                },
                {
                    'variable': 'income',
                    'statistic': 'mean',
                    'confidence_level': 0.95
                }
            ]
        }
        
        weight_results = weight_engine.apply_weights(validated_data, weight_config)
        
        self.assertIn('weighted', weight_results)
        self.assertIn('unweighted', weight_results)
        self.assertIn('age_mean', weight_results['weighted'])
        self.assertIn('income_mean', weight_results['weighted'])


if __name__ == '__main__':
    unittest.main()