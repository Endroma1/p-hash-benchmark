from typing import Generator 
import db

def main():
    process_images()
    
def process_images():
    """
    Compares each hash in each hashing method.
    """
    with db.Database.from_config() as database:
        for hash_method in iter_hash_methods(database):
            for hash in iter_hashes(database, hash_method.id):
                for compare in iter_hashes(database,hash_method.id, min_id=hash.id):   # min_id: Start at the id of the current hash being compared. This way, (A,B) and (B,A) are skipped
                    hamming = match_images(hash.hash, compare.hash)
                    database.add_hamming_distance(hamming, hash.id, compare.id)

def iter_hashes(database:db.Database, method_id:int, min_id:int = 1)->Generator[db.Hash]:
    """
    Iterates over all hashes in db, sequentially and in batches.
    """
    amount=100
    while True:
        batch = database.get_hashes(amount, min_id, method_id)
        if not batch:
            break
        for i in batch:
            yield i
        min_id = max(h.id for h in batch) + 1

def iter_hash_methods(database:db.Database, min_id:int = 1)->Generator[db.HashMethod]:
    """
    Iterates over all hashes in db, sequentially and in batches.
    """
    amount=100
    while True:
        batch = database.get_hash_methods(amount, min_id)
        if not batch:
            break
        for i in batch:
            yield i
        min_id += amount


def match_images(hash1:str, hash2:str)->float:
    if len(hash1) != len(hash2):
        raise ValueError("Hashes must have the same length")

    int1 = int(hash1, 16)
    int2 = int(hash2, 16)

    xor = int1 ^ int2
    distance = bin(xor).count("1")

    total_bits = len(hash1) * 4

    return distance / total_bits

if __name__ == "__main__":
    main()
