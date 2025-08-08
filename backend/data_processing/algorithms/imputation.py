import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
import logging

logger = logging.getLogger(__name__)


class ImputationEngine:
    """
    Engine for handling missing value imputation in survey data.
    Supports mean, median, mode, and KNN imputation methods.
    """
    
    def __init__(self):
        self.imputers = {}
        self.encoders = {}
        
    def impute_missing_values(self, df, config):
        """
        Impute missing values based on configuration.
        
        Args:
            df (pd.DataFrame): Input dataframe
            config (dict): Configuration with imputation methods per column
                          Format: {'column_name': {'method': 'mean|median|mode|knn'}}
        
        Returns:
            pd.DataFrame: Dataframe with imputed values
            dict: Imputation statistics and logs
        """
        df_imputed = df.copy()
        stats = {
            'total_missing_before': df.isnull().sum().sum(),
            'columns_processed': [],
            'imputation_log': []
        }
        
        try:
            for column, column_config in config.items():
                if column not in df.columns:
                    logger.warning(f"Column '{column}' not found in dataset")
                    continue
                    
                method = column_config.get('method', 'mean')
                missing_count = df[column].isnull().sum()
                
                if missing_count == 0:
                    continue
                    
                logger.info(f"Imputing {missing_count} missing values in column '{column}' using {method}")
                
                if method == 'mean' and pd.api.types.is_numeric_dtype(df[column]):
                    df_imputed[column] = df_imputed[column].fillna(df[column].mean())
                    
                elif method == 'median' and pd.api.types.is_numeric_dtype(df[column]):
                    df_imputed[column] = df_imputed[column].fillna(df[column].median())
                    
                elif method == 'mode':
                    mode_value = df[column].mode()
                    if len(mode_value) > 0:
                        df_imputed[column] = df_imputed[column].fillna(mode_value[0])
                    else:
                        logger.warning(f"No mode found for column '{column}', skipping")
                        
                elif method == 'knn':
                    df_imputed = self._knn_imputation(df_imputed, column, column_config.get('n_neighbors', 5))
                    
                else:
                    logger.warning(f"Unsupported imputation method '{method}' for column '{column}'")
                    continue
                
                stats['columns_processed'].append({
                    'column': column,
                    'method': method,
                    'missing_count': missing_count,
                    'imputed_count': missing_count - df_imputed[column].isnull().sum()
                })
                
                stats['imputation_log'].append(
                    f"Column '{column}': Imputed {missing_count} values using {method}"
                )
            
            stats['total_missing_after'] = df_imputed.isnull().sum().sum()
            stats['total_imputed'] = stats['total_missing_before'] - stats['total_missing_after']
            
            return df_imputed, stats
            
        except Exception as e:
            logger.error(f"Error during imputation: {str(e)}")
            raise
    
    def _knn_imputation(self, df, target_column, n_neighbors=5):
        """Perform KNN imputation for a specific column."""
        try:
            # Prepare data for KNN imputation
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if target_column not in numeric_columns:
                # Convert categorical to numeric for KNN
                if target_column not in self.encoders:
                    self.encoders[target_column] = LabelEncoder()
                    non_null_values = df[target_column].dropna()
                    if len(non_null_values) > 0:
                        self.encoders[target_column].fit(non_null_values)
                    else:
                        return df  # Cannot encode empty series
                
                # Encode non-null values
                mask = df[target_column].notna()
                df.loc[mask, target_column] = self.encoders[target_column].transform(df.loc[mask, target_column])
            
            # Use numeric columns for KNN
            knn_data = df[numeric_columns].copy()
            
            # Perform KNN imputation
            imputer = KNNImputer(n_neighbors=n_neighbors)
            imputed_data = imputer.fit_transform(knn_data)
            
            # Replace the target column
            target_idx = numeric_columns.index(target_column)
            df[target_column] = imputed_data[:, target_idx]
            
            # Decode if it was categorical
            if target_column in self.encoders:
                df[target_column] = df[target_column].round().astype(int)
                df[target_column] = self.encoders[target_column].inverse_transform(df[target_column])
            
            return df
            
        except Exception as e:
            logger.error(f"KNN imputation failed for column {target_column}: {str(e)}")
            return df
    
    def suggest_imputation_method(self, df, column):
        """
        Suggest the best imputation method for a column based on its characteristics.
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column name
            
        Returns:
            dict: Suggested method and reasoning
        """
        if column not in df.columns:
            return {'method': None, 'reason': 'Column not found'}
        
        col_data = df[column]
        missing_pct = col_data.isnull().sum() / len(col_data)
        
        if missing_pct == 0:
            return {'method': None, 'reason': 'No missing values'}
        
        if missing_pct > 0.5:
            return {
                'method': 'drop_column',
                'reason': f'Too many missing values ({missing_pct:.1%})'
            }
        
        if pd.api.types.is_numeric_dtype(col_data):
            if col_data.nunique() / len(col_data.dropna()) < 0.1:
                return {'method': 'mode', 'reason': 'Numeric but categorical-like distribution'}
            elif missing_pct < 0.1:
                return {'method': 'mean', 'reason': 'Low missing percentage, numeric data'}
            else:
                return {'method': 'knn', 'reason': 'Higher missing percentage, numeric data'}
        else:
            return {'method': 'mode', 'reason': 'Categorical data'}
    
    def get_imputation_statistics(self, df_original, df_imputed):
        """Generate detailed statistics about the imputation process."""
        stats = {
            'summary': {
                'total_rows': len(df_original),
                'total_columns': len(df_original.columns),
                'missing_before': df_original.isnull().sum().sum(),
                'missing_after': df_imputed.isnull().sum().sum()
            },
            'column_details': []
        }
        
        for column in df_original.columns:
            missing_before = df_original[column].isnull().sum()
            missing_after = df_imputed[column].isnull().sum()
            
            column_stats = {
                'column': column,
                'missing_before': missing_before,
                'missing_after': missing_after,
                'imputed_count': missing_before - missing_after,
                'missing_pct_before': missing_before / len(df_original),
                'missing_pct_after': missing_after / len(df_imputed)
            }
            
            stats['column_details'].append(column_stats)
        
        return stats