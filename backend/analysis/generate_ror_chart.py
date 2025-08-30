import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_ror_chart_with_confidence_intervals(query):
    """
    Generate ROR chart with confidence intervals
    Returns the file path of the generated chart
    """
    try:
        # Create charts directory if it doesn't exist
        charts_dir = os.path.join(settings.MEDIA_ROOT, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # Generate quarters for X-axis
        quarters = []
        year_start, quarter_start = query.year_start, query.quarter_start
        year_end, quarter_end = query.year_end, query.quarter_end
        
        current_year, current_quarter = year_start, quarter_start
        while (current_year < year_end) or (current_year == year_end and current_quarter <= quarter_end):
            quarters.append(f"{current_year} Q{current_quarter}")
            current_quarter += 1
            if current_quarter > 4:
                current_quarter = 1
                current_year += 1
        
        # Generate simulated ROR data
        num_quarters = len(quarters)
        
        # Generate ROR values (between 0.1 to 10, representing odds ratios)
        ror_values = []
        for _ in range(num_quarters):
            # Generate realistic ROR values (most should be around 1, some elevated)
            if random.random() < 0.7:  # 70% normal values
                ror = np.random.uniform(0.5, 2.0)
            else:  # 30% more significant values
                ror = np.random.uniform(2.0, 8.0)
            ror_values.append(ror)
        
        # Generate confidence intervals (lower and upper bounds)
        ror_lower = []
        ror_upper = []
        
        for ror in ror_values:
            # Generate realistic confidence intervals
            ci_width = np.random.uniform(0.3, 1.2)  # Variable CI width
            lower = max(0.1, ror - ci_width)
            upper = min(15.0, ror + ci_width)
            
            ror_lower.append(lower)
            ror_upper.append(upper)
        
        # Create DataFrame for easier handling
        df = pd.DataFrame({
            'quarters': quarters,
            'ror_values': ror_values,
            'ror_lower': ror_lower,
            'ror_upper': ror_upper
        })
        
        # Calculate LOG10 values for plotting (but keep original for display)
        log_ror_values = np.log10(ror_values)
        log_ror_lower = np.log10(ror_lower)
        log_ror_upper = np.log10(ror_upper)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot confidence intervals as fill_between (on log scale)
        x_positions = range(len(quarters))
        ax.fill_between(x_positions, log_ror_lower, log_ror_upper, 
                       alpha=0.3, color='lightblue', label='95% Confidence Interval')
        
        # Plot ROR line (on log scale)
        ax.plot(x_positions, log_ror_values, 'o-', color='darkblue', 
               linewidth=2, markersize=6, label='ROR Values')
        
        # Add horizontal line at log10(1) = 0 (no association)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='No Association (ROR=1)')
        
        # Set custom Y-axis labels showing original ROR values
        log_ticks = np.log10([0.1, 0.25, 0.5, 1, 2, 4, 8, 16])
        original_labels = ['0.1', '0.25', '0.5', '1', '2', '4', '8', '16']
        ax.set_yticks(log_ticks)
        ax.set_yticklabels(original_labels)
        
        # Customize the plot
        ax.set_xlabel('Quarter', fontsize=12, fontweight='bold')
        ax.set_ylabel('Reporting Odds Ratio (ROR)', fontsize=12, fontweight='bold')
        ax.set_title(f'ROR Analysis with Confidence Intervals: {query.name}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Set X-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(quarters, rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Add legend
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Add text annotations for significant values
        for i, (q, ror_val, log_val) in enumerate(zip(quarters, ror_values, log_ror_values)):
            if ror_val > 2.0:  # Highlight significant associations
                ax.annotate(f'ROR: {ror_val:.2f}', 
                           xy=(i, log_val), 
                           xytext=(10, 10), 
                           textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7),
                           fontsize=9,
                           ha='left')
        
        # Tight layout
        plt.tight_layout()
        
        # Save the chart
        chart_filename = f"ror_chart_{query.id}_{query.name.replace(' ', '_').replace('/', '_')}.png"
        chart_path = os.path.join(charts_dir, chart_filename)
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"ROR chart generated successfully: {chart_path}")
        
        # Also save the data as JSON for potential future use
        data_filename = f"ror_data_{query.id}.json"
        data_path = os.path.join(charts_dir, data_filename)
        df.to_json(data_path, orient='records', date_format='iso')
        
        return chart_path, data_path
        
    except Exception as e:
        logger.error(f"Error generating ROR chart: {str(e)}")
        raise e

def generate_mock_ror_data(num_points=20):
    """
    Generate mock ROR data for testing purposes
    Returns three arrays: ror_values, ror_lower, ror_upper
    """
    ror_values = []
    ror_lower = []
    ror_upper = []
    
    for i in range(num_points):
        # Generate base ROR value
        if random.random() < 0.6:  # 60% normal associations
            base_ror = np.random.uniform(0.3, 3.0)
        else:  # 40% stronger associations
            base_ror = np.random.uniform(3.0, 12.0)
        
        # Generate confidence interval
        ci_range = np.random.uniform(0.5, 2.0)
        lower = max(0.05, base_ror - ci_range)
        upper = min(20.0, base_ror + ci_range)
        
        ror_values.append(round(base_ror, 3))
        ror_lower.append(round(lower, 3))
        ror_upper.append(round(upper, 3))
    
    return ror_values, ror_lower, ror_upper