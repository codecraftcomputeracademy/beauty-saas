from app.core.security import hash_password, verify_password


def main():
    password = "TestPassword@123"

    password_hash = hash_password(password)

    print("Password hashing: PASS")
    print(f"Hash generated: {password_hash[:30]}...")

    if password_hash == password:
        print("ERROR: Plaintext password was stored")
        return

    if verify_password(password, password_hash):
        print("Correct password verification: PASS")
    else:
        print("Correct password verification: FAIL")

    if not verify_password(
        "WrongPassword@123",
        password_hash,
    ):
        print("Incorrect password rejection: PASS")
    else:
        print("Incorrect password rejection: FAIL")


if __name__ == "__main__":
    main()