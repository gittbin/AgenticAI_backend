# # backend/check_db_location.py
# from pymongo import MongoClient
# import datetime

# # SAO CHÉP Y HỆT DÒNG MONGO_URI TỪ FILE database.py CỦA BẠN VÀO ĐÂY
# # Đây là bước quan trọng nhất để đảm bảo chúng ta đang kiểm tra đúng chỗ.
# MONGO_URI = "mongodb+srv://gittbin:tranledung@cluster0.j8r21fd.mongodb.net/Summer_Project?retryWrites=true&w=majority&appName=Cluster0"

# try:
#     client = MongoClient(MONGO_URI)
    
#     # Lấy database mặc định mà Connection String đang trỏ tới
#     # Nếu URI của bạn có /ten_db thì nó sẽ lấy ten_db, nếu không nó sẽ lấy 'test'
#     db = client.get_database()

#     print("✅ Kết nối thành công!")
#     print("--------------------------------------------------")
#     print(f"👉 Tên Database mà code đang kết nối tới là: '{db.name}'")
#     print("--------------------------------------------------")

#     print("\nCác collection hiện có trong database này:")
#     collection_names = db.list_collection_names()
#     if not collection_names:
#         print("(Chưa có collection nào)")
#     else:
#         for name in collection_names:
#             print(f"- {name}")

#     # Ghi một "dấu vết" duy nhất vào database này để bạn có thể tìm thấy
#     marker_collection = db["debug_markers"]
#     marker_id = marker_collection.insert_one({
#         "message": "Đây là dấu vết từ script chẩn đoán.",
#         "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
#     }).inserted_id

#     print(f"\n✅ Đã chèn một 'dấu vết' vào collection 'debug_markers' với ID: {marker_id}")
    
#     print("\n>>> HƯỚNG DẪN TIẾP THEO <<<")
#     print("1. Đọc kỹ tên Database được in ra ở trên.")
#     print("2. Lên giao diện web MongoDB Atlas, nhấn 'Browse Collections'.")
#     print("3. Tìm xem có Database nào có tên trùng khớp không.")
#     print("4. Nếu có, hãy bấm vào nó và bạn sẽ thấy collection 'debug_markers' cùng với 'users' và 'chat_histories'.")

# except Exception as e:
#     print(f"❌ Đã xảy ra lỗi: {e}")
# finally:
#     if 'client' in locals():
#         client.close()









# # backend/test_env.py
# import os
# from dotenv import load_dotenv

# print("Đang thử tải các biến từ file .env...")

# # load_dotenv() sẽ tìm file .env trong thư mục hiện tại
# is_loaded = load_dotenv()

# if is_loaded:
#     print("✅ File .env đã được tìm thấy và tải thành công!")
# else:
#     print("❌ CẢNH BÁO: Không tìm thấy file .env trong thư mục này!")

# print("\nKiểm tra các biến môi trường:")

# google_key = os.getenv("GOOGLE_API_KEY")
# langchain_key = os.getenv("LANGCHAIN_API_KEY")

# print(f"  - GOOGLE_API_KEY: {'Đã tìm thấy' if google_key else 'KHÔNG TÌM THẤY'}")
# print(f"  - LANGCHAIN_API_KEY: {'Đã tìm thấy' if langchain_key else 'KHÔNG TÌM THẤY'}")

# if langchain_key:
#     print("\n>>> Mọi thứ có vẻ ổn. Vấn đề có thể nằm ở cách Uvicorn khởi động.")
# else:
#     print("\n>>> LỖI: Python không đọc được LANGCHAIN_API_KEY từ file .env. Vui lòng kiểm tra lại Bước 1 và Bước 2 ở trên.")













# backend/run.py

import uvicorn
from dotenv import load_dotenv
import os

def main():
    """
    Điểm khởi đầu để chạy ứng dụng FastAPI.
    Hàm này đảm bảo các biến môi trường được tải TRƯỚC KHI
    Uvicorn import và chạy ứng dụng 'main:app'.
    """
    print(">>> Đang tải các biến môi trường từ file .env...")
    load_dotenv()
    
    # In ra để xác nhận
    print(f"LANGCHAIN_API_KEY được tìm thấy: {'Có' if os.getenv('LANGCHAIN_API_KEY') else 'Không'}")
    
    print(">>> Bắt đầu khởi chạy server Uvicorn...")
    uvicorn.run(
        "main:app",  # Đường dẫn đến ứng dụng FastAPI của bạn
        host="127.0.0.1",
        port=8000,
        reload=True   # Bật chế độ reload
    )

if __name__ == "__main__":
    main()