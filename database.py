# # # backend/database.py
# # from pymongo import MongoClient

# # # THAY THẾ BẰNG CONNECTION STRING CỦA BẠN
# # MONGO_URI = "mongodb+srv://gittbin:tranledung@cluster0.j8r21fd.mongodb.net/Summer_Project?retryWrites=true&w=majority&appName=Cluster0"
# # client = MongoClient(MONGO_URI)

# # # Database chính
# # db = client.learning_agent_db

# # # Các collections (tương tự như tables trong SQL)
# # user_collection = db["users"]
# # chat_history_collection = db["chat_histories"]

# # # backend/database.py (Phiên bản đã sửa lỗi)

# from pymongo import MongoClient

# # --- THAY THẾ CONNECTION STRING CỦA BẠN VÀO ĐÂY ---
# # Rất quan trọng: Hãy thêm tên database bạn muốn vào cuối URI, trước dấu '?'
# # Ví dụ: /learning_agent_db?retryWrites=true...
# MONGO_URI = "mongodb+srv://gittbin:tranledung@cluster0.j8r21fd.mongodb.net/Summer_Project?retryWrites=true&w=majority&appName=Cluster0"

# client = MongoClient(MONGO_URI)

# # Chúng ta lấy database một cách tường minh từ client
# db = client.learning_agent_db

# # ĐỊNH NGHĨA TÊN COLLECTION MỘT CÁCH NHẤT QUÁN
# # Sử dụng tên viết thường và có chữ 's' ở cuối theo quy ước
# USER_COLLECTION_NAME = "users"
# CHAT_HISTORY_COLLECTION_NAME = "chat_histories"

# # Lấy các đối tượng collection
# user_collection = db[USER_COLLECTION_NAME]
# chat_history_collection = db[CHAT_HISTORY_COLLECTION_NAME]

# print("✅ Database connection module loaded successfully.")
# print(f"   - Database: '{db.name}'")
# print(f"   - User Collection: '{USER_COLLECTION_NAME}'")
# print(f"   - Chat History Collection: '{CHAT_HISTORY_COLLECTION_NAME}'")



# file: database.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Tải các biến từ file .env (chứa MONGO_URI)
load_dotenv()

# --- CẤU HÌNH ---
# Lấy MONGO_URI từ biến môi trường để bảo mật hơn
MONGO_URI = os.getenv("MONGO_URI") 
if not MONGO_URI:
    raise ValueError("LỖI: Biến môi trường MONGO_URI chưa được thiết lập trong file .env")

# Định nghĩa tên database và các collection một cách nhất quán
DB_NAME = "learning_agent_db" # Bạn có thể thay đổi nếu muốn
USER_COLLECTION_NAME = "users"
SESSIONS_COLLECTION_NAME = "sessions"             # <<< THÊM MỚI
CHAT_HISTORY_COLLECTION_NAME = "chat_histories"   # <<< Thống nhất tên
QUIZ_COLLECTION_NAME = "quiz"
INCORRECT_ANSWERS_COLLECTION_NAME = "incorrect_answer"
# --- KHỞI TẠO KẾT NỐI ---
try:
    # Khởi tạo client kết nối tới MongoDB
    client = MongoClient(MONGO_URI)
    
    # Kiểm tra kết nối để ứng dụng dừng lại ngay nếu DB có vấn đề
    client.admin.command('ping') 
    
    # Lấy đối tượng database từ client
    db = client[DB_NAME]

    # Lấy các đối tượng collection để export và sử dụng trong toàn ứng dụng
    user_collection = db[USER_COLLECTION_NAME]
    sessions_collection = db[SESSIONS_COLLECTION_NAME]         # <<< THÊM MỚI
    chat_history_collection = db[CHAT_HISTORY_COLLECTION_NAME] # <<< Thống nhất tên
    quizzes_collection = db[QUIZ_COLLECTION_NAME]
    incorrect_answers_collection=db[INCORRECT_ANSWERS_COLLECTION_NAME]
    print("✅ Kết nối tới MongoDB thành công!")
    print(f"   - Đang sử dụng database: '{db.name}'")
    print(f"   - User Collection: '{user_collection.name}'")
    print(f"   - Sessions Collection: '{sessions_collection.name}'")
    print(f"   - Chat History Collection: '{chat_history_collection.name}'")

except ConnectionFailure as e:
    print(f"❌ LỖI NGHIÊM TRỌNG: Không thể kết nối tới MongoDB.")
    print(f"   - Vui lòng kiểm tra chuỗi MONGO_URI và đảm bảo MongoDB đang chạy.")
    print(f"   - Chi tiết lỗi: {e}")
    # Dừng ứng dụng nếu không kết nối được DB
    raise
except Exception as e:
    print(f"❌ Đã xảy ra lỗi không mong muốn khi thiết lập database: {e}")
    raise