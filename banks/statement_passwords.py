BANK_PASSWORDS = {
    "PBB": "02APR1969",
    "UOB": None,
    "HLB": None,   # No password
    "RHB": "6096690402",
    "MYB": "02Apr1969",
    "CIMB": "t@026096",
}

def get_password_from_bank(selected_bank:str):
    password = BANK_PASSWORDS.get(selected_bank)

    # Ask user only if not pre-defined
    if not password :
        password = input("Enter password (leave empty if none): ").strip() or None
    else:
        print(f"🔐 Using saved password for {selected_bank}")

    return password