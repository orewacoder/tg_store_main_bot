import secrets


def generate_id(length=12, prefix=''):
    lower_bound = 10 ** (length - 1)
    upper_bound = 10 ** length - 1
    return prefix + str(secrets.randbelow(upper_bound - lower_bound) + lower_bound)

