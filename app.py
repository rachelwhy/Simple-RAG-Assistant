# app.py - 稳定版DeepSeek RAG助手
import streamlit as st
import requests
import PyPDF2
from docx import Document
import io

# 页面配置
st.set_page_config(
    page_title="Simple RAG Assistant",
    page_icon="📚",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .chat-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .assistant-message {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    .stButton > button {
        border-radius: 20px;
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False

# 标题
st.markdown("""
<div class="main-header">
    <h1>📚 Simple RAG Assistant</h1>
    <p>上传文档，智能问答 | 基于DeepSeek API</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("🔑 API设置")

    # API密钥输入
    api_key_input = st.text_input(
        "DeepSeek API密钥",
        type="password",
        placeholder="sk-...",
        help="在 platform.deepseek.com 获取",
        value=st.session_state.api_key
    )

    if api_key_input:
        st.session_state.api_key = api_key_input
        if api_key_input.startswith("sk-"):
            st.session_state.api_key_valid = True
            st.success("✅ API密钥已设置")
        else:
            st.session_state.api_key_valid = False
            st.error("❌ API密钥格式不正确")

    st.divider()

    # 文档上传
    st.header("📁 文档上传")
    uploaded_files = st.file_uploader(
        "选择文件",
        type=['txt', 'pdf', 'docx', 'md', 'py', 'js', 'html', 'css', 'cpp', 'java'],
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.documents:
                try:
                    # 读取文件内容
                    if file.name.endswith('.pdf'):
                        pdf_reader = PyPDF2.PdfReader(file)
                        content = ""
                        for page in pdf_reader.pages:
                            content += page.extract_text() + "\n"
                    elif file.name.endswith('.docx'):
                        doc = Document(file)
                        content = "\n".join([p.text for p in doc.paragraphs])
                    else:
                        content = file.getvalue().decode('utf-8', errors='ignore')

                    # 分块处理
                    chunks = []
                    paragraphs = content.split('\n\n')
                    for p in paragraphs:
                        if len(p.strip()) > 50:
                            chunks.append(p.strip())

                    # 如果段落太少，按句子分
                    if len(chunks) < 3:
                        sentences = content.replace('\n', ' ').split('。')
                        chunks = [s.strip() + '。' for s in sentences if len(s.strip()) > 30]

                    st.session_state.documents[file.name] = {
                        'content': content,
                        'chunks': chunks
                    }
                    st.success(f"✅ {file.name} ({len(chunks)}段)")
                except Exception as e:
                    st.error(f"❌ {file.name}: {str(e)}")

    # 文档列表
    if st.session_state.documents:
        st.divider()
        st.header("📋 已加载文档")
        for name in list(st.session_state.documents.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {name[:30]}")
            with col2:
                if st.button("❌", key=f"del_{name}"):
                    del st.session_state.documents[name]
                    st.rerun()

    # 清空按钮
    if st.session_state.documents and st.button("🗑️ 清空所有", use_container_width=True):
        st.session_state.documents = {}
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.info("""
    **使用说明**:
    1. 输入DeepSeek API密钥
    2. 上传文档
    3. 在下方提问
    """)

# 主界面
st.header("💬 智能问答")

# 显示聊天历史
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <b>👤 你:</b><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <b>🤖 AI:</b><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)

# 输入框和按钮
col1, col2 = st.columns([5, 1])
with col1:
    question = st.text_input("", placeholder="请输入您的问题...", label_visibility="collapsed")
with col2:
    send_button = st.button("发送", type="primary", use_container_width=True)

# 处理提问
if send_button and question:
    # 验证
    if not st.session_state.api_key_valid:
        st.error("请先设置有效的API密钥")
    elif not st.session_state.documents:
        st.error("请先上传文档")
    else:
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": question})

        # 检索相关文档
        relevant_chunks = []
        question_lower = question.lower()
        keywords = [w for w in question_lower.split() if len(w) > 1]

        for name, info in st.session_state.documents.items():
            for chunk in info['chunks']:
                chunk_lower = chunk.lower()
                score = sum(1 for word in keywords if word in chunk_lower)
                if score > 0:
                    relevant_chunks.append({
                        'file': name,
                        'content': chunk,
                        'score': score
                    })

        # 排序
        relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
        top_chunks = relevant_chunks[:3]

        # 构建上下文
        if top_chunks:
            context = "\n\n---\n\n".join([f"【{c['file']}】\n{c['content']}" for c in top_chunks])
        else:
            # 如果没有匹配，用整个文档
            context = "\n\n---\n\n".join([f"【{name}】\n{info['content'][:1000]}"
                                          for name, info in st.session_state.documents.items()])

        # 调用API
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.api_key}",
                "Content-Type": "application/json"
            }

            system_prompt = """你是一个专业的文档问答助手。请基于提供的文档内容回答问题。
如果文档中有相关信息，请详细回答。如果文档中没有相关信息，请说"根据当前文档，我无法回答这个问题"。
回答要准确、简洁。"""

            user_prompt = f"""文档内容：
{context}

问题：{question}

请回答："""

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']

                # 添加来源
                if top_chunks:
                    answer += "\n\n---\n📖 **参考来源**"
                    for c in top_chunks[:2]:
                        preview = c['content'][:100] + "..."
                        answer += f"\n• {c['file']}: {preview}"

                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                error_msg = f"API错误: {response.status_code}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

            st.rerun()

        except Exception as e:
            error_msg = f"错误: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

# 底部
st.divider()
st.caption("基于 DeepSeek API 构建 | 需要有效的API密钥")