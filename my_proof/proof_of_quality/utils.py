# The MIT License (MIT)
# Copyright © 2024 PrimeInsightsDAO, philanthrope

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from .config import get_validation_config

def parse_float(value):
    if isinstance(value, str):
        value = value.strip("'\"")
    try:
        return float(value)
    except ValueError:
        return 0.0

def parse_date(date_string):
    date_formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S']
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date '{date_string}' is not in a recognized format.")

def calculate_time_weight(date_range: dict) -> tuple:
    """
    Calculate time weight using natural logarithm that tapers off at max_age.
    Weight = 1 - ln(1 + age/365) / ln(1 + max_age/365)
    """
    if date_range['latest']:
        latest_date = datetime.fromisoformat(date_range['latest'])
    else:
        return 0.0, 0

    current_date = datetime.now()
    age_in_days = (current_date - latest_date).days

    if age_in_days < 0:
        return 0.0, age_in_days

    # Use 4 years as max age
    max_age_days = 365 * 4
    
    # Natural log scaling relative to years
    # This creates a smooth curve that reaches 0 at max_age
    weight = 1 - (np.log1p(age_in_days/365) / np.log1p(max_age_days/365))
    
    # Ensure weight is between 0 and 1
    weight = max(0.0, min(1.0, weight))

    return weight, age_in_days

def plot_decay_comparison(half_life_days=365):
    """
    Visualize the time decay function behavior
    """
    age_days = np.linspace(0, 365 * 4, 1000)  # Show 4 years
    
    # Calculate weights
    weights = [calculate_time_weight({'latest': (datetime.now() - timedelta(days=d)).isoformat()})[0] for d in age_days]
    
    plt.figure(figsize=(12, 6))
    plt.plot(age_days, weights, 'b-', linewidth=2, label='Time Weight')
    
    # Add markers
    plt.axvline(x=365, color='r', linestyle='--', label='1 Year (50% Decay)')
    plt.axhline(y=1.0, color='g', linestyle='--', label='Full Weight')
    plt.axhline(y=0.5, color='y', linestyle='--', label='Half Weight')
    
    plt.grid(True, alpha=0.3)
    plt.xlabel('Age (days)')
    plt.ylabel('Weight')
    plt.title('Time Weight: Flat First Year + Logarithmic Decay')
    plt.legend()
    
    plt.ylim(-0.05, 1.05)
    plt.savefig('time_decay_comparison.png')

def calculate_log_score(value: float, min_value: float, validation_config: Dict[str, any]) -> float:
    """
    Calculate a pure logarithmic score.
    score = ln(min(1, value/min_value))
    """
    if value <= 0 or min_value <= 0:
        return 0.0
    
    score_scaling = validation_config.get("SCORE_SCALING", 1.5)
    
    # Calculate ratio
    ratio = value / min_value
    
    # Pure logarithmic scoring
    log_score = np.log1p(ratio) / np.log1p(10)  # normalize to log(11) for 0-1 range
    
    # Apply scaling
    log_score *= score_scaling
    
    # Ensure score is between 0 and 1
    return max(0.0, min(1.0, log_score))

def visualize_log_score_behavior(validation_config: Dict[str, any]):
    """
    Visualize how calculate_log_score behaves with different inputs.
    Shows the effect of ratio and scaling on final scores.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    # Test ranges
    min_value = 1.0
    values = np.linspace(0, 10 * min_value, 1000)  # Test up to 10x minimum
    
    # Calculate scores
    scores = [calculate_log_score(v, min_value, validation_config) for v in values]
    ratios = values / min_value

    # Create figure with multiple subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot 1: Score vs Value
    ax1.plot(values, scores, 'b-', label='Score')
    ax1.axvline(x=min_value, color='r', linestyle='--', label='Min Value')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('Value')
    ax1.set_ylabel('Score')
    ax1.set_title('Score vs Actual Value')
    ax1.legend()

    # Plot 2: Score vs Ratio
    ax2.plot(ratios, scores, 'g-', label='Score')
    ax2.axvline(x=1, color='r', linestyle='--', label='Min Ratio')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('Ratio (value/min_value)')
    ax2.set_ylabel('Score')
    ax2.set_title('Score vs Ratio')
    ax2.legend()

    plt.tight_layout()
    plt.savefig('log_score_behavior.png')

    # Print some example values
    print("\nExample Scores:")
    test_ratios = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    for ratio in test_ratios:
        score = calculate_log_score(ratio * min_value, min_value, validation_config)
        print(f"Ratio: {ratio:4.1f}x minimum -> Score: {score:.3f}")

def analyze_scoring_behavior(validation_config: Dict[str, any]):
    """
    Comprehensive analysis of the scoring system behavior.
    Shows multiple visualizations and analyses of how scores change with different inputs.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.gridspec import GridSpec
    from datetime import datetime, timedelta

    # Create figure with multiple subplots
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 15))
    gs = GridSpec(3, 2, figure=fig)
    
    # 1. Basic Score vs Ratio relationship
    ax1 = fig.add_subplot(gs[0, 0])
    ratios = np.linspace(0, 10, 1000)
    scores = [calculate_log_score(r, 1.0, validation_config) for r in ratios]
    ax1.plot(ratios, scores, 'b-', label='Score')
    ax1.axvline(x=1, color='r', linestyle='--', label='Minimum')
    ax1.axhline(y=0.5, color='g', linestyle='--', label='Mid Score')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('Ratio (value/minimum)')
    ax1.set_ylabel('Score')
    ax1.set_title('Basic Score vs Ratio')
    ax1.legend()

    # 2. Score Growth Analysis
    ax2 = fig.add_subplot(gs[0, 1])
    multiples = [1, 2, 5, 10, 20, 50, 100]
    min_values = [1, 10, 100, 1000]
    for min_val in min_values:
        scores = [calculate_log_score(m * min_val, min_val, validation_config) for m in multiples]
        ax2.plot(multiples, scores, 'o-', label=f'Min={min_val}')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_xlabel('Multiple of Minimum')
    ax2.set_ylabel('Score')
    ax2.set_title('Score Growth with Different Minimums')
    ax2.legend()

    # 3. Time Weight Effect
    ax3 = fig.add_subplot(gs[1, 0])
    days = np.linspace(0, 365*2, 1000)
    weights = [calculate_time_weight({'latest': (datetime.now() - timedelta(days=d)).isoformat()})[0] for d in days]
    ax3.plot(days, weights, 'g-', label='Time Weight')
    ax3.axvline(x=365, color='r', linestyle='--', label='1 Year')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlabel('Age (days)')
    ax3.set_ylabel('Weight')
    ax3.set_title('Time Weight Decay')
    ax3.legend()

    # 4. Combined Effects
    ax4 = fig.add_subplot(gs[1, 1])
    ratios = np.linspace(0, 10, 100)
    ages = [0, 30, 90, 180, 365]
    for age in ages:
        time_weight = calculate_time_weight({'latest': (datetime.now() - timedelta(days=age)).isoformat()})[0]
        scores = [calculate_log_score(r, 1.0, validation_config) * time_weight for r in ratios]
        ax4.plot(ratios, scores, label=f'{age} days old')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlabel('Ratio (value/minimum)')
    ax4.set_ylabel('Final Score')
    ax4.set_title('Combined Score with Time Decay')
    ax4.legend()

    # 5. Score Distribution Analysis
    ax5 = fig.add_subplot(gs[2, :])
    test_cases = [
        (0.5, 'Below Minimum'),
        (1.0, 'At Minimum'),
        (1.5, 'Above Minimum'),
        (2.0, '2x Minimum'),
        (5.0, '5x Minimum'),
        (10.0, '10x Minimum')
    ]
    ages = [0, 30, 90, 180, 365]
    data = []
    labels = []
    for ratio, label in test_cases:
        for age in ages:
            time_weight = calculate_time_weight({'latest': (datetime.now() - timedelta(days=age)).isoformat()})[0]
            score = calculate_log_score(ratio, 1.0, validation_config) * time_weight
            data.append(score)
            labels.append(f'{label}\n{age} days')
    
    ax5.bar(range(len(data)), data)
    ax5.set_xticks(range(len(data)))
    ax5.set_xticklabels(labels, rotation=45, ha='right')
    ax5.grid(True, alpha=0.3)
    ax5.set_ylabel('Final Score')
    ax5.set_title('Score Distribution Analysis')

    # Print numerical analysis
    print("\nNumerical Analysis:")
    print("\n1. Basic Ratio Effects:")
    for ratio in [0.5, 1.0, 1.5, 2.0, 5.0, 10.0]:
        score = calculate_log_score(ratio, 1.0, validation_config)
        print(f"Ratio {ratio:4.1f}x minimum -> Score: {score:.3f}")

    print("\n2. Time Weight Effects:")
    for days in [0, 30, 90, 180, 365]:
        weight = calculate_time_weight({'latest': (datetime.now() - timedelta(days=days)).isoformat()})[0]
        print(f"Age {days:3d} days -> Weight: {weight:.3f}")

    print("\n3. Combined Effects:")
    for ratio in [1.0, 2.0, 5.0]:
        for days in [0, 90, 365]:
            time_weight = calculate_time_weight({'latest': (datetime.now() - timedelta(days=days)).isoformat()})[0]
            score = calculate_log_score(ratio, 1.0, validation_config) * time_weight
            print(f"Ratio {ratio:4.1f}x, Age {days:3d} days -> Final Score: {score:.3f}")

    plt.tight_layout()
    plt.savefig('scoring_analysis.png')

# Add to existing visualization functions
def plot_all_analyses(validation_config: Dict[str, any]):
    """Run all visualization and analysis functions."""
    print("=== Log Score Behavior ===")
    visualize_log_score_behavior(validation_config)
    
    print("\n=== Comprehensive Scoring Analysis ===")
    analyze_scoring_behavior(validation_config)
    
    print("\n=== Time Decay Comparison ===")
    plot_decay_comparison(validation_config)
