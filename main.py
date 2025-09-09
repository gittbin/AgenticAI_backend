
# from fastapi import FastAPI, Depends, HTTPException, status
# # ... (giữ nguyên các import khác)
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# import json
# from bson import ObjectId
# import os
# from dotenv import load_dotenv

# load_dotenv()

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# # SỬA LỖI TẠI ĐÂY
# from langchain_google_genai import ChatGoogleGenerativeAI 
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain import hub
# from langchain.tools import Tool

# # --- LOGIC AGENT ---

# # 1. Khởi tạo LLM (SỬA LỖI TẠI ĐÂY)
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash-latest",
#     google_api_key=os.getenv("GOOGLE_API_KEY")
# )

# # 2. Logic của Tool (Không đổi)
# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     # ... (giữ nguyên toàn bộ code của hàm này)
#     print(f"--- LOGIC TOOL được gọi bởi user: '{username}' với câu hỏi: '{query}' ---")
#     history_cursor = chat_history_collection.find(
#         {"username": username, "role": {"$ne": "user"}}
#     ).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history:
#         return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(history)])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"

# # 3. NÂNG CẤP LỚN: SỬ DỤNG XML AGENT
# # Tạo tool với tên và mô tả bằng tiếng Việt
# tools = [
#     Tool(
#         name="tra_cuu_lich_su_hoc_tap",
#         func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#         description="Công cụ này rất hữu ích để tra cứu lịch sử trò chuyện trong quá khứ của người dùng. Sử dụng khi người dùng hỏi về các chủ đề đã học hoặc những gì đã nói trước đó."
#     )
# ]

# # Tải một prompt đã được tối ưu hóa cho XML Agent từ LangChain Hub
# # Prompt này hoạt động tốt hơn nhiều so với việc chúng ta tự viết
# prompt = hub.pull("hwchase17/xml-agent-conv")

# # Thêm các hướng dẫn bằng tiếng Việt vào prompt
# prompt.messages[0].prompt.template = "Bạn là một trợ lý học tập AI tên là 'Trí Tuệ', thân thiện, kiên nhẫn và hữu ích. Hãy luôn trả lời bằng tiếng Việt.\n\n" + prompt.messages[0].prompt.template

# # Tạo agent bằng create_xml_agent
# agent = create_xml_agent(llm, tools, prompt)

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# # ... (giữ nguyên CORS, endpoints đăng ký, đăng nhập)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # ... (giữ nguyên các endpoint /auth/register và /auth/login)
# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}


# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
    
#     # Cập nhật lại cách tạo tool để truyền username vào
#     tools_with_context = [
#         Tool(
#             name="tra_cuu_lich_su_hoc_tap",
#             func=lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#             description="Công cụ này rất hữu ích để tra cứu lịch sử trò chuyện trong quá khứ của người dùng. Sử dụng khi người dùng hỏi về các chủ đề đã học hoặc những gì đã nói trước đó."
#         )
#     ]
    
#     # Tạo executor với tool đã có context
#     agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True)

#     user_message_doc = {
#         "username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)
#     }
#     chat_history_collection.insert_one(user_message_doc)

#     try:
#         # Lấy lịch sử chat để đưa vào agent
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history = []
#         for doc in reversed(list(history_cursor)):
#             if doc['role'] == 'user':
#                 chat_history.append({"role": "user", "content": doc['content']})
#             else:
#                 chat_history.append({"role": "assistant", "content": doc['content']})

#         response = agent_executor.invoke({"input": request.message, "chat_history": chat_history})
#         ai_response_content = response["output"]
#     except Exception as e:
#         print(f"Lỗi khi thực thi Agent: {e}")
#         ai_response_content = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Bạn có thể thử lại không?"

#     ai_message_doc = {
#         "username": username, "role": "assistant", "content": ai_response_content, "timestamp": datetime.now(timezone.utc)
#     }
#     chat_history_collection.insert_one(ai_message_doc)
    
#     return {
#         "userMessage": {"sender": "user", "message": user_message_doc["content"]},
#         "aiMessage": {"sender": "ai", "message": ai_message_doc["content"]}
#     }
# # ... (giữ nguyên 2 endpoint /api/history/sessions và /api/history/messages/{session_date})
# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list

# import os
# from dotenv import load_dotenv

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded:
#     print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else:
#     print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# # Kiểm tra các biến quan trọng và báo lỗi nếu thiếu
# LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if not LANGCHAIN_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy LANGCHAIN_API_KEY trong môi trường. Vui lòng kiểm tra file .env.")
# if not GOOGLE_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy GOOGLE_API_KEY trong môi trường. Vui lòng kiểm tra file .env.")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# # --- BƯỚC 2: IMPORT CÁC THƯ VIỆN CÒN LẠI SAU KHI .ENV ĐÃ ĐƯỢC TẢI ---
# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# import json
# from bson import ObjectId

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain import hub
# from langchain.tools import Tool

# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)

# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL được gọi bởi user: '{username}' với câu hỏi: '{query}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(history)])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"

# from langchain.prompts import PromptTemplate

# tools = [
#     Tool(
#         name="tra_cuu_lich_su_hoc_tap",
#         func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#         description="Công cụ để tra cứu các đoạn hội thoại học tập gần đây nhất của người dùng"
#     )
# ]

# # Prompt phải có {tools}, {input}, {agent_scratchpad}
# prompt_template = """
# Bạn là một trợ lý học tập AI tên là 'Trí Tuệ', thân thiện, kiên nhẫn và hữu ích.
# Bạn có thể sử dụng các công cụ sau đây để hỗ trợ người dùng:

# {tools}

# Người dùng nói: {input}

# # Ghi chú suy luận (không xóa, để agent theo dõi tiến trình):
# {agent_scratchpad}
# """

# prompt = PromptTemplate.from_template(prompt_template)

# agent = create_xml_agent(llm, tools, prompt)

# print(">>> [main.py] Agent đã khởi tạo thành công.")


# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# # ... (giữ nguyên CORS, endpoints đăng ký, đăng nhập)
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     # ... (giữ nguyên code)
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     # ... (giữ nguyên code)
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     tools_with_context = [Tool(name="tra_cuu_lich_su_hoc_tap", func=lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username), description="...")]
#     agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True)
#     user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#     chat_history_collection.insert_one(user_message_doc)
#     try:
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history = []
#         for doc in reversed(list(history_cursor)):
#             role = "human" if doc['role'] == 'user' else "ai"
#             chat_history.append({"role": role, "content": doc['content']})
#         response = agent_executor.invoke({"input": request.message, "chat_history": chat_history})
#         ai_response_content = response["output"]
#     except Exception as e:
#         print(f"Lỗi khi thực thi Agent: {e}")
#         ai_response_content = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Bạn có thể thử lại không?"
#     ai_message_doc = {"username": username, "role": "assistant", "content": ai_response_content, "timestamp": datetime.now(timezone.utc)}
#     chat_history_collection.insert_one(ai_message_doc)
#     return {"userMessage": {"sender": "user", "message": user_message_doc["content"]}, "aiMessage": {"sender": "ai", "message": ai_message_doc["content"]}}

# # ... (giữ nguyên 2 endpoint /api/history/sessions và /api/history/messages/{session_date})
# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list










# # backend/main.py

# import os
# from dotenv import load_dotenv

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded:
#     print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else:
#     print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if not GOOGLE_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy GOOGLE_API_KEY trong môi trường. Vui lòng kiểm tra file .env.")

# print(">>> [main.py] Các API keys đã được tải thành công.")
# # ================== KIỂM TRA GEMINI API KEY ==================
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.callbacks import get_openai_callback

# print(">>> [main.py] Đang kiểm tra Gemini API key...")
# try:
#     llm_test = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)
#     with get_openai_callback() as cb:
#         resp = llm_test.invoke("ping")
#         print(">>> [main.py] Gemini phản hồi:", resp.content)
#         print(">>> [main.py] Token usage:", cb)  # In số tokens đã dùng
#     print(">>> [main.py] Gemini API key hợp lệ, có thể chạy.")
# except Exception as e:
#     print(">>> [main.py] LỖI: Không thể kết nối Gemini:", e)
# # ============================================================
# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# import json
# from bson import ObjectId

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun
# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)

# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL được gọi bởi user: '{username}' với câu hỏi: '{query}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(history)])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"
# search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
# tools = [
#     Tool(
#         name="tra_cuu_lich_su_tro_chuyen", # Đổi tên cho rõ ràng hơn
#         func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#         description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây."
#     ),
#     search_tool # Thêm công cụ tìm kiếm vào danh sách
# ]

# prompt_template_str = """Bạn là một trợ lý học tập AI chuyên gia tên là 'Trí Tuệ'. Luôn luôn trả lời bằng tiếng Việt.

# QUY TẮC LỰA CHỌN HÀNH ĐỘNG:
# 1. Nếu người dùng hỏi kiến thức chung, định nghĩa, hoặc thông tin mới (ví dụ: "AI là gì?", "tóm tắt về ...") → sử dụng công cụ `tim_kiem_internet`.
# 2. Nếu người dùng hỏi về các cuộc trò chuyện đã diễn ra (ví dụ: "lần trước chúng ta nói gì?", "tôi đã học gì rồi?") → sử dụng công cụ `tra_cuu_lich_su_tro_chuyen`.
# 3. Nếu người dùng chỉ chào hỏi hoặc hỏi không rõ ràng → trả lời trực tiếp, không dùng công cụ.

# Bạn có quyền truy cập vào các công cụ sau:
# {tools}

# QUY ĐỊNH ĐỊNH DẠNG:
# - Bạn CHỈ ĐƯỢC PHÉP chọn MỘT trong hai định dạng XML sau.
# - Tuyệt đối không được trả cả hai cùng lúc.
# - Các tham số trong <parameters> chỉ có duy nhất thẻ <query>.

# 1. Khi cần dùng công cụ:
# <tool>
#   <tool_name>tên_công_cụ</tool_name>
#   <parameters>
#     <query>nội_dung_cần_xử_lý</query>
#   </parameters>
# </tool>

# 2. Khi trả lời trực tiếp (chào hỏi, làm rõ):
# <final_answer>câu_trả_lời_của_bạn</final_answer>

# Dữ liệu hỗ trợ bạn:
# <history>
# {chat_history}
# </history>

# Câu hỏi mới của người dùng: {input}

# {agent_scratchpad}
# """
# prompt = PromptTemplate.from_template(prompt_template_str)
# agent = create_xml_agent(llm, tools, prompt)
# print(">>> [main.py] Agent đã khởi tạo thành công.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     tools_with_context = [
#         Tool(name="tra_cuu_lich_su_tro_chuyen", 
#              func=lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username), 
#              description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây."
#              ),
#         search_tool
#              ]
#     agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True)
#     user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#     chat_history_collection.insert_one(user_message_doc)
#     try:
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
#         response = agent_executor.invoke({"input": request.message, "chat_history": chat_history_str})
#         ai_response_content = response["output"]
#     except Exception as e:
#         print(f"Lỗi khi thực thi Agent: {e}")
#         ai_response_content = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Bạn có thể thử lại không?"
#     ai_message_doc = {"username": username, "role": "assistant", "content": ai_response_content, "timestamp": datetime.now(timezone.utc)}
#     chat_history_collection.insert_one(ai_message_doc)
#     return {"userMessage": {"sender": "user", "message": user_message_doc["content"]}, "aiMessage": {"sender": "ai", "message": ai_message_doc["content"]}}

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list





















# import os
# from dotenv import load_dotenv

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# # ... (giữ nguyên phần tải và kiểm tra .env)
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# # Lấy key của OpenRouter
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY trong môi trường.")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# # ... (giữ nguyên các import khác)
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# import json
# from bson import ObjectId
# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection
# from starlette.responses import StreamingResponse

# # --- THAY ĐỔI 1: IMPORT TỪ LANGCHAIN_COMMUNITY ---
# from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun


# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")

# # --- THAY ĐỔI 2: KHỞI TẠO LLM BẰNG ChatOpenRouter ---
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")  # OpenRouter key
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"  # OpenRouter endpoint

# llm = ChatOpenAI(
#     model="anthropic/claude-3-haiku",  # hoặc gemini, gpt-3.5-turbo...
#     temperature=0.7,
# )
# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL được gọi bởi user: '{username}' với câu hỏi: '{query}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(history)])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"
# def tao_quiz_logic(topic: str) -> str:
#     """Tạo ra một bài quiz nhỏ về một chủ đề cụ thể."""
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' ---")
    
#     prompt = f"""
#     Tạo một bài kiểm tra trắc nghiệm gồm 3 câu hỏi về chủ đề '{topic}'.
#     YÊU CẦU ĐỊNH DẠNG: Trả về dưới dạng một chuỗi JSON hợp lệ.
#     Mỗi câu hỏi phải có cấu trúc: {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A" }}
    
#     Ví dụ JSON:
#     [
#       {{
#         "question": "Python là ngôn ngữ lập trình gì?",
#         "options": ["Biên dịch", "Thông dịch", "Hợp ngữ", "Nhị phân"],
#         "answer": "B"
#       }}
#     ]
    
#     JSON của bạn:
#     """
    
#     quiz_response = llm.invoke(prompt)
#     quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)

#     # Làm sạch output của LLM để đảm bảo nó là JSON
#     try:
#         # Tìm vị trí bắt đầu và kết thúc của mảng JSON
#         start_index = quiz_json_str.find('[')
#         end_index = quiz_json_str.rfind(']')
#         if start_index != -1 and end_index != -1:
#             clean_json = quiz_json_str[start_index : end_index + 1]
#             # Kiểm tra xem có phải JSON hợp lệ không
#             json.loads(clean_json)
#             return clean_json
#         else:
#             return '{ "error": "Không thể tạo quiz theo đúng định dạng." }'
#     except Exception as e:
#         print(f"Lỗi khi parse JSON quiz: {e}")
#         return '{ "error": "Lỗi khi tạo quiz." }'

# # Thêm tool mới vào danh sách
# quiz_tool = Tool(
#     name="tao_quiz",
#     func=tao_quiz_logic,
#     description="Rất hữu ích khi người dùng muốn kiểm tra kiến thức về một chủ đề cụ thể. Đầu vào là tên của chủ đề."
# )
# search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
# tools = [
#     Tool(
#         name="tra_cuu_lich_su_tro_chuyen", # Đổi tên cho rõ ràng hơn
#         func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#         description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây."
#     ),
#     search_tool,
#     quiz_tool  # Thêm công cụ tìm kiếm vào danh sách
# ]

# prompt_template_str = """Bạn là một trợ lý học tập AI chuyên gia tên là 'Trí Tuệ'. Luôn luôn trả lời bằng tiếng Việt.

# **QUY TẮC LỰA CHỌN HÀNH ĐỘNG:**
# 1.  **Đối với câu hỏi kiến thức chung, định nghĩa, hoặc thông tin mới (ví dụ: 'AI là gì?', 'tóm tắt về [chủ đề X]'):** BẠN PHẢI sử dụng công cụ `tim_kiem_internet`.
# 2.  **Đối với câu hỏi về các cuộc trò chuyện đã diễn ra (ví dụ: 'lần trước chúng ta nói gì?', 'tôi đã học gì rồi?'):** BẠN PHẢI sử dụng công cụ `tra_cuu_lich_su_tro_chuyen`.
# 3.  **Khi người dùng yêu cầu một bài QUIZ, KIỂM TRA, hay CÂU HỎI ÔN TẬP:** BẠN PHẢI sử dụng công cụ `tao_quiz`.
# 4.  **Đối với các câu hỏi chào hỏi hoặc không rõ ràng:** Hãy trả lời trực tiếp mà không dùng công cụ.
# **LUẬT NGHIÊM NGẶT**
# - Mỗi lần trả lời, chỉ chọn MỘT trong hai định dạng: <tool> hoặc <final_answer>.
# - Không bao giờ vừa dùng <tool> vừa trả lời trực tiếp ngoài XML.
# - Nếu dùng <tool>, output PHẢI chỉ chứa một khối <tool> duy nhất, không có chữ nào khác.
# - Nếu dùng <final_answer>, output PHẢI chỉ chứa một khối <final_answer> duy nhất.

# Bạn có quyền truy cập vào các công cụ sau:
# {tools}

# QUY ĐỊNH ĐỊNH DẠNG:
# - Bạn CHỈ ĐƯỢC PHÉP chọn MỘT trong hai định dạng XML sau.
# - Tuyệt đối không được trả cả hai cùng lúc.
# - Các tham số trong <parameters> chỉ có duy nhất thẻ <query>.

# 1. Khi cần dùng công cụ:
# <tool>
#   <tool_name>CHỈ ĐƯỢC chọn một trong: tim_kiem_internet, tra_cuu_lich_su_tro_chuyen, tao_quiz</tool_name>
#   <parameters>
#     <query>nội_dung_cần_xử_lý</query>
#   </parameters>
# </tool>

# 2. Khi trả lời trực tiếp (chào hỏi, làm rõ):
# <final_answer>câu_trả_lời_của_bạn</final_answer>

# Dữ liệu hỗ trợ bạn:
# <history>
# {chat_history}
# </history>

# Câu hỏi mới của người dùng: {input}

# {agent_scratchpad}
# """
# prompt = PromptTemplate.from_template(prompt_template_str)
# agent = create_xml_agent(llm, tools, prompt)
# print(">>> [main.py] Agent đã khởi tạo thành công.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}
# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
    
#     # Định nghĩa một hàm generator bất đồng bộ để tạo ra dòng dữ liệu
#     async def stream_generator():
#         # --- Phần setup logic Agent (không thay đổi) ---
#         tools_with_context = [
#             Tool(
#                 name="tra_cuu_lich_su_tro_chuyen",
#                 func=lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username),
#                 description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây."
#             ),
#             search_tool,
#             quiz_tool  
#         ]
#         agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True, max_iterations=5)
        
#         # --- Phần xử lý dữ liệu (không thay đổi) ---
#         # Lưu tin nhắn của người dùng trước
#         user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#         chat_history_collection.insert_one(user_message_doc)
        
#         # Lấy lịch sử để đưa vào Agent
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
        
#         # --- Phần streaming cốt lõi ---
#         full_response = ""
#         try:
#             # Sử dụng astream_events để nhận các chunk dữ liệu một cách có cấu trúc
#             # Đây là phương pháp streaming hiện đại nhất của LangChain
#             async for event in agent_executor.astream_events(
#                 {"input": request.message, "chat_history": chat_history_str},
#                 version="v1"
#             ):
#                 kind = event["event"]
#                 # Lắng nghe sự kiện khi LLM đang stream các chunk văn bản
#                 if kind == "on_llm_stream":
#                     token = event["data"]["chunk"]
#                     if isinstance(token, str):
#                         full_response += token
#                         yield token # Gửi (yield) từng chunk văn bản về cho frontend
#                         await asyncio.sleep(0.01) # Một khoảng dừng nhỏ để frontend có thời gian render
                
#                 # (Tùy chọn) Lắng nghe sự kiện khi Tool kết thúc để hiển thị cho người dùng biết
#                 elif kind == "on_tool_end":
#                     tool_output = f'\n\n<observation>\nĐã tìm thấy: {event["data"]["output"][:100]}...\n</observation>\n\n'
#                     # yield tool_output # Bạn có thể bỏ comment dòng này nếu muốn frontend hiển thị cả kết quả của tool
        
#         except Exception as e:
#             print(f"Lỗi khi streaming Agent: {e}")
#             full_response = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Bạn có thể thử lại không?"
#             yield full_response

#         # --- Lưu toàn bộ câu trả lời vào DB sau khi stream kết thúc ---
#         ai_message_doc = {
#             "username": username,
#             "role": "assistant",
#             "content": full_response, # Lưu toàn bộ câu trả lời đã được ghép lại
#             "timestamp": datetime.now(timezone.utc)
#         }
#         chat_history_collection.insert_one(ai_message_doc)

#     # Trả về một StreamingResponse, trỏ đến hàm generator ở trên
#     return StreamingResponse(stream_generator(), media_type="text/event-stream")

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list



















# # # backend/main.py (Phiên bản cuối cùng v12 - Quay lại phương pháp ChatOpenAI ổn định)

# import os
# from dotenv import load_dotenv
# import asyncio
# import json

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# from fastapi.responses import StreamingResponse
# from bson import ObjectId

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# # SỬA LỖI IMPORT Ở ĐÂY
# from langchain_openai import ChatOpenAI 
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun

# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")

# # SỬA LỖI KHỞI TẠO LLM Ở ĐÂY: Dùng "cầu nối" ChatOpenAI
# # "Đánh lừa" ChatOpenAI để nó trỏ đến endpoint và dùng key của OpenRouter
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# # Thêm header cần thiết cho OpenRouter
# os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'


# llm = ChatOpenAI(
#     model="anthropic/claude-3-haiku", # Hoặc bất kỳ model nào trên OpenRouter
#     temperature=0.7,
#     streaming=True # Quan trọng để giữ hiệu ứng gõ chữ
# )

# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL 'Lịch sử' được gọi bởi user: '{username}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(list(history_cursor))])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"

# def tao_quiz_logic(topic: str) -> str:
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' ---")
#     prompt_str = f"""
#     Tạo một bài kiểm tra trắc nghiệm gồm 3 câu hỏi về chủ đề '{topic}'.
#     YÊU CẦU ĐỊNH DẠNG: Trả về dưới dạng một chuỗi JSON hợp lệ, không có ký tự markdown nào khác.
#     Mỗi câu hỏi phải có cấu trúc: {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A" }}
#     JSON của bạn:
#     """
#     quiz_response = llm.invoke(prompt_str)
#     quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
#     try:
#         start_index = quiz_json_str.find('[')
#         end_index = quiz_json_str.rfind(']')
#         if start_index != -1 and end_index != -1:
#             clean_json = quiz_json_str[start_index : end_index + 1]
#             json.loads(clean_json)
#             return clean_json
#         else: return '{ "error": "Không thể tạo quiz theo đúng định dạng." }'
#     except Exception as e: return f'{{ "error": "Lỗi khi tạo quiz: {e}" }}'

# search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
# quiz_tool = Tool(name="tao_quiz", func=tao_quiz_logic, description="Rất hữu ích khi người dùng muốn kiểm tra kiến thức về một chủ đề cụ thể. Đầu vào là tên của chủ đề.")
# history_tool = Tool(name="tra_cuu_lich_su_tro_chuyen", func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username), description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây.")

# tools = [history_tool, search_tool, quiz_tool]

# prompt_template_str = """Bạn là một trợ lý học tập AI chuyên gia tên là 'Trí Tuệ'. Luôn luôn trả lời bằng tiếng Việt.

# **QUY TẮC LỰA CHỌN HÀNH ĐỘNG:**
# 1.  **Đối với câu hỏi kiến thức chung, định nghĩa, hoặc thông tin mới (ví dụ: 'AI là gì?', 'tóm tắt về [chủ đề X]'):** BẠN PHẢI sử dụng công cụ `tim_kiem_internet`.
# 2.  **Đối với câu hỏi về các cuộc trò chuyện đã diễn ra (ví dụ: 'lần trước chúng ta nói gì?', 'tôi đã học gì rồi?'):** BẠN PHẢI sử dụng công cụ `tra_cuu_lich_su_tro_chuyen`.
# 3.  **Khi người dùng yêu cầu một bài QUIZ, KIỂM TRA, hay CÂU HỎI ÔN TẬP:** BẠN PHẢI sử dụng công cụ `tao_quiz`.
# 4.  **Đối với các câu hỏi chào hỏi hoặc không rõ ràng:** Hãy trả lời trực tiếp mà không dùng công cụ.

# Bạn có quyền truy cập vào các công cụ sau:
# {tools}

# Bạn PHẢI sử dụng một trong hai định dạng XML sau để trả lời.

# **1. Khi cần dùng công cụ:**
# <tool>
# <tool_name>tên_công_cụ_bạn_chọn</tool_name>
# <parameters>
# <query>chủ_đề_cần_tìm_kiếm_hoặc_câu_hỏi_về_lịch_sử</query>
# </parameters>
# </tool>

# **2. Khi trả lời trực tiếp (chào hỏi, làm rõ):**
# <final_answer>câu_trả_lời_của_bạn</final_answer>

# Lịch sử trò chuyện gần đây:
# <history>
# {chat_history}
# </history>

# Câu hỏi mới của người dùng: {input}

# Bây giờ, hãy phân tích câu hỏi dựa trên QUY TẮC LỰA CHỌN HÀNH ĐỘNG và đưa ra câu trả lời theo đúng định dạng XML.
# {agent_scratchpad}
# """

# prompt = PromptTemplate.from_template(prompt_template_str)
# agent = create_xml_agent(llm, tools, prompt)
# print(">>> [main.py] Agent đã khởi tạo thành công.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/api/greeting")
# async def get_personalized_greeting(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     last_message = chat_history_collection.find_one({"username": username, "role": "user"}, sort=[("timestamp", -1)])
#     last_topic = last_message["content"] if last_message else None
    
#     prompt_str = f"""Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.
# - Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.
# - Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.
# Lời chào của bạn:"""
    
#     greeting_response = llm.invoke(prompt_str)
#     greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
#     return {"message": greeting_text.strip()}

# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     async def stream_generator():
#         tools_with_context = [history_tool, search_tool, quiz_tool]
#         tools_with_context[0].func = lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username)
#         agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True, max_iterations=5)
        
#         user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#         chat_history_collection.insert_one(user_message_doc)
        
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
        
#         full_response = ""
#         try:
#             async for chunk in agent_executor.astream(
#                 {"input": request.message, "chat_history": chat_history_str}
#             ):
#                 if "output" in chunk:
#                     token = chunk["output"]
#                     full_response += token
#                     yield token
#                     await asyncio.sleep(0.01)
#         except Exception as e:
#             print(f"Lỗi khi streaming Agent: {e}")
#             full_response = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ."
#             yield full_response

#         if full_response:
#              ai_message_doc = {"username": username, "role": "assistant", "content": full_response.strip(), "timestamp": datetime.now(timezone.utc)}
#              chat_history_collection.insert_one(ai_message_doc)

#     return StreamingResponse(stream_generator(), media_type="text/event-stream")

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list



# # backend/main.py (Phiên bản cuối cùng v13 - Siêu ổn định)

# import os
# from dotenv import load_dotenv
# import asyncio
# import json

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# from fastapi.responses import StreamingResponse
# from bson import ObjectId

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun

# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")

# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'

# llm = ChatOpenAI(
#     model="anthropic/claude-3-haiku",
#     temperature=0.7,
#     streaming=True
# )

# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL 'Lịch sử' được gọi bởi user: '{username}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(list(history_cursor))])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"

# def tao_quiz_logic(topic: str) -> str:
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' ---")
#     prompt_str = f"""
#     Tạo một bài kiểm tra trắc nghiệm gồm 3 câu hỏi về chủ đề '{topic}'.
#     YÊU CẦU ĐỊNH DẠNG: Trả về dưới dạng một chuỗi JSON hợp lệ, không có ký tự markdown nào khác.
#     Mỗi câu hỏi phải có cấu trúc: {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A" }}
#     JSON của bạn:
#     """
#     quiz_response = llm.invoke(prompt_str)
#     quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
#     try:
#         start_index = quiz_json_str.find('[')
#         end_index = quiz_json_str.rfind(']')
#         if start_index != -1 and end_index != -1:
#             clean_json = quiz_json_str[start_index : end_index + 1]
#             json.loads(clean_json)
#             return clean_json
#         else: return '{ "error": "Không thể tạo quiz theo đúng định dạng." }'
#     except Exception as e: return f'{{ "error": "Lỗi khi tạo quiz: {e}" }}'

# search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
# quiz_tool = Tool(name="tao_quiz", func=tao_quiz_logic, description="Rất hữu ích khi người dùng muốn kiểm tra kiến thức về một chủ đề cụ thể. Đầu vào là tên của chủ đề.")
# history_tool = Tool(name="tra_cuu_lich_su_tro_chuyen", func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username), description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây.")

# tools = [history_tool, search_tool, quiz_tool]

# # NÂNG CẤP PROMPT LẦN CUỐI
# prompt_template_str = """Bạn là một trợ lý học tập AI chuyên gia tên là 'Trí Tuệ'. Luôn luôn trả lời bằng tiếng Việt.

# **QUY TẮC TỐI THƯỢNG:**
# 1.  **Luôn phân tích câu hỏi của người dùng trước.**
# 2.  **Ưu tiên trả lời trực tiếp** nếu đó là câu chào hỏi hoặc câu hỏi không rõ ràng.
# 3.  **Nếu là câu hỏi kiến thức chung**, BẮT BUỘC dùng công cụ `tim_kiem_internet`.
# 4.  **Nếu là câu hỏi về lịch sử trò chuyện**, BẮT BUỘC dùng công cụ `tra_cuu_lich_su_tro_chuyen`.
# 5.  **Nếu người dùng yêu cầu quiz/kiểm tra**, BẮT BUỘC dùng công cụ `tao_quiz`.

# **Bạn có quyền truy cập vào các công cụ sau:**
# {tools}

# **ĐỊNH DẠNG OUTPUT (CỰC KỲ QUAN TRỌNG):**
# -   Bạn CHỈ ĐƯỢC PHÉP tạo ra **MỘT** khối XML duy nhất trong mỗi lượt trả lời.
# -   **KHÔNG BAO GIỜ** viết bất kỳ văn bản nào bên ngoài khối XML.

# **1. Định dạng dùng công cụ:**
# <tool>
# <tool_name>tên_công_cụ</tool_name>
# <parameters>
# <query>đầu_vào_cho_công_cụ</query>
# </parameters>
# </tool>

# **2. Định dạng trả lời trực tiếp:**
# <final_answer>câu_trả_lời_của_bạn</final_answer>

# ---
# **DỮ LIỆU HIỆN CÓ**

# Lịch sử trò chuyện gần đây:
# <history>
# {chat_history}
# </history>

# Câu hỏi mới của người dùng: {input}

# ---
# **BẮT ĐẦU SUY NGHĨ**
# {agent_scratchpad}
# """

# prompt = PromptTemplate.from_template(prompt_template_str)
# agent = create_xml_agent(llm, tools, prompt)
# print(">>> [main.py] Agent đã khởi tạo thành công.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate): #...
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()): #...
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/api/greeting")
# async def get_personalized_greeting(current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     last_message = chat_history_collection.find_one({"username": username, "role": "user"}, sort=[("timestamp", -1)])
#     last_topic = last_message["content"] if last_message else None
#     prompt_str = f"""Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.
# - Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.
# - Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.
# Lời chào của bạn:"""
#     greeting_response = llm.invoke(prompt_str)
#     greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
#     return {"message": greeting_text.strip()}

# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     async def stream_generator():
#         tools_with_context = [history_tool, search_tool, quiz_tool]
#         tools_with_context[0].func = lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username)
#         # THÊM `return_intermediate_steps=True` ĐỂ GỠ LỖI
#         agent_executor = AgentExecutor(agent=agent, tools=tools_with_context, verbose=True, handle_parsing_errors=True, max_iterations=5, return_intermediate_steps=True)
        
#         user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#         chat_history_collection.insert_one(user_message_doc)
        
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
        
#         full_response = ""
#         try:
#             async for chunk in agent_executor.astream(
#                 {"input": request.message, "chat_history": chat_history_str}
#             ):
#                 if "output" in chunk:
#                     token = chunk["output"]
#                     full_response += token
#                     yield token
#                     await asyncio.sleep(0.01)
#                 # In ra các bước trung gian để gỡ lỗi
#                 if "intermediate_steps" in chunk:
#                     print("--- INTERMEDIATE STEPS ---")
#                     print(chunk["intermediate_steps"])
#         except Exception as e:
#             print(f"Lỗi khi streaming Agent: {e}")
#             full_response = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Có vẻ như có chút nhầm lẫn, bạn có thể thử lại không?"
#             yield full_response

#         if full_response:
#              ai_message_doc = {"username": username, "role": "assistant", "content": full_response.strip(), "timestamp": datetime.now(timezone.utc)}
#              chat_history_collection.insert_one(ai_message_doc)

#     return StreamingResponse(stream_generator(), media_type="text/event-stream")

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list










# import os
# from dotenv import load_dotenv
# import asyncio
# import json
# import re # Thêm import cho Regular Expression

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# from fastapi.responses import StreamingResponse
# from bson import ObjectId

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, chat_history_collection

# from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun

# # --- LOGIC AGENT ---
# print(">>> [main.py] Đang khởi tạo Agent...")

# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'

# llm = ChatOpenAI(
#     model="anthropic/claude-3-haiku",
#     temperature=0.7,
#     streaming=True
# )

# def tra_cuu_lich_su_hoc_tap_logic(query: str, username: str) -> str:
#     print(f"--- LOGIC TOOL 'Lịch sử' được gọi bởi user: '{username}' ---")
#     history_cursor = chat_history_collection.find({"username": username, "role": {"$ne": "user"}}).sort("timestamp", -1).limit(5)
#     history = list(history_cursor)
#     if not history: return "Không tìm thấy lịch sử trò chuyện nào trước đó."
#     formatted_history = "\n".join([f"- {item['content']}" for item in reversed(list(history_cursor))])
#     return f"Đây là một vài đoạn hội thoại gần đây nhất:\n{formatted_history}"

# def tao_quiz_logic(topic: str) -> str:
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' ---")
#     prompt_str = f"""
#     Tạo một bài kiểm tra trắc nghiệm gồm 3 câu hỏi về chủ đề '{topic}'.
#     YÊU CẦU ĐỊNH DẠNG: Trả về dưới dạng một chuỗi JSON hợp lệ, không có ký tự markdown nào khác.
#     Mỗi câu hỏi phải có cấu trúc: {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A" }}
#     JSON của bạn:
#     """
#     quiz_response = llm.invoke(prompt_str)
#     quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
#     try:
#         start_index = quiz_json_str.find('[')
#         end_index = quiz_json_str.rfind(']')
#         if start_index != -1 and end_index != -1:
#             clean_json = quiz_json_str[start_index : end_index + 1]
#             json.loads(clean_json)
#             return clean_json
#         else: return '{ "error": "Không thể tạo quiz theo đúng định dạng." }'
#     except Exception as e: return f'{{ "error": "Lỗi khi tạo quiz: {e}" }}'

# search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
# quiz_tool = Tool(name="tao_quiz", func=tao_quiz_logic, description="Rất hữu ích khi người dùng muốn kiểm tra kiến thức về một chủ đề cụ thể. Đầu vào là tên của chủ đề.")
# history_tool = Tool(name="tra_cuu_lich_su_tro_chuyen", func=lambda query, username="": tra_cuu_lich_su_hoc_tap_logic(query=query, username=username), description="Rất hữu ích để xem lại các tin nhắn trong quá khứ. Chỉ dùng khi người dùng hỏi về những gì đã nói trước đây.")

# tools = [history_tool, search_tool, quiz_tool]

# prompt_template_str = """Bạn là một trợ lý học tập AI chuyên gia tên là 'Trí Tuệ'. Luôn luôn trả lời bằng tiếng Việt.

# **QUY TRÌNH LÀM VIỆC (BẮT BUỘC TUÂN THỦ):**

# **Bước 1: Phân tích câu hỏi của người dùng.**
# - Nếu là câu hỏi kiến thức chung → Đi đến Bước 2A.
# - Nếu là câu hỏi về lịch sử trò chuyện → Đi đến Bước 2A.
# - Nếu là yêu cầu tạo quiz → Đi đến Bước 2A.
# - Nếu là câu chào hỏi hoặc không rõ ràng → Đi đến Bước 2B.

# **Bước 2: Chọn định dạng Output.**
# Bạn CHỈ ĐƯỢC PHÉP chọn MỘT trong hai định dạng dưới đây. KHÔNG BAO GIỜ viết văn bản nào bên ngoài các thẻ XML.

# **2A. Định dạng dùng công cụ:**
# <tool>
# <tool_name>tên_công_cụ_phù_hợp</tool_name>
# <parameters>
# <query>đầu_vào_cho_công_cụ</query>
# </parameters>
# </tool>

# **2B. Định dạng trả lời trực tiếp:**
# <final_answer>câu_trả_lời_của_bạn</final_answer>

# **Bước 3: Tổng hợp câu trả lời (SAU KHI DÙNG CÔNG CỤ).**
# - Sau khi bạn nhận được kết quả từ một công cụ trong thẻ `<observation>`, lượt phản hồi TIẾP THEO của bạn BẮT BUỘC phải là Định dạng 2B, tức là một khối `<final_answer>` duy nhất để tổng hợp thông tin đó lại cho người dùng.

# ---
# **DANH SÁCH CÔNG CỤ CỦA BẠN:**
# {tools}
# ---
# **DỮ LIỆU HIỆN CÓ**
# Lịch sử trò chuyện gần đây:
# <history>
# {chat_history}
# </history>
# Câu hỏi mới của người dùng: {input}
# ---
# **BẮT ĐẦU LÀM VIỆC THEO QUY TRÌNH**
# {agent_scratchpad}
# """

# prompt = PromptTemplate.from_template(prompt_template_str)
# agent = create_xml_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=5)

# print(">>> [main.py] Agent đã khởi tạo thành công.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# @app.post("/auth/register")
# async def register_user(user: UserCreate): #...
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()): #...
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/api/greeting")
# async def get_personalized_greeting(current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     last_message = chat_history_collection.find_one({"username": username, "role": "user"}, sort=[("timestamp", -1)])
#     last_topic = last_message["content"] if last_message else None
#     prompt_str = f"""Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.
# - Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.
# - Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.
# Lời chào của bạn:"""
#     greeting_response = llm.invoke(prompt_str)
#     greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
#     return {"message": greeting_text.strip()}

# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     async def stream_generator():
#         history_tool.func = lambda query: tra_cuu_lich_su_hoc_tap_logic(query=query, username=username)
        
#         user_message_doc = {"username": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc)}
#         chat_history_collection.insert_one(user_message_doc)
        
#         history_cursor = chat_history_collection.find({"username": username}).sort("timestamp", -1).limit(10)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
        
#         full_response = ""
#         try:
#             # SỬA LỖI Ở ĐÂY: Dùng astream_log và thêm bộ lọc
#             async for chunk in agent_executor.astream_log(
#                 {"input": request.message, "chat_history": chat_history_str},
#                 include_names=["ChatOpenAI"],
#             ):
#                 for op in chunk.ops:
#                     if op["path"] == "/streamed_output/-":
#                         stream_content = op["value"]
#                         # Đôi khi output là một dict (khi có tool), chỉ lấy phần text
#                         if isinstance(stream_content, dict) and "output" in stream_content:
#                             token = stream_content["output"]
#                         elif isinstance(stream_content, str):
#                             token = stream_content
#                         else:
#                             continue # Bỏ qua các chunk không phải text

#                         full_response += token
#                         yield token
#                         await asyncio.sleep(0.01)
#         except Exception as e:
#             print(f"Lỗi khi streaming Agent: {e}")
#             full_response = "Xin lỗi, tôi gặp lỗi khi đang suy nghĩ. Bạn có thể thử lại không?"
#             yield full_response

#         # Làm sạch response trước khi lưu
#         match = re.search(r"<final_answer>(.*?)</final_answer>", full_response, re.DOTALL)
#         clean_response = match.group(1).strip() if match else re.sub(r'<[^>]*>', '', full_response).strip()

#         if clean_response:
#              ai_message_doc = {"username": username, "role": "assistant", "content": clean_response, "timestamp": datetime.now(timezone.utc)}
#              chat_history_collection.insert_one(ai_message_doc)

#     return StreamingResponse(stream_generator(), media_type="text/event-stream")

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     pipeline = [{"$match": {"username": username}}, {"$sort": {"timestamp": -1}}, {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "content": "$content"}}, {"$group": {"_id": "$date", "firstMessage": {"$last": "$content"}}}, {"$sort": {"_id": -1}}]
#     sessions = list(chat_history_collection.aggregate(pipeline))
#     return [{"session_id": s["_id"], "title": s["firstMessage"][:50] + "..."} for s in sessions]

# @app.get("/api/history/messages/{session_date}")
# async def get_session_messages(session_date: str, current_user: dict = Depends(get_current_user)): #...
#     username = current_user["username"]
#     start_date = datetime.strptime(f"{session_date}T00:00:00.000", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     end_date = datetime.strptime(f"{session_date}T23:59:59.999", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
#     history_cursor = chat_history_collection.find({"username": username, "timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
#     history_list = []
#     for doc in history_cursor:
#         history_list.append({"sender": doc["role"], "message": doc["content"]})
#     return history_list













# import os
# from dotenv import load_dotenv
# import asyncio
# import json
# import re
# from uuid import uuid4

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status, Response
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# from fastapi.responses import StreamingResponse

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, sessions_collection, chat_history_collection

# from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor, create_xml_agent
# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain_community.tools import DuckDuckGoSearchRun
# from langchain.schema.output_parser import OutputParserException

# # --- KHỞI TẠO CÁC THÀNH PHẦN CỐ ĐỊNH ---
# print(">>> [main.py] Đang khởi tạo các thành phần cố định...")
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'

# llm = ChatOpenAI(model="anthropic/claude-3-haiku", temperature=0.7, streaming=True)

# # --- CÁC HÀM LOGIC CỦA TOOL ---
# def tao_quiz_logic(topic: str) -> str:
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' ---")
    
#     # Một prompt mạnh mẽ hơn để đảm bảo LLM trả về đúng định dạng
#     prompt_str = f"""
#     Bạn là một chuyên gia tạo câu hỏi trắc nghiệm.
#     Hãy tạo một bài kiểm tra gồm 3 câu hỏi về chủ đề '{topic}'.
#     Mỗi câu hỏi phải có cấu trúc sau:
#     - "question": (string) Nội dung câu hỏi.
#     - "options": (array of strings) Chính xác 4 lựa chọn A, B, C, D.
#     - "answer": (string) Đáp án đúng, phải là một trong 4 lựa chọn trên.
#     - "explanation": (string) Một câu giải thích ngắn gọn tại sao đáp án đó lại đúng.

#     YÊU CẦU ĐỊNH DẠNG: Chỉ trả về một mảng JSON (một array chứa các object câu hỏi) hợp lệ.
#     KHÔNG được thêm bất kỳ văn bản, giải thích hay markdown nào bên ngoài mảng JSON.
#     Bắt đầu bằng `[` và kết thúc bằng `]`.

#     JSON của bạn:
#     """
    
#     try:
#         quiz_response = llm.invoke(prompt_str)
#         # Lấy nội dung text từ response
#         quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
        
#         # Tìm mảng JSON đầu tiên và duy nhất trong chuỗi trả về
#         match = re.search(r'\[\s*\{.*?\}\s*\]', quiz_json_str, re.DOTALL)
#         if not match:
#             print("Lỗi: Không tìm thấy JSON hợp lệ trong phản hồi của LLM.")
#             return json.dumps({ "error": "Không thể tạo quiz theo đúng định dạng." })

#         clean_json_str = match.group(0)
        
#         # Kiểm tra xem chuỗi có phải là JSON hợp lệ không
#         json.loads(clean_json_str) 
        
#         # Trả về chuỗi JSON sạch
#         return clean_json_str
        
#     except Exception as e:
#         print(f"Đã xảy ra lỗi nghiêm trọng khi tạo hoặc parse quiz: {e}")
#         return json.dumps({ "error": f"Lỗi khi tạo quiz: {e}" })

# # --- PROMPT TEMPLATE ---
# # prompt_template_str = """Bạn là 'Trí Tuệ', một trợ lý học tập AI chuyên gia.

# # **QUY TẮC ĐỊNH DẠNG ĐẦU RA (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT):**
# # Bạn CHỈ ĐƯỢC PHÉP trả lời bằng MỘT trong hai định dạng dưới đây.

# # **Định dạng 1: Yêu cầu Công cụ**
# # <tool><tool_name>tên_công_cụ</tool_name><parameters><query>đầu_vào_cho_công_cụ</query></parameters></tool>

# # **Định dạng 2: Câu trả lời Cuối cùng (Dạng văn bản nói chuyện)**
# # <final_answer>(Nội dung câu trả lời của bạn nằm ở đây)</final_answer>

# # **LƯU Ý QUAN TRỌNG VỀ TOOL `tao_quiz`:**
# # - Khi bạn quyết định sử dụng tool `tao_quiz`, đó là HÀNH ĐỘNG CUỐI CÙNG của bạn trong lượt này.
# # - Kết quả từ tool `tao_quiz` là một chuỗi JSON. Bạn KHÔNG cần phải đọc hay diễn giải nó.
# # - Chỉ cần gọi tool, và hệ thống sẽ tự động hiển thị quiz cho người dùng.
# # - Ví dụ: Nếu người dùng nói "tạo quiz đi", bạn chỉ cần trả về:
# #   <tool><tool_name>tao_quiz</tool_name><parameters><query>chủ đề đang thảo luận</query></parameters></tool>

# # ---
# # **QUY TẮC VỀ HÀNH VI VÀ CHẤT LƯỢNG NỘI DUNG (Áp dụng cho `<final_answer>`):**
# # (Phần này giữ nguyên như lần trước)
# # 1.  **Hiểu Ý Định Người Dùng:**
# #     *   Khi người dùng hỏi "ôn tập", "nhắc lại", hãy xác định **chủ đề học thuật gần nhất** và chỉ nhắc lại tên chủ đề đó.
# #     *   Khi tóm tắt lịch sử, hãy tập trung vào các **chủ đề học thuật**.
# # 2.  **Nói chuyện tự nhiên:** **Tuyệt đối không được nhắc đến các thuật ngữ kỹ thuật** của bạn.
# # 3.  **Đi sâu chi tiết:** Khi trả lời câu hỏi kiến thức mới, hãy giải thích có cấu trúc, ví dụ, chi tiết.
# # 4.  **Luôn chủ động:** Luôn kết thúc câu trả lời bằng một gợi ý hành động.

# # ---
# # **CÔNG CỤ HIỆN CÓ:**
# # {tools}
# # ---
# # **LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY:**
# # <history>{chat_history}</history>
# # ---
# # **YÊU CẦU MỚI TỪ NGƯỜI DÙNG:** {input}
# # ---
# # **BẮT ĐẦU SUY NGHĨ:**
# # {agent_scratchpad}
# # """
# prompt_template_str = """Bạn là 'Trí Tuệ', một trợ lý học tập AI chuyên gia.

# **QUY TẮC ĐỊNH DẠNG ĐẦU RA (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT):**
# Bạn CHỈ ĐƯỢC PHÉP trả lời bằng MỘT trong hai định dạng dưới đây.

# **Định dạng 1: Yêu cầu Công cụ**
# - Bạn sẽ tạo ra MỘT thẻ `<tool>` duy nhất.
# - Bên trong thẻ `<parameters>`, tên của thẻ tham số PHẢI TRÙNG KHỚP với tên tham số trong hàm của công cụ (ví dụ: tool `tao_quiz` có tham số `topic`, vậy bạn phải dùng thẻ `<topic>`).
# - **QUAN TRỌNG NHẤT:** SAU KHI bạn đã tạo ra thẻ `</tool>` đóng, bạn PHẢI DỪNG LẠI NGAY LẬP TỨC. KHÔNG được viết thêm bất kỳ ký tự nào khác.

# Ví dụ gọi tool `tao_quiz` với chủ đề "Lịch sử La Mã":
# <tool><tool_name>tao_quiz</tool_name><parameters><topic>Lịch sử La Mã</topic></parameters></tool>

# **Định dạng 2: Câu trả lời Cuối cùng (Dạng văn bản nói chuyện)**
# <final_answer>(Nội dung câu trả lời của bạn nằm ở đây)</final_answer>

# **LƯU Ý QUAN TRỌNG VỀ TOOL `tao_quiz`:**
# - Khi bạn quyết định sử dụng tool `tao_quiz`, đó là HÀNH ĐỘNG CUỐI CÙNG của bạn trong lượt này.
# - Kết quả từ tool `tao_quiz` là một chuỗi JSON. Bạn KHÔNG cần phải đọc hay diễn giải nó.
# - Chỉ cần gọi tool, và hệ thống sẽ tự động hiển thị quiz cho người dùng.

# ---
# **QUY TẮC VỀ HÀNH VI VÀ CHẤT LƯỢNG NỘI DUNG (Áp dụng cho `<final_answer>`):**
# (Phần này giữ nguyên như lần trước)
# 1.  **Hiểu Ý Định Người Dùng:**
#     *   Khi người dùng hỏi "ôn tập", "nhắc lại", hãy xác định **chủ đề học thuật gần nhất** và chỉ nhắc lại tên chủ đề đó.
#     *   Khi tóm tắt lịch sử, hãy tập trung vào các **chủ đề học thuật**.
# 2.  **Nói chuyện tự nhiên:** **Tuyệt đối không được nhắc đến các thuật ngữ kỹ thuật** của bạn.
# 3.  **Đi sâu chi tiết:** Khi trả lời câu hỏi kiến thức mới, hãy giải thích có cấu trúc, ví dụ, chi tiết.
# 4.  **Luôn chủ động:** Luôn kết thúc câu trả lời bằng một gợi ý hành động.

# ---
# **CÔNG CỤ HIỆN CÓ:**
# {tools}
# ---
# **LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY:**
# <history>{chat_history}</history>
# ---
# **YÊU CẦU MỚI TỪ NGƯỜI DÙNG:** {input}
# ---
# **BẮT ĐẦU SUY NGHĨ:**
# {agent_scratchpad}
# """
# prompt = PromptTemplate.from_template(prompt_template_str)
# print(">>> [main.py] Các thành phần cố định đã khởi tạo.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Session-ID"])

# # --- Endpoints Auth, Greeting, History (Đã đúng) ---
# @app.post("/auth/register")
# # ... (Giữ nguyên)
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# # ... (Giữ nguyên)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/api/greeting")
# # ... (Giữ nguyên)
# async def get_personalized_greeting(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     last_message = chat_history_collection.find_one({"user_id": username, "role": "user"}, sort=[("timestamp", -1)])
#     last_topic = last_message["content"] if last_message else None
#     prompt_str = f"Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.\n- Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.\n- Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.\nLời chào của bạn:"
#     greeting_response = llm.invoke(prompt_str)
#     greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
#     return {"message": greeting_text.strip()}

# @app.get("/api/history/sessions")
# # ... (Giữ nguyên)
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     sessions_cursor = sessions_collection.find({ "user_id": username }).sort("updated_at", -1)
#     return [{"session_id": s["session_id"], "title": s["title"]} for s in sessions_cursor]

# @app.get("/api/history/messages/{session_id}")
# # ... (Giữ nguyên)
# async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     session = sessions_collection.find_one({ "session_id": session_id, "user_id": username })
#     if not session: raise HTTPException(status_code=404, detail="Session not found or access denied")
#     history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", 1)
#     return [{"sender": ("ai" if doc["role"] == "assistant" else doc["role"]), "message": doc["content"]} for doc in history_cursor]


# # --- Endpoint Chat ---
# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, response: Response, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     session_id = request.session_id
#     is_new_session = False

#     if not session_id:
#         is_new_session = True
#         session_id = str(uuid4())
#         new_session = { "session_id": session_id, "user_id": username, "title": "Cuộc trò chuyện mới...", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc) }
#         sessions_collection.insert_one(new_session)
#     else:
#         sessions_collection.update_one({ "session_id": session_id, "user_id": username }, { "$set": { "updated_at": datetime.now(timezone.utc) } })
#     response.headers["X-Session-ID"] = session_id

#     async def stream_generator():
#         # <<< SỬA LỖI AGENT BỊ LÚ LẪN >>>
#         # Xây dựng toàn bộ Agent và Tools BÊN TRONG request để đảm bảo môi trường "sạch"
        
#         # 1. Định nghĩa các tool tĩnh
#         search_tool = DuckDuckGoSearchRun(name="tim_kiem_internet")
#         quiz_tool = Tool(
#             name="tao_quiz",
#             func=tao_quiz_logic,
#             description="Rất hữu ích khi người dùng muốn kiểm tra kiến thức về một chủ đề cụ thể. Đầu vào là tên của chủ đề."
#         )
#         tools = [search_tool, quiz_tool]

#         # 2. Tạo Agent và Executor với bộ tool hoàn chỉnh
#         agent = create_xml_agent(llm, tools, prompt)
#         custom_error_message = """LỖI ĐỊNH DẠNG: Phản hồi của bạn không tuân thủ quy tắc. BẠN BẮT BUỘC phải sử dụng một trong hai định dạng sau: <tool>...</tool> HOẶC <final_answer>...</final_answer>. Hãy thử lại và gói câu trả lời của bạn vào đúng thẻ XML."""
#         agent_executor = AgentExecutor(
#             agent=agent, 
#             tools=tools, 
#             verbose=True, 
#             handle_parsing_errors=custom_error_message, 
#             max_iterations=5
#         )
        
#         # 3. Tiếp tục logic như cũ
#         user_message_doc = { "session_id": session_id, "user_id": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc) }
#         chat_history_collection.insert_one(user_message_doc)
        
#         history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", -1).limit(20)
#         chat_history_str = "\n".join([f"{doc['role']}: {doc['content']}" for doc in reversed(list(history_cursor))])
        
#         full_response = ""
#         try:
#             # Chỉ gọi Agent một lần duy nhất với ainvoke thay vì astream_log
#             # vì chúng ta cần toàn bộ output để parse (JSON hoặc text)
#             result = await agent_executor.ainvoke({ "input": request.message, "chat_history": chat_history_str })
#             full_response = result.get("output", "")
#             yield full_response

#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")
#             error_message = "Xin lỗi, một lỗi không mong muốn đã xảy ra. Vui lòng thử lại."
#             full_response = error_message
#             yield error_message

#         # Phần xử lý và lưu trữ kết quả không thay đổi nhiều
#         # Tìm xem output có phải là JSON quiz không
#         json_match = re.search(r'\[\s*\{.*?\}\s*\]', full_response, re.DOTALL)
#         is_quiz = json_match is not None

#         # Chỉ lưu vào lịch sử nếu đó không phải là một quiz JSON
#         if not is_quiz:
#             # Trích xuất câu trả lời từ thẻ <final_answer> nếu có
#             final_answer_match = re.findall(r"<final_answer>(.*?)</final_answer>", full_response, re.DOTALL)
#             clean_response = ""
#             if final_answer_match:
#                 clean_response = final_answer_match[-1].strip()
#             elif "<tool>" not in full_response:
#                 clean_response = re.sub(r'<[^>]*>', '', full_response).strip()
            
#             if clean_response:
#                 ai_message_doc = { "session_id": session_id, "user_id": username, "role": "assistant", "content": clean_response, "timestamp": datetime.now(timezone.utc) }
#                 chat_history_collection.insert_one(ai_message_doc)
#                 if is_new_session:
#                     conversation_for_title = f"user: {request.message}\nassistant: {clean_response}"
#                     new_title = await generate_session_title(conversation_for_title, llm)
#                     sessions_collection.update_one({ "session_id": session_id }, { "$set": { "title": new_title } })

#     return StreamingResponse(stream_generator(), media_type="text/event-stream")

# # Hàm hỗ trợ tạo tiêu đề (để cuối file)
# async def generate_session_title(message_history: str, llm_instance: ChatOpenAI) -> str:
#     # ... (Giữ nguyên)
#     prompt = f"Dựa trên đoạn hội thoại sau, hãy tạo ra một tiêu đề ngắn gọn (dưới 10 từ) và súc tích bằng tiếng Việt.\n\nĐoạn hội thoại:\n{message_history}\n\nTiêu đề của bạn:"
#     try:
#         response = await llm_instance.ainvoke(prompt)
#         title = response.content if hasattr(response, 'content') else str(response)
#         return title.strip().strip('"')
#     except Exception as e:
#         print(f"Lỗi khi tạo tiêu đề: {e}")
#         return "Cuộc trò chuyện mới"

# main.py (Phiên bản cuối cùng - Tái cấu trúc với Function Calling, ổn định và thông minh)





# import os
# from dotenv import load_dotenv
# import asyncio
# import json
# import re
# from uuid import uuid4
# from pydantic import BaseModel
# from typing import Dict,Any

# print(">>> [main.py] Bắt đầu tải file .env...")
# is_loaded = load_dotenv()
# if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
# else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")

# print(">>> [main.py] Các API keys đã được tải thành công.")

# from fastapi import FastAPI, Depends, HTTPException, status, Response
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordRequestForm
# from datetime import datetime, timezone
# from fastapi.responses import StreamingResponse

# from models import UserCreate, ChatRequest
# from auth import get_password_hash, verify_password, create_access_token, get_current_user
# from database import user_collection, sessions_collection, chat_history_collection, quizzes_collection, incorrect_answers_collection


# from langchain_openai import ChatOpenAI
# from langchain.tools import tool
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
# from langchain_core.utils.function_calling import convert_to_openai_tool
# from langchain_community.tools import DuckDuckGoSearchRun

# # --- KHỞI TẠO CÁC THÀNH PHẦN CỐ ĐỊNH ---
# print(">>> [main.py] Đang khởi tạo các thành phần cố định...")
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
# os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'

# # Sử dụng một model hỗ trợ tốt tool calling. GPT-3.5 Turbo là lựa chọn kinh tế và rất tin cậy.
# # Bạn vẫn có thể dùng "anthropic/claude-3-haiku" nếu muốn, nó cũng hỗ trợ tốt.
# llm = ChatOpenAI(model="openai/gpt-3.5-turbo", temperature=0.5, streaming=True)

# # --- CÁC HÀM LOGIC CỦA TOOL (Rất quan trọng: Thêm docstring rõ ràng) ---
# @tool
# def tao_quiz_logic(topic: str, user_id: str) -> dict:
#     """Tạo một bài kiểm tra trắc nghiệm về một chủ đề cụ thể, LƯU VÀO DATABASE, và trả về trạng thái. 'topic' là chủ đề của bài quiz. 'user_id' là định danh của người dùng."""
#     print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' cho user: '{user_id}' ---")
#     prompt_str = f"Bạn là một chuyên gia tạo câu hỏi trắc nghiệm. Hãy tạo một bài kiểm tra gồm 3 câu hỏi về chủ đề '{topic}'. Mỗi câu hỏi phải có cấu trúc sau: \"question\": (string), \"options\": (array of 4 strings), \"answer\": (string), \"explanation\": (string). YÊU CẦU ĐỊNH DẠNG: Chỉ trả về một mảng JSON hợp lệ. Bắt đầu bằng `[` và kết thúc bằng `]`."
#     try:
#         quiz_creator_llm = ChatOpenAI(model="openai/gpt-3.5-turbo", temperature=0.3)
#         quiz_response = quiz_creator_llm.invoke(prompt_str)
#         quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
        
#         match = re.search(r'\[\s*\{.*?\}\s*\]', quiz_json_str, re.DOTALL)
#         if not match:
#             raise ValueError("LLM không trả về định dạng JSON như mong đợi.")
        
#         clean_json_str = match.group(0)
#         questions_data = json.loads(clean_json_str)
        
#         quiz_document = {
#             "quiz_id": str(uuid4()), "user_id": user_id, "topic": topic,
#             "questions": questions_data, "created_at": datetime.now(timezone.utc),
#             "completed_at": None, "score": None
#         }
#         quizzes_collection.insert_one(quiz_document)
#         print(f"--- Đã lưu quiz về '{topic}' vào DB thành công! ---")
#         return {"status": "success", "topic": topic}
        
#     except Exception as e:
#         print(f"Lỗi nghiêm trọng khi tạo hoặc lưu quiz: {e}")
#         return {"status": "error", "message": str(e)}

# @tool
# def tim_kiem_internet_logic(query: str) -> str:
#     """Tìm kiếm thông tin trên Internet khi không có đủ kiến thức."""
#     print(f"--- LOGIC TOOL 'Tìm kiếm' được gọi với query: '{query}' ---")
#     return DuckDuckGoSearchRun().run(query)

# print(">>> [main.py] Các thành phần cố định đã khởi tạo.")

# # --- KHỞI TẠO APP VÀ CÁC ENDPOINTS ---
# app = FastAPI()
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Session-ID"])

# # ... (Các endpoints Auth, Greeting, History không cần thay đổi và đã đúng) ...
# @app.post("/auth/register")
# async def register_user(user: UserCreate):
#     existing_user = user_collection.find_one({"username": user.username})
#     if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
#     hashed_password = get_password_hash(user.password)
#     user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
#     return {"message": "User created successfully"}

# @app.post("/auth/login")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     access_token = create_access_token(data={"sub": user["username"]})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/api/greeting")
# async def get_personalized_greeting(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     last_message = chat_history_collection.find_one({"user_id": username, "role": "user"}, sort=[("timestamp", -1)])
#     last_topic = last_message["content"] if last_message else None
#     prompt_str = f"Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.\n- Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.\n- Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.\nLời chào của bạn:"
#     greeting_response = llm.invoke(prompt_str)
#     greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
#     return {"message": greeting_text.strip()}

# @app.get("/api/history/sessions")
# async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     sessions_cursor = sessions_collection.find({ "user_id": username }).sort("updated_at", -1)
#     return [{"session_id": s["session_id"], "title": s["title"]} for s in sessions_cursor]

# @app.get("/api/history/messages/{session_id}")
# async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     session = sessions_collection.find_one({ "session_id": session_id, "user_id": username })
#     if not session: raise HTTPException(status_code=404, detail="Session not found or access denied")
#     history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", 1)
#     return [{"sender": ("ai" if doc["role"] == "assistant" else doc["role"]), "message": doc["content"]} for doc in history_cursor]
# @app.get("/api/quizzes")
# async def get_user_quizzes(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     quizzes_cursor = quizzes_collection.find({"user_id": username}).sort("created_at", -1)
    
#     quiz_list = []
#     for q in quizzes_cursor:
#         status = "Chưa làm"
#         if q.get("completed_at"):
#             status = f"Đã hoàn thành ({q.get('score', 0)}/{len(q.get('questions', []))})"
#         elif q.get("user_answers") and len(q.get("user_answers")) > 0:
#             status = "Đang làm dở"
            
#         quiz_list.append({
#             "quiz_id": q["quiz_id"], 
#             "topic": q["topic"], 
#             "created_at": q["created_at"],
#             "status": status # Thêm trạng thái để frontend hiển thị
#         })
#     return quiz_list
# class QuizProgress(BaseModel):
#     user_answers: Dict[str, Any]
# class QuizSubmission(BaseModel):
#     user_answers: Dict[str, str]
# @app.post("/api/quizzes/{quiz_id}/submit")
# async def submit_quiz(quiz_id: str, submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
    
#     # 1. Tìm bài quiz trong DB
#     quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
#     if not quiz:
#         raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz.")
#     if quiz.get("completed_at"):
#         raise HTTPException(status_code=400, detail="Bạn đã hoàn thành bài quiz này rồi.")

#     # 2. Chấm điểm và xác định câu sai
#     score = 0
#     results = {}
#     user_answers = submission.user_answers
    
#     for index, question_data in enumerate(quiz["questions"]):
#         q_index_str = str(index)
#         user_answer = user_answers.get(q_index_str)
#         is_correct = user_answer == question_data["answer"]
        
#         if is_correct:
#             score += 1
#         else:
#             # Lưu câu sai vào collection riêng
#             incorrect_doc = {
#                 "user_id": username,
#                 "quiz_id": quiz_id,
#                 "topic": quiz["topic"],
#                 "question": question_data["question"],
#                 "options": question_data["options"],
#                 "correct_answer": question_data["answer"],
#                 "user_answer": user_answer,
#                 "explanation": question_data["explanation"],
#                 "incorrectly_answered_at": datetime.now(timezone.utc)
#             }
#             # Dùng update_one với upsert=True để tránh lưu trùng lặp câu hỏi sai
#             incorrect_answers_collection.update_one(
#                 {"user_id": username, "question": question_data["question"]},
#                 {"$set": incorrect_doc},
#                 upsert=True
#             )
            
#     # 3. Cập nhật lại document của quiz với kết quả
#     quizzes_collection.update_one(
#         {"quiz_id": quiz_id},
#         {
#             "$set": {
#                 "completed_at": datetime.now(timezone.utc),
#                 "score": score,
#                 "user_answers": user_answers
#             }
#         }
#     )
    
#     print(f"User '{username}' đã nộp bài quiz '{quiz['topic']}' với điểm số: {score}/{len(quiz['questions'])}")
    
#     # 4. Trả về kết quả chi tiết để frontend hiển thị
#     return {"message": "Nộp bài thành công!", "score": score, "total_questions": len(quiz["questions"])}

# # <<< THAY ĐỔI 5: Endpoint MỚI để lấy các câu sai từ DB >>>
# @app.get("/api/incorrect-answers")
# async def get_incorrect_answers(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     incorrect_docs = incorrect_answers_collection.find({"user_id": username}).sort("incorrectly_answered_at", -1)
    
#     # Chuyển đổi thành định dạng quiz để tái sử dụng component QuizView
#     questions_for_review = [
#         {
#             "question": doc["question"],
#             "options": doc["options"],
#             "answer": doc["correct_answer"],
#             "explanation": doc["explanation"]
#         } 
#         for doc in incorrect_docs
#     ]
    
#     return questions_for_review
# # --- ENDPOINT CHAT (SỬA LỖI TRUY CẬP DANH SÁCH) ---
# @app.post("/api/chat")
# async def chat_with_agent(request: ChatRequest, response: Response, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     session_id = request.session_id
#     is_new_session = False

#     if not session_id:
#         is_new_session = True
#         session_id = str(uuid4())
#         new_session = { "session_id": session_id, "user_id": username, "title": "Cuộc trò chuyện mới...", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc) }
#         sessions_collection.insert_one(new_session)
#     else:
#         sessions_collection.update_one({ "session_id": session_id, "user_id": username }, { "$set": { "updated_at": datetime.now(timezone.utc) } })
#     response.headers["X-Session-ID"] = session_id

#     async def stream_generator():
#         tools = [tao_quiz_logic, tim_kiem_internet_logic,get_user_weaknesses]
        
#         system_prompt = """Bạn là 'Trí Tuệ', một trợ lý học tập AI chuyên gia, thân thiện và thông minh.
#         - Khi người dùng yêu cầu hành động (ví dụ: "tạo quiz", "tìm kiếm"), nhưng không cung cấp đủ tham số, bạn BẮT BUỘC phải nhìn vào lượt trò chuyện ngay trước đó để suy ra tham số còn thiếu.
#         - Ví dụ: Nếu bạn vừa nhắc đến chủ đề "Cây quyết định" và người dùng trả lời "tốt thôi, tạo cho tôi một bài quiz", bạn phải tự động hiểu rằng `topic` của quiz là "Cây quyết định" và gọi tool `tao_quiz_logic`.
#         - Khi trả lời câu hỏi kiến thức, hãy giải thích có cấu trúc, chi tiết, nêu ví dụ.
#         - Luôn kết thúc câu trả lời bằng một gợi ý hành động để khuyến khích người dùng học tiếp.
#         - Tuyệt đối không được nhắc đến các thuật ngữ kỹ thuật như 'lịch sử được cung cấp', 'prompt' hay 'quy tắc' của bạn.
#         """
        
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", system_prompt),
#             ("placeholder", "{chat_history}"),
#             ("human", "{input}"),
#         ])
        
#         llm_with_tools = llm.bind_tools(tools)
#         chain = prompt | llm_with_tools

#         history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", -1).limit(10)
#         chat_history_for_prompt = []
#         for doc in reversed(list(history_cursor)):
#             if doc["role"] == "user":
#                 chat_history_for_prompt.append(HumanMessage(content=doc["content"]))
#             elif doc["role"] == "assistant":
#                 chat_history_for_prompt.append(AIMessage(content=doc["content"]))
        
#         user_message_doc = { "session_id": session_id, "user_id": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc) }
#         chat_history_collection.insert_one(user_message_doc)
        
#         full_response_content = ""
#         try:
#             ai_response = await chain.ainvoke({
#                 "input": request.message,
#                 "chat_history": chat_history_for_prompt
#             })
#             if ai_response.tool_calls:
#                 # <<< THAY ĐỔI QUAN TRỌNG NHẤT Ở ĐÂY >>>
#                 # tool_calls là một DANH SÁCH, chúng ta cần lấy phần tử đầu tiên [0]
#                 tool_call = ai_response.tool_calls[0]
                
#                 tool_name = tool_call['name']
#                 tool_args = tool_call['args']
                
#                 print(f"--- AI yêu cầu gọi tool: {tool_name} với tham số: {tool_args} ---")
                
#                 selected_tool = next((t for t in tools if t.name == tool_name), None)
#                 if selected_tool:
#                     if tool_name == "tao_quiz_logic":
#                         # user_id đã được AI tự động suy luận và điền vào tool_args nếu
#                         # chúng ta thêm nó vào docstring. Tuy nhiên, để an toàn,
#                         # ta vẫn có thể gán lại ở đây.
#                         tool_args['user_id'] = username
#                         tool_output = selected_tool.run(tool_args)
                        
#                         if tool_output.get("status") == "success":
#                             topic = tool_output.get('topic', 'chủ đề đó')
#                             full_response_content = f"Tôi đã tạo xong một bài quiz về '{topic}' cho bạn rồi. Bạn có thể vào mục 'Bài kiểm tra' để làm nhé!"
#                         else:
#                             full_response_content = "Rất tiếc, đã có lỗi xảy ra trong quá trình tạo quiz của bạn. Vui lòng thử lại sau."
                    
#                     elif tool_name == "tim_kiem_internet_logic":
#                         full_response_content = selected_tool.run(tool_args)
                    
#                 else:
#                     full_response_content = "Lỗi: Tool không tồn tại."
#             else:
#                 full_response_content = ai_response.content
#         except Exception as e:
#             print(f"Lỗi nghiêm trọng khi chạy chain: {e}")
#             full_response_content = "Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý."
            
#         yield full_response_content

#         if full_response_content:
#             ai_message_doc = { "session_id": session_id, "user_id": username, "role": "assistant", "content": full_response_content, "timestamp": datetime.now(timezone.utc) }
#             chat_history_collection.insert_one(ai_message_doc)
#             if is_new_session:
#                 conversation_for_title = f"user: {request.message}\nassistant: {full_response_content}"
#                 new_title = await generate_session_title(conversation_for_title, llm)
#                 sessions_collection.update_one({ "session_id": session_id }, { "$set": { "title": new_title } })

#     return StreamingResponse(stream_generator(), media_type="text/event-stream")
# @app.put("/api/quizzes/{quiz_id}/progress")
# async def save_quiz_progress(quiz_id: str, progress: QuizProgress, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
    
#     # Tìm quiz và đảm bảo nó chưa được hoàn thành
#     quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
#     if not quiz:
#         raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz.")
#     if quiz.get("completed_at"):
#         raise HTTPException(status_code=400, detail="Không thể cập nhật bài quiz đã hoàn thành.")

#     # Cập nhật trường user_answers trong DB
#     quizzes_collection.update_one(
#         {"quiz_id": quiz_id},
#         {"$set": {"user_answers": progress.user_answers}}
#     )
    
#     return {"message": "Tiến trình đã được lưu."}
# @app.get("/api/quizzes/{quiz_id}")
# async def get_quiz_details(quiz_id: str, current_user: dict = Depends(get_current_user)):
#     """Lấy chi tiết một bài quiz cụ thể để người dùng có thể làm bài."""
#     username = current_user["username"]
    
#     # Query phải khớp cả quiz_id và user_id để đảm bảo bảo mật
#     quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
    
#     if not quiz:
#         raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz hoặc bạn không có quyền truy cập.")
        
#     # QUAN TRỌNG: Loại bỏ trường '_id' của MongoDB trước khi trả về
#     # vì nó không thể được chuyển đổi thành JSON một cách tự động.
#     quiz.pop('_id', None)
    
#     return quiz
# @tool
# def get_user_weaknesses(user_id: str) -> str:
#     """Lấy danh sách các chủ đề và câu hỏi mà người dùng thường trả lời sai để tạo nội dung ôn tập cá nhân hóa."""
#     incorrect_docs = incorrect_answers_collection.find({"user_id": user_id}).limit(10)
    
#     if not incorrect_docs:
#         return "Người dùng này chưa trả lời sai câu nào."
        
#     summary = "Người dùng này thường gặp khó khăn với các câu hỏi sau:\n"
#     for doc in incorrect_docs:
#         summary += f"- Chủ đề '{doc['topic']}': Câu hỏi '{doc['question']}' (Đáp án đúng: {doc['correct_answer']})\n"
        
#     return summary
# # Hàm hỗ trợ tạo tiêu đề
# async def generate_session_title(message_history: str, llm_instance: ChatOpenAI) -> str:
#     prompt = f"Dựa trên đoạn hội thoại sau, hãy tạo ra một tiêu đề ngắn gọn (dưới 10 từ) và súc tích bằng tiếng Việt.\n\nĐoạn hội thoại:\n{message_history}\n\nTiêu đề của bạn:"
#     try:
#         response = await llm_instance.ainvoke(prompt)
#         title = response.content if hasattr(response, 'content') else str(response)
#         return title.strip().strip('"')
#     except Exception as e:
#         print(f"Lỗi khi tạo tiêu đề: {e}")
#         return "Cuộc trò chuyện mới"

import os
from dotenv import load_dotenv
import json
import re
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse

# --- Local Imports ---
from models import UserCreate, ChatRequest
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from database import user_collection, sessions_collection, chat_history_collection, quizzes_collection, incorrect_answers_collection

# --- LangChain Imports ---
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_community.tools import DuckDuckGoSearchRun

# --- 1. CONFIGURATION & SETUP ---
print(">>> [main.py] Bắt đầu tải file .env...")
is_loaded = load_dotenv()
if is_loaded: print(">>> [main.py] File .env được tìm thấy và đã tải.")
else: print(">>> [main.py] CẢNH BÁO: Không tìm thấy file .env.")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("LỖI NGHIÊM TRỌNG: Không tìm thấy OPENROUTER_API_KEY...")
print(">>> [main.py] Các API keys đã được tải thành công.")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_DEFAULT_HEADERS"] = '{"HTTP-Referer": "http://localhost", "X-Title": "Personalized Learning Agent"}'

llm = ChatOpenAI(model="openai/gpt-3.5-turbo", temperature=0.5, streaming=True)

# --- 2. PYDANTIC MODELS for API Requests ---
class QuizProgress(BaseModel):
    user_answers: Dict[str, Any]

class QuizSubmission(BaseModel):
    user_answers: Dict[str, str]

# --- 3. TOOL LOGIC & DEFINITIONS ---

# --- Tool 1: Tạo Quiz ---
@tool
def tao_quiz(topic: str, num_questions: int = 3) -> str:
    """
    Tạo nội dung cho một bài kiểm tra trắc nghiệm về một chủ đề cụ thể.
    - 'topic' (bắt buộc): là chủ đề của bài quiz.
    - 'num_questions' (tùy chọn): là số lượng câu hỏi cần tạo, mặc định là 3 nếu không được chỉ định.
    """
    print(f"--- LOGIC TOOL 'Tạo Quiz' được gọi với chủ đề: '{topic}' và số lượng: {num_questions} câu ---")
    
    # Giới hạn hợp lý để tránh yêu cầu quá lớn
    if num_questions > 20:
        num_questions = 20
        
    prompt_str = (
        f"Bạn là một chuyên gia tạo câu hỏi trắc nghiệm. "
        f"Hãy tạo một bài kiểm tra gồm chính xác {num_questions} câu hỏi về chủ đề '{topic}'. "
        f"Mỗi câu hỏi phải có cấu trúc sau: \"question\": (string), \"options\": (array of 4 strings), \"answer\": (string), \"explanation\": (string). "
        f"YÊU CẦU ĐỊNH DẠNG: Chỉ trả về một mảng JSON hợp lệ. Bắt đầu bằng `[` và kết thúc bằng `]`."
    )
    try:
        quiz_creator_llm = ChatOpenAI(model="openai/gpt-3.5-turbo", temperature=0.3)
        quiz_response = quiz_creator_llm.invoke(prompt_str)
        quiz_json_str = quiz_response.content if hasattr(quiz_response, 'content') else str(quiz_response)
        
        match = re.search(r'\[\s*\{.*?\}\s*\]', quiz_json_str, re.DOTALL)
        if not match: raise ValueError("LLM không trả về định dạng JSON như mong đợi.")
        
        clean_json_str = match.group(0)
        # Kiểm tra xem có đủ số lượng câu hỏi không (đôi khi LLM không tuân thủ 100%)
        # Đây là một bước kiểm tra nâng cao, không bắt buộc nhưng nên có
        data = json.loads(clean_json_str)
        print(f"--- LLM đã tạo ra {len(data)}/{num_questions} câu hỏi. ---")

        return clean_json_str
        
    except Exception as e:
        print(f"Lỗi khi tạo nội dung quiz: {e}")
        return json.dumps({"error": f"Lỗi khi tạo nội dung quiz: {e}"})

# --- Tool 2: Tìm kiếm Internet ---
@tool
def tim_kiem_internet(query: str) -> str:
    """Tìm kiếm thông tin trên Internet khi không có đủ kiến thức. 'query' là câu hỏi hoặc từ khóa tìm kiếm."""
    print(f"--- LOGIC TOOL 'Tìm kiếm' được gọi với query: '{query}' ---")
    return DuckDuckGoSearchRun().run(query)

# --- Tool 3: Ôn tập cá nhân hóa ---
def get_user_weaknesses_logic(user_id: str) -> str:
    """Hàm logic để lấy dữ liệu các câu sai từ DB."""
    incorrect_docs = list(incorrect_answers_collection.find({"user_id": user_id}).sort("incorrectly_answered_at", -1).limit(5))
    if not incorrect_docs:
        return "Người dùng này chưa có câu trả lời sai nào được ghi nhận."
    
    summary = "Đây là những điểm yếu của người dùng:\n"
    for doc in incorrect_docs:
        summary += (
            f"- Chủ đề: '{doc.get('topic', 'N/A')}'. "
            f"Câu hỏi: '{doc.get('question', 'N/A')}'. "
            f"Đáp án đúng: '{doc.get('correct_answer', 'N/A')}'. "
            f"Giải thích: '{doc.get('explanation', 'N/A')}'\n"
        )
    return summary

@tool
def get_user_weaknesses() -> str:
    """Rất hữu ích khi người dùng yêu cầu ôn tập, xem lại kiến thức họ còn yếu, hoặc hỏi về những câu họ đã làm sai. Tool này không cần tham số đầu vào."""
    return "Đang lấy dữ liệu điểm yếu của người dùng..."

# --- 4. FASTAPI APP INITIALIZATION ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Session-ID"])

# --- 5. API ENDPOINTS ---

# --- Auth Endpoints ---
@app.post("/auth/register")
async def register_user(user: UserCreate):
    # ... (code không đổi)
    existing_user = user_collection.find_one({"username": user.username})
    if existing_user: raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    user_collection.insert_one({"username": user.username, "hashed_password": hashed_password})
    return {"message": "User created successfully"}

@app.post("/auth/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # ... (code không đổi)
    user = user_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Greeting & History Endpoints ---
@app.get("/api/greeting")
async def get_personalized_greeting(current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    last_message = chat_history_collection.find_one({"user_id": username, "role": "user"}, sort=[("timestamp", -1)])
    last_topic = last_message["content"] if last_message else None
    prompt_str = f"Viết một lời chào mừng quay trở lại thật thân thiện (khoảng 2-3 câu) cho người dùng tên là '{username}'.\n- Nếu người dùng đã học một chủ đề trước đó ({last_topic}), hãy nhắc lại chủ đề đó và gợi ý ôn tập hoặc học tiếp.\n- Nếu đây là lần đầu tiên ({last_topic} is None), hãy chào mừng họ và khuyến khích họ bắt đầu.\nLời chào của bạn:"
    greeting_response = llm.invoke(prompt_str)
    greeting_text = greeting_response.content if hasattr(greeting_response, 'content') else str(greeting_response)
    return {"message": greeting_text.strip()}

@app.get("/api/history/sessions")
async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    sessions_cursor = sessions_collection.find({ "user_id": username }).sort("updated_at", -1)
    return [{"session_id": s["session_id"], "title": s["title"]} for s in sessions_cursor]

@app.get("/api/history/messages/{session_id}")
async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    session = sessions_collection.find_one({ "session_id": session_id, "user_id": username })
    if not session: raise HTTPException(status_code=404, detail="Session not found or access denied")
    history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", 1)
    return [{"sender": ("ai" if doc["role"] == "assistant" else doc["role"]), "message": doc["content"]} for doc in history_cursor]

# --- Quiz Management Endpoints ---
@app.get("/api/quizzes")
async def get_user_quizzes(current_user: dict = Depends(get_current_user)):
    """Lấy tất cả các bài quiz của người dùng, bao gồm cả trạng thái và điểm số."""
    username = current_user["username"]
    quizzes_cursor = quizzes_collection.find({"user_id": username}).sort("created_at", -1)
    
    quiz_list = []
    for q in quizzes_cursor:
        total_questions = len(q.get("questions", []))
        status = "Mới"
        score_display = f"0/{total_questions}" # Mặc định

        if q.get("completed_at"):
            score = q.get('score', 0)
            status = "Đã hoàn thành"
            score_display = f"{score}/{total_questions}"
        elif q.get("user_answers") and len(q.get("user_answers")) > 0:
            status = "Đang làm dở"
        
        quiz_list.append({
            "quiz_id": q["quiz_id"], 
            "topic": q["topic"], 
            "created_at": q["created_at"],
            "status": status,
            "score_display": score_display # Dữ liệu mới để hiển thị điểm
        })
    return quiz_list
@app.get("/api/quizzes/{quiz_id}")
async def get_quiz_details(quiz_id: str, current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
    if not quiz: raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz hoặc bạn không có quyền truy cập.")
    quiz.pop('_id', None)
    return quiz

@app.put("/api/quizzes/{quiz_id}/progress")
async def save_quiz_progress(quiz_id: str, progress: QuizProgress, current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
    if not quiz: raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz.")
    if quiz.get("completed_at"): raise HTTPException(status_code=400, detail="Không thể cập nhật bài quiz đã hoàn thành.")
    quizzes_collection.update_one({"quiz_id": quiz_id}, {"$set": {"user_answers": progress.user_answers}})
    return {"message": "Tiến trình đã được lưu."}

@app.post("/api/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    quiz = quizzes_collection.find_one({"quiz_id": quiz_id, "user_id": username})
    if not quiz: raise HTTPException(status_code=404, detail="Không tìm thấy bài quiz.")
    if quiz.get("completed_at"): raise HTTPException(status_code=400, detail="Bạn đã hoàn thành bài quiz này rồi.")
    score = 0
    for index, question_data in enumerate(quiz["questions"]):
        if str(index) in submission.user_answers and submission.user_answers[str(index)] == question_data["answer"]:
            score += 1
        else:
            incorrect_doc = {"user_id": username, "quiz_id": quiz_id, "topic": quiz["topic"], "question": question_data["question"], "options": question_data["options"], "correct_answer": question_data["answer"], "user_answer": submission.user_answers.get(str(index)), "explanation": question_data["explanation"], "incorrectly_answered_at": datetime.now(timezone.utc)}
            incorrect_answers_collection.update_one({"user_id": username, "question": question_data["question"]}, {"$set": incorrect_doc}, upsert=True)
    quizzes_collection.update_one({"quiz_id": quiz_id}, {"$set": {"completed_at": datetime.now(timezone.utc), "score": score, "user_answers": submission.user_answers}})
    return {"message": "Nộp bài thành công!", "score": score, "total_questions": len(quiz["questions"])}

@app.get("/api/incorrect-answers")
async def get_incorrect_answers(current_user: dict = Depends(get_current_user)):
    # ... (code không đổi)
    username = current_user["username"]
    incorrect_docs = incorrect_answers_collection.find({"user_id": username}).sort("incorrectly_answered_at", -1)
    questions_for_review = [{"question": doc["question"], "options": doc["options"], "answer": doc["correct_answer"], "explanation": doc["explanation"]} for doc in incorrect_docs]
    return questions_for_review

# --- Main Chat Endpoint (Agent Logic) ---
# --- Main Chat Endpoint (Agent Logic - SỬA LỖI REACT LOOP) ---
@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest, response: Response, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    session_id = request.session_id
    is_new_session = False
    if not session_id:
        is_new_session = True
        session_id = str(uuid4())
        new_session = { "session_id": session_id, "user_id": username, "title": "Cuộc trò chuyện mới...", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc) }
        sessions_collection.insert_one(new_session)
    else:
        sessions_collection.update_one({ "session_id": session_id, "user_id": username }, { "$set": { "updated_at": datetime.now(timezone.utc) } })
    response.headers["X-Session-ID"] = session_id

    async def stream_generator():
        tools = [tao_quiz, tim_kiem_internet, get_user_weaknesses]
        system_prompt = """Bạn là 'Trí Tuệ', một trợ lý học tập AI chuyên gia, thân thiện và tận tâm.

        **QUY TẮC CHUNG:**
        - Luôn suy luận để gọi tool khi cần thiết. Nếu người dùng yêu cầu hành động mà không cung cấp tham số, hãy suy luận từ lịch sử chat.
        - Khi trả lời câu hỏi kiến thức mới, hãy giải thích có cấu trúc, chi tiết, nêu ví dụ thực tế.
        - Luôn chủ động kết thúc câu trả lời bằng một câu hỏi gợi mở để khuyến khích người dùng học tiếp.

        **QUY TẮC ĐẶC BIỆT KHI ÔN TẬP (TOOL get_user_weaknesses):**
        Khi tool 'get_user_weaknesses' trả về dữ liệu, bạn phải đóng vai một gia sư chuyên nghiệp và tận tâm. Nhiệm vụ của bạn là biến dữ liệu thô đó thành một **BÀI GIẢNG MINI** chi tiết, chứ không phải một bản tóm tắt ngắn. Hãy tuân thủ nghiêm ngặt cấu trúc sau:

        1.  **Mở đầu thân thiện:** Bắt đầu bằng cách xác nhận rằng bạn sẽ giúp họ ôn lại những phần họ còn yếu. Ví dụ: "Chắc chắn rồi, chúng ta hãy cùng xem lại những khái niệm mà bạn còn hơi bối rối nhé."

        2.  **Đi sâu vào từng câu sai:** Với MỖI câu hỏi họ làm sai, hãy tuân thủ cấu trúc sau:
            a. **Nêu lại câu hỏi và đáp án đúng:** In đậm câu hỏi và đáp án. Ví dụ: "Ở câu hỏi **'What is overfitting in machine learning?'**, đáp án chính xác là **'When a model is too complex and learns noise in the data'**."
            b. **GIẢNG BÀI CHI TIẾT:** Đây là phần quan trọng nhất. Đừng chỉ lặp lại phần 'explanation' ngắn gọn từ tool. Hãy giải thích khái niệm đó một cách **cặn kẽ và chi tiết (tối thiểu 3-5 câu)**, như thể bạn đang giảng cho một người mới bắt đầu. Phân tích tại sao đáp án đó lại đúng.
            c. **Đưa ra Ví dụ hoặc Phép Tương Đồng (Analogy):** Cung cấp một ví dụ thực tế hoặc một phép so sánh dễ hiểu để minh họa cho khái niệm đó. Ví dụ: "Hãy tưởng tượng overfitting giống như một học sinh học thuộc lòng tất cả các bài văn mẫu, nhưng khi gặp một đề bài mới thì lại không thể viết được, vì bạn ấy chỉ nhớ 'nhiễu' chứ không hiểu 'quy luật'."

        3.  **Tổng kết và khuyến khích:** Sau khi đã phân tích hết các câu sai, hãy đưa ra một lời động viên và tóm tắt lại những gì họ cần chú ý.

        4.  **Câu hỏi gợi mở:** Luôn kết thúc bằng một câu hỏi để khuyến khích họ học sâu hơn. Ví dụ: "Sau khi xem lại, bạn có muốn tôi tạo một vài câu hỏi quiz khác chỉ tập trung vào chủ đề 'Overfitting' để kiểm tra lại không?"
        """
        
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("placeholder", "{chat_history}"), ("human", "{input}")])
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("placeholder", "{chat_history}"), ("human", "{input}")])
        llm_with_tools = llm.bind_tools(tools)
        chain = prompt | llm_with_tools

        history_cursor = chat_history_collection.find({ "session_id": session_id }).sort("timestamp", -1).limit(10)
        chat_history_for_prompt = [AIMessage(content=doc["content"]) if doc["role"] == "assistant" else HumanMessage(content=doc["content"]) for doc in reversed(list(history_cursor))]
        user_message_doc = { "session_id": session_id, "user_id": username, "role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc) }
        chat_history_collection.insert_one(user_message_doc)
        
        full_response_content = ""
        try:
            ai_response = await chain.ainvoke({"input": request.message, "chat_history": chat_history_for_prompt})
            
            if ai_response.tool_calls:
                tool_call = ai_response.tool_calls[0]
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                print(f"--- AI yêu cầu gọi tool: {tool_name} với tham số: {tool_args} ---")
                
                if tool_name == "tao_quiz":
                    questions_json_str = tao_quiz.func(**tool_args)
                    try:
                        questions_data = json.loads(questions_json_str)
                        if "error" in questions_data: raise ValueError("Tool đã trả về một lỗi.")
                        quiz_document = {"quiz_id": str(uuid4()), "user_id": username, "topic": tool_args.get("topic"), "questions": questions_data, "created_at": datetime.now(timezone.utc)}
                        quizzes_collection.insert_one(quiz_document)
                        full_response_content = f"Tôi đã tạo xong một bài quiz về '{tool_args.get('topic')}' cho bạn rồi. Bạn có thể vào mục 'Bài kiểm tra' để làm nhé!"
                    except Exception as e:
                        full_response_content = "Rất tiếc, đã có lỗi xảy ra trong quá trình tạo quiz."

                elif tool_name == "get_user_weaknesses":
                    tool_output = get_user_weaknesses_logic(user_id=username)
                    messages_for_second_call = chat_history_for_prompt + [HumanMessage(content=request.message), AIMessage(content="", tool_calls=[tool_call]), ToolMessage(content=tool_output, tool_call_id=tool_call['id'])]
                    
                    # <<< SỬA LỖI Ở ĐÂY: Thêm "input": "" vào lời gọi ainvoke thứ hai >>>
                    final_response = await chain.ainvoke({
                        "chat_history": messages_for_second_call,
                        "input": "" 
                    })
                    full_response_content = final_response.content
                
                elif tool_name == "tim_kiem_internet":
                    full_response_content = tim_kiem_internet.func(**tool_args)

            else:
                full_response_content = ai_response.content
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi chạy chain: {e}")
            full_response_content = "Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý."
            
        yield full_response_content
        
        if full_response_content:
            ai_message_doc = { "session_id": session_id, "user_id": username, "role": "assistant", "content": full_response_content, "timestamp": datetime.now(timezone.utc) }
            chat_history_collection.insert_one(ai_message_doc)
            if is_new_session:
                conversation_for_title = f"user: {request.message}\nassistant: {full_response_content}"
                new_title = await generate_session_title(conversation_for_title, llm)
                sessions_collection.update_one({ "session_id": session_id }, { "$set": { "title": new_title } })

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# --- 6. HELPER FUNCTIONS ---
async def generate_session_title(message_history: str, llm_instance: ChatOpenAI) -> str:
    # ... (code không đổi)
    prompt = f"Dựa trên đoạn hội thoại sau, hãy tạo ra một tiêu đề ngắn gọn (dưới 10 từ) và súc tích bằng tiếng Việt.\n\nĐoạn hội thoại:\n{message_history}\n\nTiêu đề của bạn:"
    try:
        response = await llm_instance.ainvoke(prompt)
        title = response.content if hasattr(response, 'content') else str(response)
        return title.strip().strip('"')
    except Exception as e:
        print(f"Lỗi khi tạo tiêu đề: {e}")
        return "Cuộc trò chuyện mới"