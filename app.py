# app.py (ở thư mục gốc)
import streamlit as st
from src.retriever import search
from src.generator import generate_answer

st.set_page_config(page_title="RAG Luật Lao Động", page_icon="📚")
st.title("📚 Chatbot Luật Lao Động 2019")

# Lưu lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Hỏi về luật lao động..."):
    # Hiện câu hỏi
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Xử lý
    with st.chat_message("assistant"):
        with st.spinner("Đang tra cứu..."):
            contexts = search(prompt, top_k=5)
            answer, status = generate_answer(prompt, contexts)  

            st.markdown(answer)

            # Chỉ in nguồn khi thành công và trong domain
            #if status == "ok":
            with st.expander("📖 Nguồn tham khảo"):
                    seen = set()
                    for ctx in contexts:
                        label = f"{ctx.get('article', '')} - {ctx.get('title', '')}"
                        if label not in seen:
                            st.write(f"• {label}")
                            seen.add(label)

    st.session_state.messages.append({"role": "assistant", "content": answer})