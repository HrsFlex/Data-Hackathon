import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class OutlierDetectionEngine:
    """
    Engine for detecting and handling outliers in survey data.
    Supports IQR, Z-score, and winsorization methods.
    """
    
    def __init__(self):
        self.outlier_stats = {}
    
    def detect_outliers(self, df, config):
        """
        Detect outliers based on configuration.
        
        Args:
            df (pd.DataFrame): Input dataframe
            config (dict): Configuration with detection methods per column
                          Format: {'column_name': {'method': 'iqr|zscore|winsorize', 'threshold': float}}
        
        Returns:
            pd.DataFrame: Dataframe with outliers marked/handled
            dict: Outlier detection statistics and logs
        """
        df_processed = df.copy()
        stats = {
            'total_outliers_detected': 0,
            'columns_processed': [],
            'outlier_log': []
        }
        
        try:
            for column, column_config in config.items():
                if column not in df.columns:
                    logger.warning(f"Column '{column}' not found in dataset")
                    continue
                
                if not pd.api.types.is_numeric_dtype(df[column]):
                    logger.warning(f"Column '{column}' is not numeric, skipping outlier detection")
                    continue
                
                method = column_config.get('method', 'iqr')
                action = column_config.get('action', 'flag')  # flag, remove, winsorize
                
                outlier_mask = self._detect_column_outliers(df[column], method, column_config)
                outlier_count = outlier_mask.sum()
                
                if outlier_count > 0:
                    logger.info(f"Detected {outlier_count} outliers in column '{column}' using {method}")
                    
                    # Apply the specified action
                    if action == 'remove':
                        df_processed = df_processed[~outlier_mask]
                    elif action == 'winsorize':
                        df_processed = self._winsorize_column(df_processed, column, column_config)
                    elif action == 'flag':
                        df_processed[f'{column}_outlier_flag'] = outlier_mask
                
                stats['columns_processed'].append({
                    'column': column,
                    'method': method,
                    'action': action,
                    'outlier_count': outlier_count,
                    'outlier_percentage': outlier_count / len(df) * 100
                })
                
                stats['outlier_log'].append(
                    f"Column '{column}': Detected {outlier_count} outliers using {method}, action: {action}"
                )
                
                stats['total_outliers_detected'] += outlier_count
            
            return df_processed, stats
            
        except Exception as e:
            logger.error(f"Error during outlier detection: {str(e)}")
            raise
    
    def _detect_column_outliers(self, series, method, config):
        """Detect outliers in a single column using specified method."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return pd.Series([False] * len(series), index=series.index)
        
        if method == 'iqr':
            return self._iqr_outliers(series, config.get('iqr_multiplier', 1.5))
        elif method == 'zscore':
            return self._zscore_outliers(series, config.get('zscore_threshold', 3))
        elif method == 'modified_zscore':
            return self._modified_zscore_outliers(series, config.get('modified_zscore_threshold', 3.5))
        else:
            logger.warning(f"Unknown outlier detection method: {method}")
            return pd.Series([False] * len(series), index=series.index)
    
    def _iqr_outliers(self, series, multiplier=1.5):
        """Detect outliers using Interquartile Range method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        return (series < lower_bound) | (series > upper_bound)
    
    def _zscore_outliers(self, series, threshold=3):
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(series.dropna()))
        outlier_mask = pd.Series([False] * len(series), index=series.index)
        outlier_mask.loc[series.dropna().index] = z_scores > threshold
        
        return outlier_mask
    
    def _modified_zscore_outliers(self, series, threshold=3.5):
        """Detect outliers using Modified Z-score method (using median)."""
        median = series.median()
        mad = np.median(np.abs(series.dropna() - median))
        
        if mad == 0:
            return pd.Series([False] * len(series), index=series.index)
        
        modified_z_scores = 0.6745 * (series - median) / mad
        return np.abs(modified_z_scores) > threshold
    
    def _winsorize_column(self, df, column, config):
        """Apply winsorization to a column."""
        lower_pct = config.get('lower_percentile', 0.05)
        upper_pct = config.get('upper_percentile', 0.95)
        
        lower_val = df[column].quantile(lower_pct)
        upper_val = df[column].quantile(upper_pct)
        
        df_winsorized = df.copy()
        df_winsorized[column] = df_winsorized[column].clip(lower=lower_val, upper=upper_val)
        
        return df_winsorized
    
    def suggest_outlier_method(self, df, column):
        """
        Suggest the best outlier detection method for a column.
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column name
            
        Returns:
            dict: Suggested method and reasoning
        """
        if column not in df.columns:
            return {'method': None, 'reason': 'Column not found'}
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            return {'method': None, 'reason': 'Column is not numeric'}
        
        col_data = df[column].dropna()
        
        if len(col_data) == 0:
            return {'method': None, 'reason': 'No valid data'}
        
        # Check distribution characteristics
        skewness = abs(col_data.skew())
        kurtosis = col_data.kurtosis()
        
        if skewness > 2 or kurtosis > 7:
            return {
                'method': 'modified_zscore',
                'reason': 'Highly skewed or heavy-tailed distribution'
            }
        elif skewness > 1:
            return {
                'method': 'iqr',
                'reason': 'Moderately skewed distribution'
            }
        else:
            return {
                'method': 'zscore',
                'reason': 'Normal-like distribution'
            }
    
    def get_outlier_statistics(self, df, column, method='iqr', config=None):
        """Generate detailed outlier statistics for a column."""
        if config is None:
            config = {}
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            return {'error': 'Column is not numeric'}
        
        col_data = df[column].dropna()
        
        if len(col_data) == 0:
            return {'error': 'No valid data'}
        
        outlier_mask = self._detect_column_outliers(df[column], method, config)
        outliers = df[column][outlier_mask]
        
        stats = {
            'method': method,
            'total_count': len(col_data),
            'outlier_count': outlier_mask.sum(),
            'outlier_percentage': outlier_mask.sum() / len(df) * 100,
            'distribution_stats': {
                'mean': col_data.mean(),
                'median': col_data.median(),
                'std': col_data.std(),
                'skewness': col_data.skew(),
                'kurtosis': col_data.kurtosis(),
                'min': col_data.min(),
                'max': col_data.max(),
                'q1': col_data.quantile(0.25),
                'q3': col_data.quantile(0.75)
            }
        }
        
        if len(outliers) > 0:
            stats['outlier_stats'] = {
                'outlier_min': outliers.min(),
                'outlier_max': outliers.max(),
                'outlier_mean': outliers.mean(),
                'outlier_std': outliers.std()
            }
        
        if method == 'iqr':
            iqr_multiplier = config.get('iqr_multiplier', 1.5)
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            
            stats['method_details'] = {
                'iqr_multiplier': iqr_multiplier,
                'Q1': Q1,
                'Q3': Q3,
                'IQR': IQR,
                'lower_bound': Q1 - iqr_multiplier * IQR,
                'upper_bound': Q3 + iqr_multiplier * IQR
            }
        
        return stats