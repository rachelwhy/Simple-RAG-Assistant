# app.py - 整文档上下文版（最通用）
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
    .user-message {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        border-radius: 15px 15px 0 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border: 1px solid #e0e0e0;
        border-radius: 15px 15px 15px 0;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .message-role {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #333333;
    }
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        color: #000000;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
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
    st.markdown("## 🔑 API设置")

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
            st.markdown("""
            <div class="success-box">
                ✅ API密钥已设置
            </div>
            """, unsafe_allow_html=True)
        else:
            st.session_state.api_key_valid = False
            st.markdown("""
            <div class="error-box">
                ❌ API密钥格式不正确
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 文档上传
    st.markdown("## 📁 文档上传")
    uploaded_files = st.file_uploader(
        "选择文件",
        type=['txt', 'pdf', 'docx', 'md', 'py', 'js', 'html', 'css', 'cpp', 'java'],
        accept_multiple_files=True,
        label_visibility="collapsed"
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

                    st.session_state.documents[file.name] = {
                        'content': content,
                        'type': file.name.split('.')[-1],
                        'size': len(content)
                    }
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ {file.name} ({len(content)}字符)
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        ❌ {file.name}: {str(e)}
                    </div>
                    """, unsafe_allow_html=True)

    # 文档列表
    if st.session_state.documents:
        st.markdown("---")
        st.markdown("## 📋 已加载文档")
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

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <b>📖 使用说明</b><br>
        1. 输入DeepSeek API密钥<br>
        2. 上传文档<br>
        3. 在下方提问<br>
        4. AI会阅读整个文档回答
    </div>
    """, unsafe_allow_html=True)

# 主界面
st.markdown("## 💬 智能问答")

# 显示聊天历史
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <div class="message-role">👤 你</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <div class="message-role">🤖 AI助手</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

# 输入区域
col1, col2 = st.columns([5, 1])
with col1:
    question = st.text_input(
        "",
        placeholder="请输入您的问题...",
        label_visibility="collapsed",
        key="question_input"
    )
with col2:
    send_button = st.button("发送", type="primary", use_container_width=True)

# 处理提问
if send_button and question:
    # 验证
    if not st.session_state.api_key_valid:
        st.markdown("""
        <div class="error-box">
            ❌ 请先设置有效的API密钥
        </div>
        """, unsafe_allow_html=True)
    elif not st.session_state.documents:
        st.markdown("""
        <div class="error-box">
            ❌ 请先上传文档
        </div>
        """, unsafe_allow_html=True)
    else:
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": question})

        # 生成回答
        with st.spinner("🤔 AI正在阅读文档并思考..."):
            try:
                # 1. 把所有文档内容合并成一个大上下文
                full_context = ""
                for name, info in st.session_state.documents.items():
                    # 限制每个文档长度，避免超过token限制（DeepSeek 128K上下文）
                    content = info['content'][:30000]  # 每个文档最多取3万字
                    full_context += f"\n\n【文档：{name}】\n{content}"

                # 如果总长度太长，截断
                if len(full_context) > 100000:
                    full_context = full_context[:100000] + "...（文档过长已截断）"

                # 2. 调用DeepSeek API
                headers = {
                    "Authorization": f"Bearer {st.session_state.api_key}",
                    "Content-Type": "application/json"
                }

                system_prompt = """你是一个专业的文档分析助手。请基于提供的文档内容回答问题。

重要规则：
1. 仔细阅读所有文档内容，理解每个文档的主题和关键信息
2. 根据用户的问题，从文档中找出相关信息并回答
3. 如果文档中有相关内容，请详细回答并注明信息来源（哪个文档）
4. 如果文档中没有相关信息，请明确说"根据当前文档，我无法回答这个问题"
5. 回答要准确、具体、有条理"""

                user_prompt = f"""请阅读以下所有文档，然后回答问题。

文档内容：
{full_context}

问题：{question}

请基于以上文档内容回答："""

                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                }

                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']

                    # 添加提示信息
                    answer += "\n\n---\n💡 *回答基于您上传的所有文档*"

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"API错误: {response.status_code}"
                    if response.status_code == 413:
                        error_msg = "文档过长，请减少上传的文档数量或大小"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

                st.rerun()

            except Exception as e:
                error_msg = f"错误: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                st.rerun()

# 底部
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666666; padding: 1rem;'>
    基于 DeepSeek API + Streamlit 构建 | 直接阅读整文档，无需检索
</div>
""", unsafe_allow_html=True)