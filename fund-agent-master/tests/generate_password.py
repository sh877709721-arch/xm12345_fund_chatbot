import secrets
import string

def generate_password(length=32):
    """生成指定长度的密码，默认16位，包含大小写字母和数字"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    # 生成16位包含大小写字母和数字的密码
    password = generate_password()
    print(password)