import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
import io
import base64
import logging

logger = logging.getLogger(__name__)

class VisualizationEngine:
    """
    Engine for creating visualizations for survey data reports.
    Supports both matplotlib/seaborn and plotly visualizations.
    """
    
    def __init__(self):
        # Set style for matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configure plotly default template
        self.plotly_template = "plotly_white"
    
    def create_data_overview_chart(self, df, chart_type='summary'):
        """Create overview visualizations of the dataset."""
        if chart_type == 'summary':
            return self._create_summary_statistics_chart(df)
        elif chart_type == 'missing_data':
            return self._create_missing_data_chart(df)
        elif chart_type == 'data_types':
            return self._create_data_types_chart(df)
        else:
            logger.warning(f"Unknown chart type: {chart_type}")
            return None
    
    def _create_summary_statistics_chart(self, df):
        """Create summary statistics visualization."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return None
        
        # Create subplots for different statistics
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Dataset Summary Statistics', fontsize=16)
        
        # 1. Distribution of values count per column
        value_counts = [df[col].count() for col in numeric_columns[:10]]  # Limit to first 10
        axes[0, 0].bar(range(len(value_counts)), value_counts)
        axes[0, 0].set_title('Non-null Values by Column')
        axes[0, 0].set_xlabel('Column Index')
        axes[0, 0].set_ylabel('Count')
        
        # 2. Missing data percentage
        missing_pct = [(df[col].isnull().sum() / len(df)) * 100 for col in numeric_columns[:10]]
        axes[0, 1].bar(range(len(missing_pct)), missing_pct)
        axes[0, 1].set_title('Missing Data Percentage')
        axes[0, 1].set_xlabel('Column Index')
        axes[0, 1].set_ylabel('Percentage')
        
        # 3. Basic statistics heatmap
        if len(numeric_columns) > 1:
            stats_data = df[numeric_columns[:10]].describe().T
            im = axes[1, 0].imshow(stats_data.values, cmap='viridis', aspect='auto')
            axes[1, 0].set_title('Statistics Heatmap')
            axes[1, 0].set_xticks(range(len(stats_data.columns)))
            axes[1, 0].set_xticklabels(stats_data.columns, rotation=45)
            axes[1, 0].set_yticks(range(len(stats_data.index)))
            axes[1, 0].set_yticklabels(stats_data.index)
            plt.colorbar(im, ax=axes[1, 0])
        
        # 4. Overall dataset info
        info_text = f"""
        Total Rows: {len(df):,}
        Total Columns: {len(df.columns)}
        Numeric Columns: {len(numeric_columns)}
        Total Missing Values: {df.isnull().sum().sum():,}
        Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB
        """
        axes[1, 1].text(0.1, 0.7, info_text, fontsize=12, verticalalignment='top')
        axes[1, 1].set_xlim(0, 1)
        axes[1, 1].set_ylim(0, 1)
        axes[1, 1].set_title('Dataset Information')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def _create_missing_data_chart(self, df):
        """Create missing data visualization."""
        missing_data = df.isnull().sum().sort_values(ascending=False)
        missing_data = missing_data[missing_data > 0]
        
        if len(missing_data) == 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Missing Data Found!', 
                   ha='center', va='center', fontsize=20, color='green')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.set_title('Missing Data Analysis', fontsize=16)
        else:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Bar chart of missing values
            missing_data[:20].plot(kind='bar', ax=ax1)
            ax1.set_title('Missing Values by Column (Top 20)')
            ax1.set_xlabel('Columns')
            ax1.set_ylabel('Number of Missing Values')
            ax1.tick_params(axis='x', rotation=45)
            
            # Percentage of missing data
            missing_pct = (missing_data / len(df) * 100)[:20]
            missing_pct.plot(kind='bar', ax=ax2, color='orange')
            ax2.set_title('Missing Data Percentage (Top 20)')
            ax2.set_xlabel('Columns')
            ax2.set_ylabel('Percentage Missing')
            ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def _create_data_types_chart(self, df):
        """Create data types distribution chart."""
        data_types = df.dtypes.value_counts()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Pie chart of data types
        ax1.pie(data_types.values, labels=data_types.index, autopct='%1.1f%%')
        ax1.set_title('Distribution of Data Types')
        
        # Bar chart with counts
        data_types.plot(kind='bar', ax=ax2)
        ax2.set_title('Column Count by Data Type')
        ax2.set_xlabel('Data Type')
        ax2.set_ylabel('Number of Columns')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def create_statistical_charts(self, results, chart_type='estimates_comparison'):
        """Create charts for statistical results."""
        if chart_type == 'estimates_comparison':
            return self._create_estimates_comparison_chart(results)
        elif chart_type == 'confidence_intervals':
            return self._create_confidence_intervals_chart(results)
        elif chart_type == 'weight_distribution':
            return self._create_weight_distribution_chart(results)
        else:
            logger.warning(f"Unknown statistical chart type: {chart_type}")
            return None
    
    def _create_estimates_comparison_chart(self, results):
        """Create comparison chart of weighted vs unweighted estimates."""
        if 'estimates_comparison' not in results:
            return None
        
        comparison_data = results['estimates_comparison']
        
        if not comparison_data:
            return None
        
        variables = [item['variable'] for item in comparison_data]
        weighted_est = [item['weighted_estimate'] for item in comparison_data]
        unweighted_est = [item['unweighted_estimate'] for item in comparison_data]
        
        x = np.arange(len(variables))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars1 = ax.bar(x - width/2, weighted_est, width, label='Weighted', alpha=0.8)
        bars2 = ax.bar(x + width/2, unweighted_est, width, label='Unweighted', alpha=0.8)
        
        ax.set_xlabel('Variables')
        ax.set_ylabel('Estimates')
        ax.set_title('Weighted vs Unweighted Estimates Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(variables, rotation=45, ha='right')
        ax.legend()
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def _create_confidence_intervals_chart(self, results):
        """Create confidence intervals visualization."""
        if 'weighted' not in results:
            return None
        
        weighted_results = results['weighted']
        
        variables = []
        estimates = []
        lower_bounds = []
        upper_bounds = []
        
        for var_name, var_data in weighted_results.items():
            if isinstance(var_data, dict) and 'confidence_interval' in var_data:
                variables.append(var_name)
                estimates.append(var_data['estimate'])
                lower_bounds.append(var_data['confidence_interval'][0])
                upper_bounds.append(var_data['confidence_interval'][1])
        
        if not variables:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        y_pos = np.arange(len(variables))
        
        # Plot estimates as points
        ax.scatter(estimates, y_pos, color='blue', s=100, zorder=3, label='Estimates')
        
        # Plot confidence intervals as horizontal lines
        for i, (est, lower, upper) in enumerate(zip(estimates, lower_bounds, upper_bounds)):
            ax.plot([lower, upper], [i, i], color='blue', alpha=0.6, linewidth=3)
            ax.plot([lower, lower], [i-0.1, i+0.1], color='blue', alpha=0.6, linewidth=2)
            ax.plot([upper, upper], [i-0.1, i+0.1], color='blue', alpha=0.6, linewidth=2)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(variables)
        ax.set_xlabel('Value')
        ax.set_title('Estimates with Confidence Intervals')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def create_processing_summary_chart(self, processing_stats):
        """Create visualization of data processing summary."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Data Processing Summary', fontsize=16)
        
        # 1. Missing value imputation summary
        if 'imputation' in processing_stats:
            imp_stats = processing_stats['imputation']
            methods = [col['method'] for col in imp_stats.get('columns_processed', [])]
            method_counts = pd.Series(methods).value_counts()
            
            if len(method_counts) > 0:
                method_counts.plot(kind='pie', ax=axes[0, 0], autopct='%1.1f%%')
                axes[0, 0].set_title('Imputation Methods Used')
                axes[0, 0].set_ylabel('')
        
        # 2. Outlier detection summary
        if 'outliers' in processing_stats:
            out_stats = processing_stats['outliers']
            total_outliers = sum([col['outlier_count'] for col in out_stats.get('columns_processed', [])])
            total_records = processing_stats.get('total_records', 1)
            
            outlier_data = ['Outliers', 'Normal Values']
            outlier_counts = [total_outliers, total_records - total_outliers]
            
            axes[0, 1].pie(outlier_counts, labels=outlier_data, autopct='%1.1f%%')
            axes[0, 1].set_title('Outlier Detection Results')
        
        # 3. Validation violations
        if 'validation' in processing_stats:
            val_stats = processing_stats['validation']
            if val_stats.get('rules_applied'):
                rule_names = [rule['rule_name'] for rule in val_stats['rules_applied']]
                violations = [rule['violations'] for rule in val_stats['rules_applied']]
                
                if rule_names:
                    axes[1, 0].bar(range(len(rule_names)), violations)
                    axes[1, 0].set_title('Validation Rule Violations')
                    axes[1, 0].set_xlabel('Rules')
                    axes[1, 0].set_ylabel('Violations')
                    axes[1, 0].set_xticks(range(len(rule_names)))
                    axes[1, 0].set_xticklabels(rule_names, rotation=45, ha='right')
        
        # 4. Processing timeline/steps
        steps = ['Upload', 'Validation', 'Cleaning', 'Imputation', 'Outliers', 'Weights', 'Results']
        completed = [1, 1, 1, 1, 1, 1, 1]  # Assuming all completed for visualization
        
        axes[1, 1].barh(steps, completed, color='green', alpha=0.7)
        axes[1, 1].set_title('Processing Steps Completed')
        axes[1, 1].set_xlabel('Status (1 = Completed)')
        
        plt.tight_layout()
        return self._matplotlib_to_base64(fig)
    
    def create_interactive_dashboard(self, df, results):
        """Create an interactive Plotly dashboard."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return None
        
        # Create a correlation heatmap
        if len(numeric_columns) > 1:
            corr_matrix = df[numeric_columns].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0
            ))
            
            fig.update_layout(
                title='Correlation Matrix of Numeric Variables',
                xaxis_title='Variables',
                yaxis_title='Variables',
                template=self.plotly_template
            )
            
            return plot(fig, output_type='div', include_plotlyjs=True)
        
        return None
    
    def _matplotlib_to_base64(self, fig):
        """Convert matplotlib figure to base64 string."""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    
    def save_chart_as_file(self, chart_data, filepath, format='png'):
        """Save chart to file (for PDF generation)."""
        if chart_data.startswith('data:image/png;base64,'):
            image_data = base64.b64decode(chart_data.split(',')[1])
            with open(filepath, 'wb') as f:
                f.write(image_data)
            return filepath
        
        return None