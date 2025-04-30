

def get_password_from_bank(selected_bank:str):
     # Always ask the user for the password
    password = input(f"Enter password for {selected_bank} (leave empty if none): ").strip() or None
    return password