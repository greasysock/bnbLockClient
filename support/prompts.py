import getpass

def get_username():
    try:
        username = str(input('Username: '))
        char_val = [ord(c) for c in username]
        invalid_chars = list()
        for char in char_val:
            if char == 45 or char == 46 or char == 95:
                continue
            elif char >= 48 and char <= 57:
                continue
            elif char >= 65 and char <= 90:
                continue
            elif char >= 97 and char <= 122:
                continue
            else:
                invalid_chars.append(char)
        if invalid_chars != []:
            raise (InvalidUsernameException(invalid_chars, 0))
        elif username.__len__() > 16 or username.__len__() == 0:
            raise (InvalidUsernameException(username.__len__(), 1))
        return username
    except InvalidUsernameException as e:
        if e.errors == 0:
            print("\n")
            for char in e.message:
                print("  ERROR: '{}' Not accepted.".format(chr(char)))
            print("\n  A-Z, a-z, 0-9, '-', '.', '_' is acceptable.\n")
        elif e.errors == 1:
            print("\n  ERROR: Username length must be 1-16 characters long.\n")
        elif e.errors == 2:
            print("\n  ERROR: '{}' is already taken.\n".format(e))
        return get_username()

def name_check1(name):
    abc_count = 0
    misc_count = 0
    char_val = [ord(c) for c in name]
    for char in char_val:
        if char <= 64:
            misc_count += 1
        elif 65 <= char <= 90:
            abc_count += 1
        elif 91 <= char <= 96:
            misc_count += 1
        elif 97 <= char <= 122:
            abc_count += 1
        else:
            misc_count += 1
    if misc_count > 0:
        raise (InvalidUsernameException("\n  ERROR: Invalid characters used. Use (a-b, A-B)\n", 0))
    elif name.__len__() >= 16 or name.__len__() < 1:
        raise (InvalidUsernameException("\n  ERROR: Invalid name length. (1-16)\n", 1))

def name_check2(name):
    abc_count = 0
    misc_count = 0
    char_val = [ord(c) for c in name]
    for char in char_val:
        if char == 32:
            abc_count += 1
        elif char >= 48 and char <= 57:
            abc_count += 1
        elif char <= 64:
            misc_count += 1
        elif 65 <= char <= 90:
            abc_count += 1
        elif 91 <= char <= 96:
            misc_count += 1
        elif 97 <= char <= 122:
            abc_count += 1
        else:
            misc_count += 1
    if misc_count > 0:
        raise (InvalidUsernameException("\n  ERROR: Invalid characters used. Use (a-b, A-B, 0-9, ' ')\n", 0))
    elif name.__len__() >= 16 or name.__len__() < 1:
        raise (InvalidUsernameException("\n  ERROR: Invalid name length. (1-16)\n", 1))

def get_name(prompt, set=1):
    set_switch = {
        1 : name_check1,
        2 : name_check2
    }
    try:
        name = input('{} Name: '.format(prompt))
        set_switch[set](name)
        return name
    except InvalidUsernameException as e:
        print(e)
        return get_name(prompt, set=set)

def password_check(password):
    char_val = [ord(c) for c in password]
    abc_count = 0
    ABC_count = 0
    spc_count = 0
    dig_count = 0
    invalid = list()
    for char in char_val:
        if char >= 33 and char <= 47:
            spc_count += 1
        elif char >= 48 and char <= 57:
            dig_count += 1
        elif char >= 58 and char <= 64:
            spc_count += 1
        elif char >= 65 and char <= 90:
            ABC_count += 1
        elif char >= 91 and char <= 96:
            spc_count +=1
        elif char >= 97 and char <= 122:
            abc_count += 1
        elif char >= 123 and char <= 126:
            spc_count += 1
        else:
            invalid.append(chr(char))

    if invalid != []:
        raise (InvalidUsernameException("\n  ERROR: Illegal characters used.\n", 3))
    if abc_count < 1 or ABC_count < 1 or spc_count < 1 or dig_count < 1:
        raise (InvalidUsernameException("\n  ERROR: Must include at least one of each: lowercase letter, uppercase letter, number, and special character.\n", 4))

def get_password():
    try:
        password = getpass.getpass()
        password_check(password)
        if password.__len__() < 9 or password.__len__() > 60:
            raise (InvalidUsernameException("\n  ERROR: Password length. (Must be at least 9-60 characters long)\n",1))
        confirm_passsword = getpass.getpass("Confirm Password: ")
        if password != confirm_passsword:
            raise (InvalidUsernameException("\n  ERROR: Passwords do not match.\n", 2))
        return password
    except InvalidUsernameException as e:
        print(e)
        return get_password()

class InvalidUsernameException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
        self.message = message