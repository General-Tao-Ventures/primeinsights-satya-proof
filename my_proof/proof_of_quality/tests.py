from my_proof.proof_of_quality import pack_scores, unpack_scores

def test_pack_scores():
    metadata_scores_dict = {
        "Retail Cart Items": 100,
        "Digital Items": 9,
        "Retail Order History": 104,
        "Audible Purchase History": 122,
        "Audible Library": 241,
        "Audible Membership Billings": 38,
        "Prime Video Viewing History": 4,
    }
    validation_scores_dict = {
        "Retail Cart Items": 43,
        "Digital Items": 254,
        "Retail Order History": 1,
        "Audible Purchase History": 14,
        "Audible Library": 55,
        "Audible Membership Billings": 238,
        "Prime Video Viewing History": 144,
    }
    metadata_scores = [value for value in metadata_scores_dict.values()]
    validation_scores = [value for value in validation_scores_dict.values()]
    packed_str = pack_scores(metadata_scores, validation_scores)
    unpacked_metadata_scores, unpacked_validation_scores = unpack_scores(packed_str)
    print(f"metadata_scores: {metadata_scores}")
    print(f"validation_scores: {validation_scores}")
    print(f"packed_str: {packed_str}")
    print(f"unpacked metadata_scores: {unpacked_metadata_scores}")
    print(f"unpacked validation_scores: {unpacked_validation_scores}")
    assert metadata_scores == unpacked_metadata_scores
    assert validation_scores == unpacked_validation_scores
    print("Test passed")
    
if __name__ == "__main__":
    test_pack_scores()