import pandas as pd
import numpy as np
import re
import logging

logger = logging.getLogger(__name__)


class RuleValidationEngine:
    """
    Engine for rule-based validation of survey data.
    Supports consistency checks, skip patterns, and custom validation rules.
    """
    
    def __init__(self):
        self.validation_rules = {}
        self.validation_results = {}
    
    def validate_data(self, df, config):
        """
        Apply validation rules based on configuration.
        
        Args:
            df (pd.DataFrame): Input dataframe
            config (dict): Configuration with validation rules
                          Format: {'rules': [{'type': 'rule_type', 'params': {...}}]}
        
        Returns:
            pd.DataFrame: Dataframe with validation flags
            dict: Validation statistics and logs
        """
        df_validated = df.copy()
        stats = {
            'total_violations': 0,
            'rules_applied': [],
            'validation_log': []
        }
        
        try:
            rules = config.get('rules', [])
            
            for rule_idx, rule in enumerate(rules):
                rule_type = rule.get('type')
                rule_name = rule.get('name', f'rule_{rule_idx}')
                
                logger.info(f"Applying validation rule: {rule_name} ({rule_type})")
                
                violations = self._apply_validation_rule(df_validated, rule)
                violation_count = violations.sum() if isinstance(violations, pd.Series) else 0
                
                if violation_count > 0:
                    flag_column = f'{rule_name}_violation'
                    df_validated[flag_column] = violations
                
                stats['rules_applied'].append({
                    'rule_name': rule_name,
                    'rule_type': rule_type,
                    'violations': violation_count,
                    'violation_rate': violation_count / len(df) * 100
                })
                
                stats['validation_log'].append(
                    f"Rule '{rule_name}': {violation_count} violations found"
                )
                
                stats['total_violations'] += violation_count
            
            return df_validated, stats
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            raise
    
    def _apply_validation_rule(self, df, rule):
        """Apply a single validation rule to the dataframe."""
        rule_type = rule.get('type')
        params = rule.get('params', {})
        
        if rule_type == 'range_check':
            return self._range_check(df, params)
        elif rule_type == 'consistency_check':
            return self._consistency_check(df, params)
        elif rule_type == 'skip_pattern':
            return self._skip_pattern_check(df, params)
        elif rule_type == 'format_check':
            return self._format_check(df, params)
        elif rule_type == 'logical_check':
            return self._logical_check(df, params)
        elif rule_type == 'completeness_check':
            return self._completeness_check(df, params)
        else:
            logger.warning(f"Unknown validation rule type: {rule_type}")
            return pd.Series([False] * len(df), index=df.index)
    
    def _range_check(self, df, params):
        """Check if values are within specified ranges."""
        column = params.get('column')
        min_val = params.get('min_value')
        max_val = params.get('max_value')
        
        if column not in df.columns:
            return pd.Series([False] * len(df), index=df.index)
        
        violations = pd.Series([False] * len(df), index=df.index)
        
        if min_val is not None:
            violations |= df[column] < min_val
        
        if max_val is not None:
            violations |= df[column] > max_val
        
        return violations
    
    def _consistency_check(self, df, params):
        """Check consistency between related columns."""
        primary_column = params.get('primary_column')
        related_column = params.get('related_column')
        relationship = params.get('relationship')  # 'greater_than', 'less_than', 'equal', etc.
        
        if primary_column not in df.columns or related_column not in df.columns:
            return pd.Series([False] * len(df), index=df.index)
        
        violations = pd.Series([False] * len(df), index=df.index)
        
        # Skip rows where either column has missing values
        valid_mask = df[primary_column].notna() & df[related_column].notna()
        
        if relationship == 'greater_than':
            violations[valid_mask] = df.loc[valid_mask, primary_column] <= df.loc[valid_mask, related_column]
        elif relationship == 'less_than':
            violations[valid_mask] = df.loc[valid_mask, primary_column] >= df.loc[valid_mask, related_column]
        elif relationship == 'equal':
            violations[valid_mask] = df.loc[valid_mask, primary_column] != df.loc[valid_mask, related_column]
        elif relationship == 'not_equal':
            violations[valid_mask] = df.loc[valid_mask, primary_column] == df.loc[valid_mask, related_column]
        
        return violations
    
    def _skip_pattern_check(self, df, params):
        """Check skip patterns - if condition A, then column B should have specific values."""
        condition_column = params.get('condition_column')
        condition_value = params.get('condition_value')
        target_column = params.get('target_column')
        expected_value = params.get('expected_value', None)  # None means should be empty
        
        if condition_column not in df.columns or target_column not in df.columns:
            return pd.Series([False] * len(df), index=df.index)
        
        # Find rows that meet the condition
        condition_mask = df[condition_column] == condition_value
        violations = pd.Series([False] * len(df), index=df.index)
        
        if expected_value is None:
            # Target column should be empty/null when condition is met
            violations[condition_mask] = df.loc[condition_mask, target_column].notna()
        else:
            # Target column should have specific value when condition is met
            violations[condition_mask] = df.loc[condition_mask, target_column] != expected_value
        
        return violations
    
    def _format_check(self, df, params):
        """Check if values match expected format (regex pattern)."""
        column = params.get('column')
        pattern = params.get('pattern')
        
        if column not in df.columns or not pattern:
            return pd.Series([False] * len(df), index=df.index)
        
        violations = pd.Series([False] * len(df), index=df.index)
        
        # Only check non-null values
        valid_mask = df[column].notna()
        
        try:
            # Check if values match the pattern
            matches = df.loc[valid_mask, column].astype(str).str.match(pattern)
            violations[valid_mask] = ~matches
        except Exception as e:
            logger.error(f"Error in format check for column {column}: {str(e)}")
            return violations
        
        return violations
    
    def _logical_check(self, df, params):
        """Apply custom logical checks using expressions."""
        expression = params.get('expression')
        
        if not expression:
            return pd.Series([False] * len(df), index=df.index)
        
        try:
            # Evaluate the expression - violations are where the expression is False
            # Expression should be written in terms of column names
            # Example: "(age >= 18) | (guardian_consent == 'Yes')"
            result = df.eval(expression)
            return ~result  # Violations are where the logical check fails
        except Exception as e:
            logger.error(f"Error in logical check: {str(e)}")
            return pd.Series([False] * len(df), index=df.index)
    
    def _completeness_check(self, df, params):
        """Check if required fields are complete based on conditions."""
        required_columns = params.get('required_columns', [])
        condition = params.get('condition')  # Optional condition for when fields are required
        
        violations = pd.Series([False] * len(df), index=df.index)
        
        if condition:
            try:
                condition_mask = df.eval(condition)
            except Exception as e:
                logger.error(f"Error evaluating condition: {str(e)}")
                condition_mask = pd.Series([True] * len(df), index=df.index)
        else:
            condition_mask = pd.Series([True] * len(df), index=df.index)
        
        # Check if required columns have missing values when condition is met
        for column in required_columns:
            if column in df.columns:
                missing_required = condition_mask & df[column].isna()
                violations |= missing_required
        
        return violations
    
    def create_validation_report(self, df_original, df_validated, stats):
        """Generate a comprehensive validation report."""
        report = {
            'summary': {
                'total_records': len(df_original),
                'total_violations': stats['total_violations'],
                'violation_rate': stats['total_violations'] / len(df_original) * 100,
                'rules_applied': len(stats['rules_applied'])
            },
            'rule_details': stats['rules_applied'],
            'validation_log': stats['validation_log']
        }
        
        # Add column-wise violation counts
        violation_columns = [col for col in df_validated.columns if col.endswith('_violation')]
        
        if violation_columns:
            report['violation_by_column'] = {}
            for col in violation_columns:
                rule_name = col.replace('_violation', '')
                violation_count = df_validated[col].sum()
                report['violation_by_column'][rule_name] = {
                    'violations': violation_count,
                    'violation_rate': violation_count / len(df_validated) * 100
                }
        
        return report
    
    def suggest_validation_rules(self, df, survey_type='general'):
        """Suggest common validation rules based on data characteristics and survey type."""
        suggestions = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Age-related validations for household surveys
        age_columns = [col for col in df.columns if 'age' in col.lower()]
        for col in age_columns:
            suggestions.append({
                'type': 'range_check',
                'name': f'{col}_range_check',
                'params': {
                    'column': col,
                    'min_value': 0,
                    'max_value': 120
                },
                'description': f'Age values should be between 0 and 120 for column {col}'
            })
        
        # Income/expenditure consistency checks
        income_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['income', 'salary', 'wage'])]
        expense_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['expense', 'expenditure', 'cost'])]
        
        if income_cols and expense_cols:
            suggestions.append({
                'type': 'logical_check',
                'name': 'income_expense_logic',
                'params': {
                    'expression': f'({income_cols[0]} >= {expense_cols[0]}) | ({income_cols[0]}.isna()) | ({expense_cols[0]}.isna())'
                },
                'description': 'Income should generally be greater than or equal to expenses'
            })
        
        # Date format validations
        date_columns = df.select_dtypes(include=['object']).columns
        for col in date_columns:
            sample_values = df[col].dropna().head(10).astype(str)
            if any(re.match(r'\d{4}-\d{2}-\d{2}', str(val)) for val in sample_values):
                suggestions.append({
                    'type': 'format_check',
                    'name': f'{col}_date_format',
                    'params': {
                        'column': col,
                        'pattern': r'^\d{4}-\d{2}-\d{2}$'
                    },
                    'description': f'Date format validation for column {col}'
                })
        
        return suggestions