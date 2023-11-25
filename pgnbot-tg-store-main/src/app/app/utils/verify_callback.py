import base64

from OpenSSL import crypto

pub_str = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC3FT0Ym8b3myVxhQW7ESuuu6lo\n" \
          "dGAsUJs4fq+Ey//jm27jQ7HHHDmP1YJO7XE7Jf/0DTEJgcw4EZhJFVwsk6d3+4fy\nBsn0tKeyGMiaE6cVkX0cy6Y85o8z" \
          "gc/CwZKc0uw6d5siAo++xl2zl+RGMXCELQVE\nox7pp208zTvown577wIDAQAB\n-----END PUBLIC KEY-----"


def callback_handler(signature, data):

    pubkey = crypto.load_publickey(crypto.FILETYPE_PEM, pub_str)
    signature = base64.b64decode(signature)

    x509 = crypto.X509()
    x509.set_pubkey(pubkey)

    try:
        crypto.verify(x509, signature, data, 'sha256')
        return True
    except crypto.Error:
        ...
    return False
