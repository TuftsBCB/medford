import hashlib

def calculate_sha_512(filename) :
    with open(filename, "rb") as f:
        bytes = f.read()
        hash = hashlib.sha512(bytes).hexdigest()
    return hash

def calculate_sha_256(filename) :
    with open(filename, "rb") as f:
        bytes = f.read()
        hash = hashlib.sha256(bytes).hexdigest()
    return hash
