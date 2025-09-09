# # backend/models.py
# from pydantic import BaseModel, Field
# from typing import Optional

# class UserBase(BaseModel):
#     username: str

# class UserCreate(UserBase):
#     password: str

# class UserInDB(UserBase):
#     hashed_password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: Optional[str] = None

# class ChatRequest(BaseModel):
#     message: str
# backend/models.py
from pydantic import BaseModel, Field
from typing import Optional

# --- Các model về User và Token (Giữ nguyên, đã rất tốt) ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Model cho Request Chat (ĐÃ SỬA LỖI) ---
class ChatRequest(BaseModel):
    message: str
    
    # <<< SỬA LỖI Ở ĐÂY
    # Thêm trường session_id để nhận ID từ frontend.
    # `Optional[str] = None` có nghĩa là trường này có thể có hoặc không,
    # và nếu không có, giá trị mặc định sẽ là None.
    # Điều này hoàn toàn khớp với logic của chúng ta:
    # - Khi bắt đầu chat mới, frontend gửi `session_id: null`.
    # - Khi tiếp tục chat cũ, frontend gửi `session_id: "một-chuỗi-uuid"`.
    session_id: Optional[str] = None