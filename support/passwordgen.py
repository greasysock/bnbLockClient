import os

def random_1():
    os.urandom(2)
    potential_char = os.urandom(1)
    potential_char_len = ord(potential_char)
    if potential_char_len >= 48 and potential_char_len <= 57:
        return potential_char.decode('ascii')
    elif potential_char_len >= 65 and potential_char_len <= 90:
        return potential_char.decode('ascii')
    elif potential_char_len >= 97 and potential_char_len <= 122:
        return potential_char.decode('ascii')
    else:
        return random_1()
def random_2():
    os.urandom(2)
    potential_char = os.urandom(1)
    potential_char_len = ord(potential_char)
    if potential_char_len >= 48 and potential_char_len <= 57:
        return potential_char.decode('ascii')
    elif potential_char_len >= 65 and potential_char_len <= 90:
        return potential_char.decode('ascii')
    else:
        return random_2()
def random_3():
    os.urandom(2)
    potential_char = os.urandom(1)
    potential_char_len = ord(potential_char)
    if potential_char_len >= 33 and potential_char_len <= 126:
        return potential_char.decode('ascii')
    else:
        return random_3()

def random_4():
    os.urandom(2)
    potential_char = os.urandom(1)
    potential_char_len = ord(potential_char)
    if 48 <= potential_char_len <= 57:
        return potential_char.decode('ascii')
    else:
        return random_4()

def random_len(length, set = 1):
    os.urandom(250)
    out_string = ""
    if set == 1:
        rand_set = random_1
    elif set == 2:
        rand_set = random_2
    elif set == 3:
        rand_set = random_3
    elif set == 4:
        rand_set = random_4
    else:
        rand_set = random_1
    for x in range(length):
        out_string = out_string + rand_set()
    return out_string
