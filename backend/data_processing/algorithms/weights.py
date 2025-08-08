import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class WeightApplicationEngine:
    """
    Engine for applying survey weights and calculating statistical estimates.
    Supports design weights, population parameter estimation, and margin of error calculations.
    """
    
    def __init__(self):
        self.weight_stats = {}
        self.estimates = {}
    
    def apply_weights(self, df, config):
        """
        Apply survey weights and calculate weighted statistics.
        
        Args:
            df (pd.DataFrame): Input dataframe
            config (dict): Configuration with weight settings
                          Format: {'weight_column': 'column_name', 'estimates': [...]}
        
        Returns:
            dict: Weighted and unweighted estimates with margins of error
        """
        weight_column = config.get('weight_column')
        
        if not weight_column or weight_column not in df.columns:
            logger.warning("Weight column not found, calculating unweighted estimates only")
            return self._calculate_unweighted_estimates(df, config)
        
        try:
            # Validate weights
            weights = df[weight_column].copy()
            weights = self._validate_weights(weights)
            
            # Calculate estimates
            estimates = {
                'weighted': {},
                'unweighted': {},
                'weight_statistics': self._get_weight_statistics(weights),
                'estimates_log': []
            }
            
            # Process each requested estimate
            estimate_configs = config.get('estimates', [])
            
            for est_config in estimate_configs:
                variable = est_config.get('variable')
                statistic = est_config.get('statistic', 'mean')
                confidence_level = est_config.get('confidence_level', 0.95)
                
                if variable not in df.columns:
                    logger.warning(f"Variable '{variable}' not found in dataset")
                    continue
                
                # Calculate weighted estimate
                weighted_result = self._calculate_weighted_estimate(
                    df[variable], weights, statistic, confidence_level
                )
                
                # Calculate unweighted estimate for comparison
                unweighted_result = self._calculate_unweighted_estimate(
                    df[variable], statistic, confidence_level
                )
                
                estimates['weighted'][f'{variable}_{statistic}'] = weighted_result
                estimates['unweighted'][f'{variable}_{statistic}'] = unweighted_result
                
                estimates['estimates_log'].append(
                    f"Variable '{variable}' ({statistic}): "
                    f"Weighted={weighted_result['estimate']:.4f} ± {weighted_result['margin_of_error']:.4f}, "
                    f"Unweighted={unweighted_result['estimate']:.4f} ± {unweighted_result['margin_of_error']:.4f}"
                )
            
            return estimates
            
        except Exception as e:
            logger.error(f"Error during weight application: {str(e)}")
            raise
    
    def _validate_weights(self, weights):
        """Validate and clean weight values."""
        # Remove missing weights
        valid_weights = weights.dropna()
        
        # Check for negative weights
        if (valid_weights < 0).any():
            logger.warning("Negative weights found, setting to zero")
            valid_weights = valid_weights.clip(lower=0)
        
        # Check for extremely large weights (potential outliers)
        weight_q99 = valid_weights.quantile(0.99)
        weight_median = valid_weights.median()
        
        if weight_q99 > 10 * weight_median:
            logger.warning("Some weights are extremely large, consider reviewing")
        
        # Replace missing weights with 1 (unweighted)
        weights_clean = weights.fillna(1.0)
        weights_clean = weights_clean.clip(lower=0)
        
        return weights_clean
    
    def _get_weight_statistics(self, weights):
        """Calculate descriptive statistics for weights."""
        return {
            'count': len(weights),
            'mean': weights.mean(),
            'median': weights.median(),
            'min': weights.min(),
            'max': weights.max(),
            'std': weights.std(),
            'sum': weights.sum(),
            'effective_sample_size': len(weights) ** 2 / (weights ** 2).sum()
        }
    
    def _calculate_weighted_estimate(self, variable, weights, statistic, confidence_level):
        """Calculate weighted estimate with margin of error."""
        # Remove missing values
        valid_mask = variable.notna() & weights.notna()
        valid_variable = variable[valid_mask]
        valid_weights = weights[valid_mask]
        
        if len(valid_variable) == 0:
            return {
                'estimate': np.nan,
                'standard_error': np.nan,
                'margin_of_error': np.nan,
                'confidence_interval': (np.nan, np.nan),
                'sample_size': 0,
                'effective_sample_size': 0
            }
        
        n = len(valid_variable)
        effective_n = n ** 2 / (valid_weights ** 2).sum()
        
        if statistic == 'mean':
            estimate = np.average(valid_variable, weights=valid_weights)
            
            # Calculate weighted variance
            weighted_mean = estimate
            weighted_variance = np.average((valid_variable - weighted_mean) ** 2, weights=valid_weights)
            
            # Standard error for weighted mean
            standard_error = np.sqrt(weighted_variance / effective_n)
            
        elif statistic == 'total':
            weight_sum = valid_weights.sum()
            estimate = np.sum(valid_variable * valid_weights)
            
            # Standard error for weighted total
            mean_estimate = np.average(valid_variable, weights=valid_weights)
            weighted_variance = np.average((valid_variable - mean_estimate) ** 2, weights=valid_weights)
            standard_error = weight_sum * np.sqrt(weighted_variance / effective_n)
            
        elif statistic == 'proportion':
            # For proportions, assume variable is binary (0/1)
            estimate = np.average(valid_variable, weights=valid_weights)
            
            # Standard error for weighted proportion
            standard_error = np.sqrt(estimate * (1 - estimate) / effective_n)
            
        else:
            logger.warning(f"Unsupported statistic: {statistic}")
            return {
                'estimate': np.nan,
                'standard_error': np.nan,
                'margin_of_error': np.nan,
                'confidence_interval': (np.nan, np.nan),
                'sample_size': n,
                'effective_sample_size': effective_n
            }
        
        # Calculate margin of error and confidence interval
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df=effective_n - 1)
        margin_of_error = t_critical * standard_error
        
        ci_lower = estimate - margin_of_error
        ci_upper = estimate + margin_of_error
        
        return {
            'estimate': estimate,
            'standard_error': standard_error,
            'margin_of_error': margin_of_error,
            'confidence_interval': (ci_lower, ci_upper),
            'confidence_level': confidence_level,
            'sample_size': n,
            'effective_sample_size': effective_n
        }
    
    def _calculate_unweighted_estimate(self, variable, statistic, confidence_level):
        """Calculate unweighted estimate with margin of error."""
        valid_variable = variable.dropna()
        n = len(valid_variable)
        
        if n == 0:
            return {
                'estimate': np.nan,
                'standard_error': np.nan,
                'margin_of_error': np.nan,
                'confidence_interval': (np.nan, np.nan),
                'sample_size': 0
            }
        
        if statistic == 'mean':
            estimate = valid_variable.mean()
            standard_error = valid_variable.std() / np.sqrt(n)
            
        elif statistic == 'total':
            estimate = valid_variable.sum()
            standard_error = valid_variable.std() * np.sqrt(n)
            
        elif statistic == 'proportion':
            estimate = valid_variable.mean()
            standard_error = np.sqrt(estimate * (1 - estimate) / n)
            
        else:
            return {
                'estimate': np.nan,
                'standard_error': np.nan,
                'margin_of_error': np.nan,
                'confidence_interval': (np.nan, np.nan),
                'sample_size': n
            }
        
        # Calculate margin of error and confidence interval
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df=n - 1)
        margin_of_error = t_critical * standard_error
        
        ci_lower = estimate - margin_of_error
        ci_upper = estimate + margin_of_error
        
        return {
            'estimate': estimate,
            'standard_error': standard_error,
            'margin_of_error': margin_of_error,
            'confidence_interval': (ci_lower, ci_upper),
            'confidence_level': confidence_level,
            'sample_size': n
        }
    
    def _calculate_unweighted_estimates(self, df, config):
        """Calculate only unweighted estimates when no weights are available."""
        estimates = {
            'unweighted': {},
            'estimates_log': ['No weight column found, calculating unweighted estimates only']
        }
        
        estimate_configs = config.get('estimates', [])
        
        for est_config in estimate_configs:
            variable = est_config.get('variable')
            statistic = est_config.get('statistic', 'mean')
            confidence_level = est_config.get('confidence_level', 0.95)
            
            if variable not in df.columns:
                continue
            
            result = self._calculate_unweighted_estimate(
                df[variable], statistic, confidence_level
            )
            
            estimates['unweighted'][f'{variable}_{statistic}'] = result
            estimates['estimates_log'].append(
                f"Variable '{variable}' ({statistic}): "
                f"Estimate={result['estimate']:.4f} ± {result['margin_of_error']:.4f}"
            )
        
        return estimates
    
    def calculate_design_effect(self, variable, weights):
        """Calculate design effect for a variable."""
        valid_mask = variable.notna() & weights.notna()
        valid_variable = variable[valid_mask]
        valid_weights = weights[valid_mask]
        
        if len(valid_variable) == 0:
            return np.nan
        
        # Weighted variance
        weighted_mean = np.average(valid_variable, weights=valid_weights)
        weighted_var = np.average((valid_variable - weighted_mean) ** 2, weights=valid_weights)
        
        # Unweighted variance
        unweighted_var = valid_variable.var()
        
        # Design effect
        n = len(valid_variable)
        effective_n = n ** 2 / (valid_weights ** 2).sum()
        
        design_effect = (weighted_var / unweighted_var) * (n / effective_n)
        
        return design_effect
    
    def create_estimates_summary(self, estimates):
        """Create a summary table of all estimates."""
        summary = {
            'estimates_comparison': [],
            'weight_effectiveness': {},
            'recommendations': []
        }
        
        # Compare weighted vs unweighted estimates
        if 'weighted' in estimates and 'unweighted' in estimates:
            for key in estimates['weighted'].keys():
                if key in estimates['unweighted']:
                    weighted = estimates['weighted'][key]
                    unweighted = estimates['unweighted'][key]
                    
                    # Calculate relative difference
                    if unweighted['estimate'] != 0:
                        rel_diff = abs(weighted['estimate'] - unweighted['estimate']) / abs(unweighted['estimate']) * 100
                    else:
                        rel_diff = 0
                    
                    summary['estimates_comparison'].append({
                        'variable': key,
                        'weighted_estimate': weighted['estimate'],
                        'unweighted_estimate': unweighted['estimate'],
                        'relative_difference_pct': rel_diff,
                        'weighted_margin_of_error': weighted['margin_of_error'],
                        'unweighted_margin_of_error': unweighted['margin_of_error']
                    })
        
        # Weight effectiveness analysis
        if 'weight_statistics' in estimates:
            weight_stats = estimates['weight_statistics']
            cv_weights = weight_stats['std'] / weight_stats['mean'] if weight_stats['mean'] > 0 else 0
            
            summary['weight_effectiveness'] = {
                'coefficient_of_variation': cv_weights,
                'effective_sample_size_ratio': weight_stats['effective_sample_size'] / weight_stats['count'],
                'assessment': self._assess_weight_effectiveness(cv_weights, weight_stats['effective_sample_size'] / weight_stats['count'])
            }
        
        return summary
    
    def _assess_weight_effectiveness(self, cv_weights, ess_ratio):
        """Assess the effectiveness of the weighting scheme."""
        if cv_weights < 0.3 and ess_ratio > 0.8:
            return "Highly effective weighting - low variability and high effective sample size"
        elif cv_weights < 0.5 and ess_ratio > 0.6:
            return "Moderately effective weighting - acceptable variability and effective sample size"
        elif cv_weights < 0.7:
            return "Moderately effective weighting - some precision loss due to weight variability"
        else:
            return "Low effectiveness - high weight variability leading to substantial precision loss"