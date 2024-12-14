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

from collections import Counter
from datetime import datetime
from .utils import parse_float, parse_date
from typing import List, Dict, Any

def analyze_data(file_name: str, data: list) -> dict:
    if file_name == "Retail.CartItems.1.csv":
        return analyze_cart_items_data(data)
    elif file_name == "Digital Items.csv":
        return analyze_digital_items_data(data)
    elif file_name in ["Retail.OrderHistory.1.csv", "Retail.OrderHistory.2.csv"]:
        return analyze_order_history_data(data)
    elif file_name == "Audible.PurchaseHistory.csv":
        return analyze_audible_purchase_history_data(data)
    elif file_name == "Audible.Library.csv":
        return analyze_audible_library_data(data)
    elif file_name == "Audible.MembershipBillings.csv":
        return analyze_audible_membership_billings_data(data)
    elif file_name == "PrimeVideo.ViewingHistory.csv":
        return analyze_prime_video_viewing_history_data(data)
    else:
        raise ValueError(f"Unknown file type: {file_name}")

def analyze_cart_items_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_items = len(data)
    total_quantity = sum(int(item['Quantity']) for item in data if item['Quantity'].isdigit())
    unique_products = len(set(item['ASIN'] for item in data if item['ASIN']))
    
    date_added_list = [parse_date(item['DateAddedToCart']) for item in data if item['DateAddedToCart']]
    earliest_added = min(date_added_list) if date_added_list else None
    latest_added = max(date_added_list) if date_added_list else None

    cart_lists = Counter(item['CartList'] for item in data if item['CartList'])
    one_click_buyable_count = Counter(item['OneClickBuyable'] for item in data if item['OneClickBuyable'])
    gift_wrapped_count = Counter(item['ToBeGiftWrapped'] for item in data if item['ToBeGiftWrapped'])

    prime_subscription_count = Counter(item['PrimeSubscription'] for item in data if item['PrimeSubscription'])
    pantry_count = Counter(item['Pantry'] for item in data if item['Pantry'])
    addon_count = Counter(item['AddOn'] for item in data if item['AddOn'])
    
    return {
        'num_items': num_items,
        'total_quantity': total_quantity,
        'unique_products': unique_products,
        'date_range': {
            'earliest': earliest_added.isoformat() if earliest_added else None,
            'latest': latest_added.isoformat() if latest_added else None,
        },
        'cart_lists': dict(cart_lists),
        'one_click_buyable': dict(one_click_buyable_count),
        'gift_wrapped': dict(gift_wrapped_count),
        'prime_subscription': dict(prime_subscription_count),
        'pantry': dict(pantry_count),
        'addon': dict(addon_count),
    }

def analyze_digital_items_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_items = len(data)
    unique_products = len(set(item['ASIN'] for item in data if item['ASIN']))
    unique_orders = len(set(item['OrderId'] for item in data if item['OrderId']))
    countries = Counter(item['DeclaredCountryCode'] for item in data if item['DeclaredCountryCode'])
    currencies = Counter(item['BaseCurrencyCode'] for item in data if item['BaseCurrencyCode'])
    product_names = [item['ProductName'] for item in data if item['ProductName']]
    total_amount = sum(parse_float(item.get('ListPriceAmount', '0')) for item in data)

    min_date = None
    max_date = None

    for entry in data:
        if entry['OrderDate'] == 'Not Applicable' or entry['FulfilledDate'] == 'Not Applicable':
            continue

        order_date = datetime.fromisoformat(entry['OrderDate'].replace('Z', '')) if 'OrderDate' in entry else None
        fulfilled_date = datetime.fromisoformat(entry['FulfilledDate'].replace('Z', '')) if 'FulfilledDate' in entry else None
        
        if order_date:
            if not min_date or order_date < min_date:
                min_date = order_date
            if not max_date or order_date > max_date:
                max_date = order_date
        
        if fulfilled_date:
            if not min_date or fulfilled_date < min_date:
                min_date = fulfilled_date
            if not max_date or fulfilled_date > max_date:
                max_date = fulfilled_date

    date_range = {
        'earliest': min_date.isoformat() if min_date else None,
        'latest': max_date.isoformat() if max_date else None
    }

    return {
        'num_items': num_items,
        'unique_products': unique_products,
        'unique_orders': unique_orders,
        'countries': dict(countries),
        'currencies': dict(currencies),
        'total_amount': round(total_amount, 2),
        'product_names_sample': product_names[:5],
        'date_range': date_range
    }

def analyze_order_history_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_orders = len(data)
    total_amount = sum(parse_float(order['Total Owed']) for order in data if order['Total Owed'])
    total_items = sum(int(order['Quantity']) for order in data if order['Quantity'])
    unique_products = len(set(order['ASIN'] for order in data if order['ASIN']))
    
    order_dates = [parse_date(order['Order Date']) for order in data if order['Order Date']]
    earliest_order = min(order_dates) if order_dates else None
    latest_order = max(order_dates) if order_dates else None

    websites = Counter(order['Website'] for order in data if order['Website'])
    payment_methods = Counter(order['Payment Instrument Type'] for order in data if order['Payment Instrument Type'])
    order_statuses = Counter(order['Order Status'] for order in data if order['Order Status'])
    
    total_shipping = sum(parse_float(order['Shipping Charge']) for order in data if order['Shipping Charge'])
    total_discounts = sum(parse_float(order['Total Discounts']) for order in data if order['Total Discounts'])

    most_expensive_item = max((parse_float(order['Unit Price']) for order in data if order['Unit Price']), default=0)

    gift_orders = sum(1 for order in data if order.get('Gift Message') != 'Not Available')

    return {
        'num_orders': num_orders,
        'total_amount': round(total_amount, 2),
        'avg_order_value': round(total_amount / num_orders, 2) if num_orders > 0 else 0,
        'total_items': total_items,
        'avg_items_per_order': round(total_items / num_orders, 2) if num_orders > 0 else 0,
        'unique_products': unique_products,
        'date_range': {
            'earliest': earliest_order.isoformat() if earliest_order else None,
            'latest': latest_order.isoformat() if latest_order else None,
        },
        'websites': dict(websites),
        'payment_methods': dict(payment_methods),
        'order_statuses': dict(order_statuses),
        'total_shipping': round(total_shipping, 2),
        'total_discounts': round(total_discounts, 2),
        'most_expensive_item': round(most_expensive_item, 2),
        'gift_orders_percentage': round((gift_orders / num_orders) * 100, 2) if num_orders > 0 else 0,
    }

def analyze_audible_purchase_history_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_purchases = len(data)
    total_amount = sum(parse_float(item['Price Paid Member']) for item in data if item['Price Paid Member'])
    unique_audiobooks = len(set(item['ASIN'] for item in data if item['ASIN']))

    order_dates = [parse_date(item['Order Place Date']) for item in data if item['Order Place Date']]
    earliest_order = min(order_dates) if order_dates else None
    latest_order = max(order_dates) if order_dates else None

    purchase_types = Counter(item['Type'] for item in data if item['Type'])
    statuses = Counter(item['Status'] for item in data if item['Status'])

    return {
        'num_purchases': num_purchases,
        'total_amount_spent': round(total_amount, 2),
        'unique_audiobooks': unique_audiobooks,
        'date_range': {
            'earliest': earliest_order.isoformat() if earliest_order else None,
            'latest': latest_order.isoformat() if latest_order else None,
        },
        'purchase_types': dict(purchase_types),
        'statuses': dict(statuses),
    }

def analyze_audible_library_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_items = len(data)
    unique_audiobooks = len(set(item['ASIN'] for item in data if item['ASIN']))
    
    date_added_list = [parse_date(item['Date Added']) for item in data if item['Date Added']]
    earliest_added = min(date_added_list) if date_added_list else None
    latest_added = max(date_added_list) if date_added_list else None

    downloaded_count = Counter(item['Downloaded'] for item in data if item['Downloaded'])
    deleted_count = Counter(item['Deleted'] for item in data if item['Deleted'])
    origin_types = Counter(item['Origin Type'] for item in data if item['Origin Type'])

    return {
        'num_items_in_library': num_items,
        'unique_audiobooks': unique_audiobooks,
        'date_range': {
            'earliest': earliest_added.isoformat() if earliest_added else None,
            'latest': latest_added.isoformat() if latest_added else None,
        },
        'downloaded': dict(downloaded_count),
        'deleted': dict(deleted_count),
        'origin_types': dict(origin_types),
    }

def analyze_audible_membership_billings_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_billings = len(data)
    total_amount = sum(parse_float(item['Total Amount']) for item in data if item['Total Amount'])
    
    billing_dates = [parse_date(item['Billing Period Start Date']) for item in data if item['Billing Period Start Date']]
    earliest_billing = min(billing_dates) if billing_dates else None
    latest_billing = max(billing_dates) if billing_dates else None

    plans = Counter(item['Plan'] for item in data if item['Plan'])
    statuses = Counter(item['Status'] for item in data if item['Status'])
    currencies = Counter(item['Currency'] for item in data if item['Currency'])

    return {
        'num_billings': num_billings,
        'total_amount_spent': round(total_amount, 2),
        'date_range': {
            'earliest': earliest_billing.isoformat() if earliest_billing else None,
            'latest': latest_billing.isoformat() if latest_billing else None,
        },
        'plans': dict(plans),
        'statuses': dict(statuses),
        'currencies': dict(currencies),
    }

def analyze_prime_video_viewing_history_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    num_sessions = len(data)
    total_seconds_viewed = sum(parse_float(item['Seconds Viewed']) for item in data if item['Seconds Viewed'])
    total_hours_viewed = total_seconds_viewed / 3600  # Convert seconds to hours
    
    unique_titles = len(set(item['Title'] for item in data if item['Title']))
    
    playback_dates = [parse_date(item['Playback Start Datetime (UTC)']) for item in data if item['Playback Start Datetime (UTC)']]
    earliest_playback = min(playback_dates) if playback_dates else None
    latest_playback = max(playback_dates) if playback_dates else None

    content_qualities = Counter(item['Content Quality Delivered'] for item in data if item['Content Quality Delivered'])
    devices = Counter(item['Device Manufacturer Name'] for item in data if item['Device Manufacturer Name'])
    
    return {
        'num_viewing_sessions': num_sessions,
        'total_hours_viewed': round(total_hours_viewed, 2),
        'unique_titles_watched': unique_titles,
        'date_range': {
            'earliest': earliest_playback.isoformat() if earliest_playback else None,
            'latest': latest_playback.isoformat() if latest_playback else None,
        },
        'content_qualities': dict(content_qualities),
        'devices_used': dict(devices),
    }
