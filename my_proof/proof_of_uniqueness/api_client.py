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

import requests
from typing import List, Dict
from datasketch import MinHash
from my_proof.proof_of_uniqueness.minhash_utils import serialize_minhash, deserialize_minhash


class ProofOfUniquenessClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key
        }

    def save_minhash(self, user_id: str, minhash: MinHash) -> int:
        minhash_data = serialize_minhash(minhash)
        response = requests.post(
            f"{self.base_url}/minhash",
            headers=self.headers,
            json={"user_id": user_id, "minhash_data": minhash_data}
        )
        response.raise_for_status()
        return response.json()["id"]

    def query_similar_minhashes(self, minhash: MinHash, num_perm: int) -> List[Dict]:
        minhash_data = serialize_minhash(minhash)
        response = requests.post(
            f"{self.base_url}/minhash/query",
            headers=self.headers,
            json={"user_id": "", "minhash_data": minhash_data}
        )
        response.raise_for_status()
        candidates = response.json()["candidates"]
        return [
            {
                "id": entry["id"],
                "user_id": entry["user_id"],
                "minhash": deserialize_minhash(entry["minhash"], num_perm=num_perm),
                "similarity": entry["similarity"]
            }
            for entry in candidates
        ]
