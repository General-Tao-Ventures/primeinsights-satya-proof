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
import logging
from typing import Dict, List, Tuple, Any
from pathlib import Path
from my_proof.utils import remote_log
from .config import INTERESTING_FILES, get_validation_config
from .data_analyzers import analyze_data
from .score_calculators import calculate_score
from .validators import validate_sample

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_csv_files(unzipped_file_path: str) -> List[Path]:
    """Find all relevant CSV files in the given directory."""
    folder_dirs = [f for f in Path(unzipped_file_path).iterdir() if f.is_dir()]
    files = [[f for f in d.iterdir() if f.is_file()]
             for d in folder_dirs if [f for f in d.iterdir() if f.is_file()] != []]
    files = [item for sublist in files for item in sublist]
    return [f for f in files if f.suffix == ".csv" and f.name in INTERESTING_FILES]


def process_single_file(csv_file: Path, config: Dict[str, any]) -> Dict:
    """Process a single CSV file and return its scores."""
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        file_data = list(csv_reader)

    # Calculate metadata score
    metadata = analyze_data(csv_file.name, file_data)
    validation_config = get_validation_config(config)
    metadata_score = calculate_score(csv_file.name, metadata, validation_config)
    logger.info(f"Metadata score for {csv_file.name}: {metadata_score}")
    remote_log(config, f"Metadata score for {csv_file.name}: {metadata_score}")

    # Calculate validation score
    if "OPENAI_API_KEY" in config and metadata_score["is_valid"]:
        logger.info("OPENAI_API_KEY is set. Performing LLM validation.")
        remote_log(config, "OPENAI_API_KEY is set. Performing LLM validation.")
        validation_score = validate_sample(file_data, csv_file.name, config["OPENAI_API_KEY"], validation_config)
    else:
        logger.info("OPENAI_API_KEY not set or metadata invalid. Skipping LLM validation.")
        remote_log(config, "OPENAI_API_KEY not set or metadata invalid. Skipping LLM validation.")
        validation_score = {
            "is_valid": False,
            "score": 0,
        }
    logger.info(f"Validation score for {csv_file.name}: {validation_score}")
    remote_log(config, f"Validation score for {csv_file.name}: {validation_score}")

    return {
        "metadata_score": metadata_score,
        "validation_openai_score": validation_score
    }


def quantize_scores(scores: List[float]) -> List[int]:
    """Quantize scores to the uint16 range (0 to 255)."""
    quantized_scores = [int(score * 255) for score in scores]
    return quantized_scores


def pack_scores_to_bytes(metadata_scores: List[int], validation_scores: List[int]) -> bytes:
    """
    Packs metadata and validation scores into a Big Endian byte array.
    Each score is stored as a uint16 (2 bytes) in Big Endian format.
    
    Format: [metadata_scores][validation_scores]
    Each section contains scores as consecutive uint16 values.

    Args:
        metadata_scores (list of int): A list of uint16 metadata scores
        validation_scores (list of int): A list of uint16 validation scores

    Returns:
        bytes: A byte array containing the packed scores in Big Endian format

    Raises:
        ValueError: If the input lists are not of the same length or scores are out of range
    """
    import struct

    if len(metadata_scores) != len(validation_scores):
        raise ValueError("metadata_scores and validation_scores must be the same length")

    packed_bytes = b''

    # Pack metadata scores in Big Endian format
    for score in metadata_scores:
        if not 0 <= score <= 255:
            raise ValueError("Metadata scores must be uint16 values between 0 and 255")
        # '>H' specifies big-endian unsigned short (2 bytes)
        packed_bytes += struct.pack('>H', score)

    # Pack validation scores in Big Endian format
    for score in validation_scores:
        if not 0 <= score <= 255:
            raise ValueError("Validation scores must be uint16 values between 0 and 255")
        packed_bytes += struct.pack('>H', score)

    return packed_bytes


def unpack_scores_from_bytes(packed_bytes: bytes) -> Tuple[List[int], List[int]]:
    """
    Unpacks the byte array into metadata and validation scores.

    Args:
        packed_bytes (bytes): The packed byte array.

    Returns:
        Tuple[List[int], List[int]]: The metadata and validation scores as lists of integers.
    """
    import struct

    total_scores = len(packed_bytes) // 2  # Each uint16 is 2 bytes
    num_categories = total_scores // 2

    metadata_scores = []
    validation_scores = []

    # Unpack metadata scores
    for i in range(num_categories):
        score_bytes = packed_bytes[i*2:(i+1)*2]
        score = struct.unpack('>H', score_bytes)[0]
        metadata_scores.append(score)

    # Unpack validation scores
    for i in range(num_categories, num_categories*2):
        score_bytes = packed_bytes[i*2:(i+1)*2]
        score = struct.unpack('>H', score_bytes)[0]
        validation_scores.append(score)

    return metadata_scores, validation_scores


def pack_scores(metadata_scores: List[int], validation_scores: List[int]) -> str:
    if len(metadata_scores) != len(validation_scores):
        raise ValueError("metadata_scores and validation_scores must be the same length")

    packed_str = ''

    # Pack metadata scores in Big Endian format
    for score in metadata_scores:
        if not 0 <= score <= 255:
            raise ValueError("Metadata scores must be uint16 values between 0 and 255")
        # '>H' specifies big-endian unsigned short (2 bytes)
        packed_str += f"{score:02x}"

    # Pack validation scores in Big Endian format
    for score in validation_scores:
        if not 0 <= score <= 255:
            raise ValueError("Validation scores must be uint16 values between 0 and 255")
        packed_str += f"{score:02x}"

    return packed_str


def unpack_scores(packed_str: str) -> Tuple[List[int], List[int]]:
    # total_scores = len(packed_bytes) // 2  # Each uint16 is 2 bytes
    # num_categories = total_scores // 2

    # metadata_scores = []
    # validation_scores = []

    # # Unpack metadata scores
    # for i in range(num_categories):
    #     score_bytes = packed_bytes[i*2:(i+1)*2]
    #     score = struct.unpack('>H', score_bytes)[0]
    #     metadata_scores.append(score)

    # # Unpack validation scores
    # for i in range(num_categories, num_categories*2):
    #     score_bytes = packed_bytes[i*2:(i+1)*2]
    #     score = struct.unpack('>H', score_bytes)[0]
    #     validation_scores.append(score)

    # return metadata_scores, validation_scores

    length = len(packed_str)
    total_scores = length // 2  # Each uint16 is 2 bytes
    num_categories = total_scores // 2
    
    metadata_scores = []
    validation_scores = []
    
    # Unpack metadata scores
    for i in range(0, length // 2, 2):
        metadata_scores.append(int(packed_str[i:i + 2], 16))
    
    # Unpack validation scores
    for i in range(length // 2, length, 2):
        validation_scores.append(int(packed_str[i:i + 2], 16))
    
    return metadata_scores, validation_scores


def calculate_weighted_scores(scores: Dict) -> Dict[str, Tuple[float, float]]:
    """Calculate weighted scores for each file."""
    weighted_scores = {}

    for name in INTERESTING_FILES:
        if name in scores:
            print(f"Processing {name}")
            print(f"Metadata score: {scores[name]['metadata_score']}")
            print(f"Validation score: {scores[name]['validation_openai_score']}")

            # Both scores should already be in 0-1 range
            metadata_score = scores[name]["metadata_score"]["score"]
            validation_score = scores[name]["validation_openai_score"]["score"]

            weighted_scores[name] = (metadata_score, validation_score)
            print()

    return weighted_scores


def proof_of_quality(config: Dict[str, Any]) -> Tuple[str, Dict[str, Tuple[float, float]]]:
    """
    Calculate proof of quality scores for all relevant files in the given directory.

    Args:
        input_extracted_dir: Path to directory containing the data files

    Returns:
        bytes: Packed byte array containing the scores
    """
    # Find relevant CSV files
    csv_files = find_csv_files(config.get('input_extracted_dir'))
    logger.info(f"Processing {len(csv_files)} CSV files")
    remote_log(config, f"Processing {len(csv_files)} CSV files")

    # Process each file
    scores = {}
    for csv_file in csv_files:
        logger.info(f"Processing file: {csv_file.name}")
        remote_log(config, f"Processing file: {csv_file.name}")
        scores[csv_file.name] = process_single_file(csv_file, config)

    # Calculate final scores
    category_scores = calculate_weighted_scores(scores)
    # total_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0

    # Log results
    logger.info(f"Pre-Weighted Scores: {scores}")
    remote_log(config, f"Pre-Weighted Scores: {scores}")
    logger.info(f"Category Scores: {category_scores}")
    remote_log(config, f"Category Scores: {category_scores}")

    return post_process_scores(category_scores), category_scores


def post_process_scores(scores: Dict[str, Tuple[float, float]]) -> str:
    """
    Encode scores into a packed byte array in Big Endian format.
    Each score is encoded as a uint16 (2 bytes) in the following format:
    [metadata_scores (2 bytes each)][validation_scores (2 bytes each)]
    
    For example, with 2 files:
    [m1_hi m1_lo][m2_hi m2_lo][v1_hi v1_lo][v2_hi v2_lo]
    where m = metadata score, v = validation score, hi/lo = high/low bytes

    Args:
        scores: Dictionary of file names to (metadata_score, validation_score) tuples

    Returns:
        bytes: Packed byte array containing the scores in Big Endian format
    """
    # Create ordered lists of scores, using 0.0 for missing files
    ordered_metadata_scores = []
    ordered_validation_scores = []
    for file_name in INTERESTING_FILES:
        if file_name in scores:
            metadata_score, validation_score = scores[file_name]
        else:
            metadata_score = 0.0
            validation_score = 0.0
        ordered_metadata_scores.append(metadata_score)
        ordered_validation_scores.append(validation_score)

    # Quantize scores to uint16 range (0 to 255)
    quantized_metadata_scores = quantize_scores(ordered_metadata_scores)
    quantized_validation_scores = quantize_scores(ordered_validation_scores)

    # Pack scores into bytes using Big Endian format
    packed_scores = pack_scores(quantized_metadata_scores, quantized_validation_scores)

    return packed_scores


def post_process_decode(packed_scores: str) -> Dict[str, Tuple[float, float]]:
    """
    Decode packed byte array back into scores dictionary.

    Args:
        packed_scores: Packed byte array containing the scores

    Returns:
        Dict[str, Tuple[float, float]]: Mapping of filenames to (metadata_score, validation_score)
    """
    # Unpack scores
    metadata_scores, validation_scores = unpack_scores(packed_scores)

    # Convert quantized scores back to float in range 0.0 to 1.0
    decoded_metadata_scores = [score / 255 for score in metadata_scores]
    decoded_validation_scores = [score / 255 for score in validation_scores]

    # Reconstruct dictionary, filtering out zero scores
    scores_dict = {}
    for file_name, metadata_score, validation_score in zip(INTERESTING_FILES, decoded_metadata_scores, decoded_validation_scores):
        if metadata_score > 0.0 or validation_score > 0.0:
            scores_dict[file_name] = (metadata_score, validation_score)

    return scores_dict


def test_post_process_scores():
    """Test encoding/decoding with missing files."""
    # Test case 1: Complete dictionary
    scores = {
        "Retail.CartItems.1.csv": (0.5, 0.6),
        "Digital Items.csv": (0.2, 0.3),
        "Retail.OrderHistory.1.csv": (0.54, 0.7),
        "Retail.OrderHistory.2.csv": (0.88, 0.9),
        "Audible.PurchaseHistory.csv": (0.55, 0.65),
        "Audible.Library.csv": (0.221, 0.5),
        "Audible.MembershipBillings.csv": (0.4552, 0.4),
        "PrimeVideo.ViewingHistory.csv": (0.1775, 0.3),
    }

    # Test case 2: Partial dictionary
    partial_scores = {
        "Retail.CartItems.1.csv": (0.5, 0.6),
        "Digital Items.csv": (0.2, 0.3),
        "Retail.OrderHistory.1.csv": (0.54, 0.7),
    }

    # Test both cases
    for test_scores in [scores, partial_scores]:
        print(f"\nTesting with {len(test_scores)} files:")
        post_processed_scores = post_process_scores(test_scores)
        decoded_scores = post_process_decode(post_processed_scores)

        print(f"Original scores: {test_scores}")
        print(f"Decoded scores: {decoded_scores}")

        # Verify reconstruction
        for file_name, (metadata_score, validation_score) in test_scores.items():
            decoded_metadata_score, decoded_validation_score = decoded_scores.get(file_name, (0.0, 0.0))
            assert abs(decoded_metadata_score - metadata_score) < 0.001, \
                f"Metadata score mismatch for {file_name}: {metadata_score} vs {decoded_metadata_score}"
            assert abs(decoded_validation_score - validation_score) < 0.001, \
                f"Validation score mismatch for {file_name}: {validation_score} vs {decoded_validation_score}"

        # Verify missing files are not in decoded output
        for file_name in INTERESTING_FILES:
            if file_name not in test_scores:
                assert file_name not in decoded_scores, \
                    f"Missing file {file_name} should not be in decoded output"

    print("\nAll tests passed!")


def test_proof_of_quality(unzipped_file_base_path: str):
    """Run proof of quality tests on small and large datasets."""
    for dataset in ["small", "large"]:
        unzipped_file_path = f"{unzipped_file_base_path}/{dataset}"
        print(f"Running proof of quality on {unzipped_file_path}")
        packed_scores = proof_of_quality(unzipped_file_path)
        decoded_scores = post_process_decode(packed_scores)
        print(f"{dataset.capitalize()} Data Scores: {decoded_scores}")
