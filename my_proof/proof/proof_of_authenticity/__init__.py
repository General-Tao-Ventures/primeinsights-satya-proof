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

import hashlib
import logging
import os
import requests
from typing import Dict, Any

def proof_of_authenticity(config: Dict[str, Any]) -> int:
    """
    1) Get API key from environment
    2) Check if hash of amazon_link equals to proof_key
    3) Call the remote /get_proof endpoint
    4) Find a data zip file in INPUT_DIR and compute its sha3 hash
    5) Compare hashes
    """

    input_zip_filepath = config.get('input_zip_filepath')
    tee_api_endpoint = config.get('tee_api_endpoint')
    prime_api_key = config.get('prime_api_key')
    amazon_link = config.get('amazon_link')
    proof_key = config.get('proof_key')

    # 1) Get API key from environment
    if not prime_api_key:
        raise RuntimeError("PRIMEINSIGHTS_TEE_API_KEY environment variable not set")

    # 2) Check if hash of amazon_link equals to proof_key
    link_hash = hashlib.sha3_256(amazon_link.encode('utf-8')).hexdigest()
    if link_hash != proof_key:
        raise ValueError(f"Amazon link hash {link_hash} does not match proof key {proof_key}")

    # 3) Call the remote /get_proof endpoint
    logging.info(f"Fetching reference data_hash from TEE for {proof_key}")
    headers = {
        "X-API-Key": prime_api_key
    }
    response = requests.get(
        f"{tee_api_endpoint}/proof/{proof_key}",
        headers=headers
    )
    if not response.ok:
        raise ValueError(f"Failed to fetch proof from TEE: {response.text}")

    resp_json = response.json()
    returned_hash = resp_json.get("data_hash")
    if not returned_hash:
        raise ValueError("No data_hash field in response")

    logging.info(f"Received reference data_hash from TEE: {returned_hash}")

    # 4) Find a data zip file in INPUT_DIR and compute its sha3 hash
    if not os.path.exists(input_zip_filepath):
        raise FileNotFoundError("No input zip file found.")

    with open(input_zip_filepath, 'rb') as f:
        file_data = f.read()
        computed_hash = hashlib.sha3_256(file_data).hexdigest()

    logging.info(f"Computed local hash of decrypted_amazon_data.zip: {computed_hash}")

    # 5) Compare hashes
    if computed_hash == returned_hash:
        return 1
    else:
        return 0
