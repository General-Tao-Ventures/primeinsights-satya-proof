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

import logging
from typing import Dict, Any
from my_proof.proof_of_uniqueness.api_client import ProofOfUniquenessClient
from my_proof.proof_of_uniqueness.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def proof_of_uniqueness(config: Dict[str, Any]) -> int:
    """
    Compute binary uniqueness score (0 or 1) for the given order history data.
    Returns:
        1 if the data is unique (no similar entries exist)
        0 if the data is too similar to existing entries or is a duplicate
    """
    client = ProofOfUniquenessClient(base_url=config['tee_api_endpoint'], api_key=config['prime_api_key'])
    
    input_extracted_dir = config["input_extracted_dir"]
    user_id = config["user_id"]
    
    minhash = DataProcessor.process_order_history(input_extracted_dir, num_perm=config['num_perm'])
    if not minhash:
        logger.warning(f"No valid data found for user {user_id}")
        return 0

    # Query the server for similar MinHashes
    similar_entries = client.query_similar_minhashes(minhash, num_perm=config['num_perm'])
    logger.info(f"Found {len(similar_entries)} candidate entries from LSH")

    if not similar_entries:
        client.save_minhash(user_id, minhash)
        logger.info("No similar entries found. Saving as new entry.")
        return 1

    # Find the highest similarity with existing entries
    max_similarity = max(entry["similarity"] for entry in similar_entries)
    logger.info(f"Highest similarity: {max_similarity:.4f}")

    # If similarity is above threshold, reject as duplicate
    if max_similarity >= config['uniqueness_threshold']:
        logger.warning(f"Data too similar to existing entry. Similarity: {max_similarity:.4f}")
        return 0

    # Data is sufficiently unique, save and accept
    client.save_minhash(user_id, minhash)
    logger.info("Data passed uniqueness check. Saving new entry.")
    return 1
