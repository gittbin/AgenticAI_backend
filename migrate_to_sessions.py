# migrate_to_sessions.py
from pymongo import MongoClient, DESCENDING, ASCENDING
from datetime import datetime, timezone

# --- THAY ĐỔI CÁC THÔNG TIN NÀY CHO PHÙ HỢP VỚI BẠN ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ten_database_cua_ban"
# ----------------------------------------------------

try:
    print(">>> Đang kết nối tới MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    chat_collection = db["chat_history"]
    session_collection = db["sessions"]
    print(">>> Kết nối thành công!")

    # BƯỚC 1: Xóa collection sessions cũ để đảm bảo không bị trùng lặp khi chạy lại script
    print(">>> Đang xóa collection 'sessions' cũ (nếu có)...")
    session_collection.drop()
    print(">>> Đã xóa collection 'sessions' cũ.")

    # BƯỚC 2: Dùng pipeline để nhóm các tin nhắn theo session_id cũ (dạng ngày)
    print(">>> Đang tìm tất cả các session cũ...")
    pipeline = [
        {"$group": {"_id": "$session_id"}},
        {"$match": {"_id": {"$ne": None}}} # Bỏ qua các tin nhắn không có session_id
    ]
    old_session_ids = [doc["_id"] for doc in chat_collection.aggregate(pipeline)]
    
    if not old_session_ids:
        print(">>> Không tìm thấy session cũ nào để di cư.")
    else:
        print(f">>> Tìm thấy {len(old_session_ids)} session cũ. Bắt đầu quá trình di cư...")
        migrated_count = 0
        
        # BƯỚC 3: Duyệt qua từng session cũ và tạo bản ghi mới trong collection 'sessions'
        for old_id in old_session_ids:
            # Tìm tin nhắn đầu tiên và cuối cùng của session cũ này
            first_message = chat_collection.find_one({"session_id": old_id}, sort=[("timestamp", ASCENDING)])
            last_message = chat_collection.find_one({"session_id": old_id}, sort=[("timestamp", DESCENDING)])

            if not first_message:
                continue

            # Tạo bản ghi session mới
            new_session_doc = {
                "session_id": old_id, # Giữ nguyên ID cũ để link không bị gãy
                "user_id": first_message.get("username") or first_message.get("user_id"),
                "title": first_message.get("content", "Lịch sử trò chuyện")[:50], # Lấy tin nhắn đầu làm tiêu đề
                "created_at": first_message.get("timestamp", datetime.now(timezone.utc)),
                "updated_at": last_message.get("timestamp", datetime.now(timezone.utc))
            }
            
            session_collection.insert_one(new_session_doc)
            migrated_count += 1
            print(f"    Đã di cư session: {old_id} -> Tiêu đề: '{new_session_doc['title']}'")
            
        print(f"\n>>> HOÀN TẤT! Đã di cư thành công {migrated_count}/{len(old_session_ids)} sessions.")

except Exception as e:
    print(f"\nXXX Đã xảy ra lỗi: {e}")
finally:
    if 'client' in locals():
        client.close()
        print(">>> Đã đóng kết nối MongoDB.")