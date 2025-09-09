# backend/config.py

# DÙNG MỘT CHUỖI BÍ MẬT MẠNH MẼ Ở ĐÂY
# Bạn có thể tạo một chuỗi ngẫu nhiên bằng cách chạy lệnh sau trong Python:
# import secrets
# secrets.token_hex(32)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Tăng thời gian hết hạn lên 60 phút