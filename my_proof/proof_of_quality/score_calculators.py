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

from datetime import datetime
from typing import Dict, Any
from .utils import calculate_log_score, calculate_time_weight

def calculate_score(file_name: str, metadata: dict, validation_config: Dict[str, Any]) -> dict:
    """
    Calculate score based on file type.
    Returns raw component scores without category weights.
    """
    if file_name == "Retail.CartItems.1.csv":
        return calculate_cart_items_score(metadata, validation_config)
    elif file_name == "Digital Items.csv":
        return calculate_digital_items_score(metadata, validation_config)
    elif file_name in ["Retail.OrderHistory.1.csv", "Retail.OrderHistory.2.csv"]:
        return calculate_retail_order_history_score(metadata, validation_config)
    elif file_name == "Audible.PurchaseHistory.csv":
        return calculate_audible_purchase_history_score(metadata, validation_config)
    elif file_name == "Audible.Library.csv":
        return calculate_audible_library_score(metadata, validation_config)
    elif file_name == "Audible.MembershipBillings.csv":
        return calculate_audible_membership_billings_score(metadata, validation_config)
    elif file_name == "PrimeVideo.ViewingHistory.csv":
        return calculate_prime_video_viewing_history_score(metadata, validation_config)
    else:
        raise ValueError(f"Unknown file type: {file_name}")

def calculate_cart_items_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_items = validation_config.get("MIN_ITEMS", 5)
    min_unique_products = validation_config.get("MIN_UNIQUE_PRODUCTS", 3)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 30)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    num_items_score = calculate_log_score(metadata["num_items"], min_items, validation_config)
    unique_products_score = calculate_log_score(metadata["unique_products"], min_unique_products, validation_config)
    date_range_score = 0
    active_ratio_score = 0
    
    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    active_items = metadata['cart_lists'].get('active', 0)
    total_items = metadata['num_items']
    active_ratio_score = active_items / total_items if total_items > 0 else 0

    # Combine scores with equal weights (sum to 1)
    score = (num_items_score * 0.3 + 
             unique_products_score * 0.3 + 
             date_range_score * 0.2 + 
             active_ratio_score * 0.2)

    # Apply time weight (already 0-1)
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_items"] >= min_items and
        metadata["unique_products"] >= min_unique_products and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100  # Convert threshold to 0-1 scale
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_digital_items_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_items = validation_config.get("MIN_DIGITAL_ITEMS", 3)
    min_unique_products = validation_config.get("MIN_UNIQUE_PRODUCTS", 2)
    min_total_amount = validation_config.get("MIN_TOTAL_AMOUNT", 50)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    num_items_score = calculate_log_score(metadata["num_items"], min_items, validation_config)
    unique_products_score = calculate_log_score(metadata["unique_products"], min_unique_products, validation_config)
    total_amount_score = calculate_log_score(metadata["total_amount"], min_total_amount, validation_config)

    # Combine scores with weights summing to 1
    score = (num_items_score * 0.3 +
             unique_products_score * 0.3 +
             total_amount_score * 0.4)

    # Apply time weight (already 0-1)
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_items"] >= min_items and
        metadata["unique_products"] >= min_unique_products and
        metadata["total_amount"] >= min_total_amount and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_retail_order_history_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_orders = validation_config.get("MIN_ORDERS", 5)
    min_total_amount = validation_config.get("MIN_TOTAL_AMOUNT", 100)
    min_unique_products = validation_config.get("MIN_UNIQUE_PRODUCTS", 3)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 30)
    min_websites = validation_config.get("MIN_WEBSITES", 1)
    min_payment_methods = validation_config.get("MIN_PAYMENT_METHODS", 1)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Check global minima for order history data
    min_data_time = validation_config.get("MIN_DATA_TIME", 365*5)  # 5 years default
    min_purchases_per_week = validation_config.get("MIN_PURCHASES_PER_WEEK", 3)  # 3 per week default

    # Calculate date range and purchases per week
    date_range_days = 0
    purchases_per_week = 0
    
    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        
        # Calculate purchases per week
        weeks = date_range_days / 7 if date_range_days > 0 else 1
        purchases_per_week = metadata["num_orders"] / weeks if weeks > 0 else 0

    # Check global minima - return zero score if not met
    if date_range_days < min_data_time or purchases_per_week < min_purchases_per_week:
        return {
            'is_valid': False,
            'score': 0.0,
            'reasons': [
                f"Date range ({date_range_days} days) below minimum ({min_data_time} days)" if date_range_days < min_data_time else None,
                f"Purchases per week ({purchases_per_week:.1f}) below minimum ({min_purchases_per_week})" if purchases_per_week < min_purchases_per_week else None
            ]
        }

    # Rest of the scoring logic remains the same...
    num_orders_score = calculate_log_score(metadata["num_orders"], min_orders, validation_config)
    total_amount_score = calculate_log_score(metadata["total_amount"], min_total_amount, validation_config)
    unique_products_score = calculate_log_score(metadata["unique_products"], min_unique_products, validation_config)
    date_range_score = 0
    websites_score = calculate_log_score(len(metadata["websites"]), min_websites, validation_config)
    payment_methods_score = calculate_log_score(len(metadata["payment_methods"]), min_payment_methods, validation_config)
    
    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    # Calculate normalized ratios (0-1)
    completed_orders = metadata["order_statuses"].get("Closed", 0)
    completion_rate = completed_orders / metadata["num_orders"] if metadata["num_orders"] > 0 else 0
    gift_orders_rate = min(metadata["gift_orders_percentage"] / 100, 1.0)

    # Combine scores with weights summing to 1
    score = (num_orders_score * 0.2 +
             total_amount_score * 0.2 +
             unique_products_score * 0.2 +
             date_range_score * 0.1 +
             websites_score * 0.1 +
             payment_methods_score * 0.1 +
             completion_rate * 0.05 +
             gift_orders_rate * 0.05)

    # Apply time weight
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_orders"] >= min_orders and
        metadata["total_amount"] >= min_total_amount and
        metadata["unique_products"] >= min_unique_products and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_audible_purchase_history_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_purchases = validation_config.get("MIN_PURCHASES", 5)
    min_total_amount = validation_config.get("MIN_TOTAL_AMOUNT", 75)
    min_unique_audiobooks = validation_config.get("MIN_UNIQUE_AUDIOBOOKS", 3)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 60)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    num_purchases_score = calculate_log_score(metadata["num_purchases"], min_purchases, validation_config)
    total_amount_score = calculate_log_score(metadata["total_amount_spent"], min_total_amount, validation_config)
    unique_audiobooks_score = calculate_log_score(metadata["unique_audiobooks"], min_unique_audiobooks, validation_config)
    date_range_score = 0
    purchase_types_score = calculate_log_score(len(metadata["purchase_types"]), 2, validation_config)

    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    # Combine scores with weights summing to 1
    score = (num_purchases_score * 0.25 +
             total_amount_score * 0.30 +
             unique_audiobooks_score * 0.25 +
             date_range_score * 0.10 +
             purchase_types_score * 0.10)

    # Apply time weight
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_purchases"] >= min_purchases and
        metadata["total_amount_spent"] >= min_total_amount and
        metadata["unique_audiobooks"] >= min_unique_audiobooks and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_audible_library_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_library_items = validation_config.get("MIN_LIBRARY_ITEMS", 10)
    min_unique_audiobooks = validation_config.get("MIN_UNIQUE_AUDIOBOOKS", 5)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 90)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    num_items_score = calculate_log_score(metadata["num_items_in_library"], min_library_items, validation_config)
    unique_audiobooks_score = calculate_log_score(metadata["unique_audiobooks"], min_unique_audiobooks, validation_config)
    date_range_score = 0
    
    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    # Calculate downloaded ratio (already 0-1)
    downloaded_yes = metadata['downloaded'].get('Yes', 0)
    total_items = metadata['num_items_in_library']
    downloaded_ratio = downloaded_yes / total_items if total_items > 0 else 0

    # Combine scores with weights summing to 1
    score = (num_items_score * 0.40 +
             unique_audiobooks_score * 0.30 +
             date_range_score * 0.20 +
             downloaded_ratio * 0.10)

    # Apply time weight
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_items_in_library"] >= min_library_items and
        metadata["unique_audiobooks"] >= min_unique_audiobooks and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_audible_membership_billings_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_billings = validation_config.get("MIN_BILLINGS", 3)
    min_total_amount = validation_config.get("MIN_TOTAL_AMOUNT", 30)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 90)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    num_billings_score = calculate_log_score(metadata["num_billings"], min_billings, validation_config)
    total_amount_score = calculate_log_score(metadata["total_amount_spent"], min_total_amount, validation_config)
    date_range_score = 0

    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    # Combine scores with weights summing to 1
    score = (num_billings_score * 0.40 +
             total_amount_score * 0.40 +
             date_range_score * 0.20)

    # Apply time weight
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_billings"] >= min_billings and
        metadata["total_amount_spent"] >= min_total_amount and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }

def calculate_prime_video_viewing_history_score(metadata: Dict[str, Any], validation_config: Dict[str, Any]) -> Dict[str, Any]:
    min_viewing_sessions = validation_config.get("MIN_VIEWING_SESSIONS", 5)
    min_total_hours = validation_config.get("MIN_TOTAL_HOURS", 10)
    min_unique_titles = validation_config.get("MIN_UNIQUE_TITLES", 3)
    min_date_range_days = validation_config.get("MIN_DATE_RANGE_DAYS", 60)
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize component scores (each between 0 and 1)
    sessions_score = calculate_log_score(metadata["num_viewing_sessions"], min_viewing_sessions, validation_config)
    hours_score = calculate_log_score(metadata["total_hours_viewed"], min_total_hours, validation_config)
    titles_score = calculate_log_score(metadata["unique_titles_watched"], min_unique_titles, validation_config)
    date_range_score = 0
    devices_score = calculate_log_score(len(metadata["devices_used"]), 2, validation_config)

    if metadata['date_range']['earliest'] and metadata['date_range']['latest']:
        earliest = datetime.fromisoformat(metadata['date_range']['earliest'])
        latest = datetime.fromisoformat(metadata['date_range']['latest'])
        date_range_days = (latest - earliest).days
        date_range_score = calculate_log_score(date_range_days, min_date_range_days, validation_config)

    # Combine scores with weights summing to 1
    score = (sessions_score * 0.25 +
             hours_score * 0.25 +
             titles_score * 0.25 +
             date_range_score * 0.15 +
             devices_score * 0.10)

    # Apply time weight
    time_weight, age_in_days = calculate_time_weight(metadata['date_range'])
    score *= time_weight

    is_valid = (
        metadata["num_viewing_sessions"] >= min_viewing_sessions and
        metadata["total_hours_viewed"] >= min_total_hours and
        metadata["unique_titles_watched"] >= min_unique_titles and
        date_range_days >= min_date_range_days and
        score >= threshold_score/100
    )

    return {
        'is_valid': is_valid,
        'score': score,
        'reasons': []
    }
