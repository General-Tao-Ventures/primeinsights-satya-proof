import json
import logging
import os
from typing import Dict, Any

from my_proof.models import ProofResponse
from my_proof.proof_of_authenticity import proof_of_authenticity
from my_proof.proof_of_uniqueness import proof_of_uniqueness
from my_proof.proof_of_quality import proof_of_quality


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")
        
        authenticity = proof_of_authenticity(self.config)
        uniqueness = proof_of_uniqueness(self.config)
        category_scores_packed_str, quality = proof_of_quality(self.config)

        self.proof_response.authenticity = authenticity
        self.proof_response.ownership = authenticity
        self.proof_response.uniqueness = uniqueness
        self.proof_response.quality = quality
        
        print(f"category_scores_packed_str: {category_scores_packed_str}")
        
        self.proof_response.metadata = category_scores_packed_str

        return self.proof_response
