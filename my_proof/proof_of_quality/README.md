# Amazon Data Proof of Quality (PoQ) System
=========================================

## Overview:
---------
This codebase implements a Proof of Quality (PoQ) system for Amazon user data. It's designed to analyze and validate various types of Amazon user data, including retail order history, digital purchases, Audible usage, and Prime Video viewing history. The system assesses the quality, consistency, and authenticity of the data, providing a score that indicates the likelihood of the data being genuine and valuable.

## Scoring System:
--------------
The PoQ system uses a sophisticated scoring mechanism that combines:

1. Category-Specific Weights:
   - Each data category (e.g., Cart Items, Order History) has specific component weights
   - Weights are distributed across different aspects (e.g., quantity, uniqueness, time range)
   - Total weights per category sum to 100

2. Logarithmic Scoring:
   - Uses natural logarithmic scaling for continuous score improvement
   - Provides accelerated growth for exceeding minimum thresholds
   - Includes volume bonuses for large datasets
   - Applies progressive scaling for higher scores

3. Time Decay:
   - Exponential decay based on data recency
   - More generous weighting for recent data
   - Additional boost for very recent data
   - Half-life configuration per network (testnet/mainnet)

4. Validation Components:
   - Metadata score (60% weight)
   - LLM validation score (40% weight)
   - Combined with category-specific weights

5. Score Ranges:
   - Small datasets: 0.4-0.6 range
   - Large datasets: >0.8 range
   - Progressive scaling prevents score saturation

## Category Weights:
----------------
1. Retail Cart Items:
   - Number of items (40%)
   - Unique products (30%)
   - Date range (20%)
   - Active items ratio (10%)

2. Digital Items:
   - Number of items (30%)
   - Unique products (30%)
   - Total amount (40%)

3. Retail Order History:
   - Number of orders (20%)
   - Total amount (20%)
   - Unique products (20%)
   - Date range (10%)
   - Websites used (10%)
   - Payment methods (10%)
   - Order completion (5%)
   - Gift orders (5%)

4. Audible Purchase History:
   - Number of purchases (25%)
   - Total amount (30%)
   - Unique audiobooks (25%)
   - Date range (10%)
   - Purchase types (10%)

5. Audible Library:
   - Number of items (40%)
   - Unique audiobooks (30%)
   - Date range (20%)
   - Downloaded ratio (10%)

6. Audible Membership:
   - Number of billings (40%)
   - Total amount (40%)
   - Date range (20%)

7. Prime Video History:
   - Viewing sessions (25%)
   - Total hours (25%)
   - Unique titles (25%)
   - Date range (15%)
   - Devices used (10%)

## How to Use:
-----------
1. Setup:
   - Ensure Python 3.7+ installed
   - Install dependencies: `pip install -r requirements.txt`
   - Set OpenAI API key: `export OPENAI_API_KEY=your_api_key_here`

2. Run Tests:
   ```bash
   python scripts/test_all.py
   ```

3. Use in Code:
   ```python
   from proof_of_quality import proof_of_quality
   score = proof_of_quality('./data/path')
   ```

## Network Configurations:
----------------------
1. Testnet (Satori):
   - More lenient thresholds
   - Faster score growth
   - Suitable for testing and development

2. Mainnet:
   - Stricter thresholds
   - More gradual score growth
   - Production-ready validation

## Score Interpretation:
--------------------
- 0.0-0.4: Insufficient or low-quality data
- 0.4-0.6: Basic quality small dataset
- 0.6-0.8: Good quality medium dataset
- 0.8-1.0: High quality large dataset

## Future Improvements:
--------------------
- Dynamic threshold adjustment
- Machine learning-based validation
- Additional data type support
- Enhanced fraud detection
