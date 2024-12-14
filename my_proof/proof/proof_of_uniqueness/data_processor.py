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

import csv
from pathlib import Path
from typing import List, Dict, Any
from datasketch import MinHash


class DataProcessor:
    @staticmethod
    def process_order_history(unzipped_data_dir: str, num_perm: int) -> MinHash:
        csv_files = DataProcessor.gather_csv_files(unzipped_data_dir)
        if not csv_files:
            return None

        minhash = MinHash(num_perm=num_perm)
        for csv_file in csv_files:
            data = DataProcessor.read_and_normalize_csv(csv_file)
            features = DataProcessor.extract_features(data)
            DataProcessor.update_minhash(minhash, features)

        return minhash

    @staticmethod
    def gather_csv_files(unzipped_data_dir: str) -> List[Path]:
        return list(Path(unzipped_data_dir).rglob("*.csv"))

    @staticmethod
    def read_and_normalize_csv(csv_file: Path) -> List[Dict[str, Any]]:
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
        
        normalized_data = []
        for row in data:
            row = {k: v.strip().lower() if isinstance(v, str) else v for k, v in row.items()}
            fields_to_remove = ['Order Date', 'Ship Date', 'Order ID']
            for field in fields_to_remove:
                row.pop(field, None)
            normalized_data.append(row)
        
        return normalized_data

    @staticmethod
    def extract_features(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        features = {
            'products': set(),
            'total_amount': 0.0,
            'total_quantity': 0,
            'categories': set(),
        }

        for row in data:
            product = row.get('Product Name') or row.get('Title')
            if product:
                features['products'].add(product)

            amount = DataProcessor.parse_float(row.get('Total Owed') or row.get('Total Amount'))
            features['total_amount'] += amount

            quantity = DataProcessor.parse_int(row.get('Quantity') or row.get('Units'))
            features['total_quantity'] += quantity

            category = row.get('Category') or row.get('Product Group')
            if category:
                features['categories'].add(category)

        return features

    @staticmethod
    def update_minhash(minhash: MinHash, features: Dict[str, Any]):
        for product in features['products']:
            minhash.update(product.encode('utf-8'))
        for category in features['categories']:
            minhash.update(category.encode('utf-8'))
        minhash.update(f"amount:{features['total_amount']:.2f}".encode('utf-8'))
        minhash.update(f"quantity:{features['total_quantity']}".encode('utf-8'))

    @staticmethod
    def parse_float(value):
        if isinstance(value, str):
            value = value.strip().replace(',', '')
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_int(value):
        if isinstance(value, str):
            value = value.strip().replace(',', '')
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
