from my_proof.proof_of_quality import pack_scores, unpack_scores

def test_pack_scores():
    metadata_scores_dict = {
        "Retail.CartItems.1.csv": 100,
        "Digital Items.csv": 9,
        "Retail.OrderHistory.1.csv": 104,
        "Retail.OrderHistory.2.csv": 122,
        "Audible.PurchaseHistory.csv": 241,
        "Audible.Library.csv": 38,
        "Audible.MembershipBillings.csv": 4,
        "PrimeVideo.ViewingHistory.csv": 234,
    }
    validation_scores_dict = {
        "Retail.CartItems.1.csv": 43,
        "Digital Items.csv": 254,
        "Retail.OrderHistory.1.csv": 1,
        "Retail.OrderHistory.2.csv": 14,
        "Audible.PurchaseHistory.csv": 55,
        "Audible.Library.csv": 238,
        "Audible.MembershipBillings.csv": 144,
        "PrimeVideo.ViewingHistory.csv": 24,
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