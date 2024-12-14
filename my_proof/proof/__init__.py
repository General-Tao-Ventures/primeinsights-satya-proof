import json
import logging
import os
from typing import Dict, Any

from my_proof.models.proof_response import ProofResponse
from my_proof.proof.proof_of_authenticity import proof_of_authenticity
from my_proof.proof.proof_of_uniqueness import proof_of_uniqueness


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")
        
        authenticity = proof_of_authenticity(self.config)
        uniqueness = proof_of_uniqueness(self.config)
        

        # # Iterate through files and calculate data validity
        # members = None

        # for input_filename in os.listdir(self.config['input_dir']):
        #     input_file = os.path.join(self.config['input_dir'], input_filename)
        #     if os.path.splitext(input_file)[1].lower() == '.json':
        #         with open(input_file, 'r') as f:
        #             input_data = json.load(f)

        #             if input_filename == 'members.json':
        #                 members = input_data

        # # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        # self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        # self.proof_response.ownership = 1.0  # Does the data belong to the user? Or is it fraudulent?
        # self.proof_response.quality = len(members) / 5  # How high quality is the data?
        # self.proof_response.uniqueness = 0  # How unique is the data relative to other datasets? (Not implemented here)

        # # Calculate overall score and validity
        # self.proof_response.valid = self.config['passcode'] == '1234'  # Check if the passcode is correct
        # self.proof_response.score = (0.6 * self.proof_response.quality + 0.4 * self.proof_response.ownership) if self.proof_response.valid else 0

        # # Additional (public) properties to include in the proof about the data
        # self.proof_response.attributes = {
        #     'family_size': len(members),
        # }

        # # Additional metadata about the proof, written onchain
        # self.proof_response.metadata = {
        #     'score1': 4,
        #     'score2': 10,
        #     'score3': 3
        # }
        
        self.proof_response.authenticity = authenticity
        self.proof_response.ownership = authenticity
        self.proof_response.uniqueness = uniqueness

        return self.proof_response
