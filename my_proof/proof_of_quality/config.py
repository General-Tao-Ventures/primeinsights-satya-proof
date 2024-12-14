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
from munch import Munch, munchify

validation_config: Munch = munchify(
    {
        "satori": {
            # Core thresholds
            "MIN_ORDERS": 1,
            "MIN_TOTAL_AMOUNT": 5,
            "MIN_UNIQUE_PRODUCTS": 1,
            "THRESHOLD_SCORE": 10,
            "SAMPLE_SIZE": 3,
            "MAX_VALIDATION_CHUNK_SIZE": 4000,
            "GPT_MODEL": "gpt-4o-mini",
            "HALF_LIFE_DAYS": 730,
            "ROLLOFF_EXPONENT": 1.2,
            
            # File-specific thresholds
            "MIN_ITEMS": 1,
            "MIN_DIGITAL_ITEMS": 1,
            "MIN_LIBRARY_ITEMS": 1,
            "MIN_UNIQUE_AUDIOBOOKS": 1,
            "MIN_PURCHASES": 1,
            "MIN_BILLINGS": 1,
            "MIN_VIEWING_SESSIONS": 1,
            "MIN_TOTAL_HOURS": 0.5,
            "MIN_UNIQUE_TITLES": 1,
            "MIN_DATE_RANGE_DAYS": 1,
            "MIN_WEBSITES": 1,
            "MIN_PAYMENT_METHODS": 1,
            
            # Score scaling factors
            "SCORE_SCALING": 1.2,  # Slightly reduced for small datasets
            "LOG_BASE": 1.8  # Increased for slower growth
        },
        
        # Mainnet - recalibrated for large datasets to score >0.8
        "mainnet": {
            # Core thresholds - further reduced minimums
            "MIN_ORDERS": 2,
            "MIN_TOTAL_AMOUNT": 20,
            "MIN_UNIQUE_PRODUCTS": 2,
            "THRESHOLD_SCORE": 15,
            "SAMPLE_SIZE": 30,
            "MAX_VALIDATION_CHUNK_SIZE": 16285,
            "GPT_MODEL": "gpt-4o",
            "HALF_LIFE_DAYS": 365,
            "ROLLOFF_EXPONENT": 1.2,
            
            # Global minimums            
            "MIN_DATA_TIME": 365*5, # 5 years
            "MIN_PURCHASES_PER_WEEK": 3, # 3 purchases per week

            # File-specific thresholds - lowered further
            "MIN_ITEMS": 2,
            "MIN_DIGITAL_ITEMS": 2,
            "MIN_LIBRARY_ITEMS": 2,
            "MIN_UNIQUE_AUDIOBOOKS": 2,
            "MIN_PURCHASES": 2,
            "MIN_BILLINGS": 1,
            "MIN_VIEWING_SESSIONS": 2,
            "MIN_TOTAL_HOURS": 1,
            "MIN_UNIQUE_TITLES": 2,
            "MIN_DATE_RANGE_DAYS": 7,
            "MIN_WEBSITES": 1,
            "MIN_PAYMENT_METHODS": 1,
            
            # Score scaling factors - significantly increased
            "SCORE_SCALING": 2.5,  # Increased scaling for higher metadata scores
            "LOG_BASE": 1.2  # Further reduced for faster growth
        }
    }
)

INTERESTING_FILES = [
    "Retail.CartItems.1.csv",
    "Digital Items.csv",
    "Retail.OrderHistory.1.csv",
    "Retail.OrderHistory.2.csv",
    "Audible.PurchaseHistory.csv",
    "Audible.Library.csv",
    "Audible.MembershipBillings.csv",
    "PrimeVideo.ViewingHistory.csv",
]

WEIGHT_PER_FILE = {
    "Retail.CartItems.1.csv": 1.5,
    "Digital Items.csv": 1.5,
    "Retail.OrderHistory.1.csv": 4.0,
    "Retail.OrderHistory.2.csv": 4.0,
    "Audible.PurchaseHistory.csv": 2.0,
    "Audible.Library.csv": 2.0,
    "Audible.MembershipBillings.csv": 1.5,
    "PrimeVideo.ViewingHistory.csv": 1.0,
}

DATA_TYPE_MAP = {
    "Retail.CartItems.1.csv": "Retail Cart Items",
    "Digital Items.csv": "Digital Items",
    "Retail.OrderHistory.1.csv": "Retail Order History",
    "Retail.OrderHistory.2.csv": "Retail Order History",
    "Audible.PurchaseHistory.csv": "Audible Purchase History",
    "Audible.Library.csv": "Audible Library",
    "Audible.MembershipBillings.csv": "Audible Membership Billings",
    "PrimeVideo.ViewingHistory.csv": "Prime Video Viewing History",
}

def get_validation_config(config: Dict[str, any]):
    return validation_config[config['network']]
