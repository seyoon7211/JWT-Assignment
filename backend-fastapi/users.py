import hashlib, hmac, secrets

_accounts = []
for i, name in enumerate(("Alice", "Bob"), 1):
    salt = secrets.token_bytes(16)
    _accounts.append(
        dict(
            id=i,
            name=name,
            email=f"{name.lower()}@class.test",
            salt=salt,
            hash=hashlib.scrypt(
                b"Classroom!2026", salt=salt, n=16384, r=8, p=1, dklen=32
            ),
        )
    )


def find_public(user_id):
    user = next((u for u in _accounts if u["id"] == user_id), None)
    return {k: user[k] for k in ("id", "name", "email")} if user else None


def verify_credentials(email, password):
    user = next((u for u in _accounts if u["email"] == email), None)
    reference = user or _accounts[0]
    digest = hashlib.scrypt(
        password.encode(), salt=reference["salt"], n=16384, r=8, p=1, dklen=32
    )
    valid = hmac.compare_digest(digest, reference["hash"])
    return find_public(user["id"]) if user and valid else None
