# app.py - 完整的DeepSeek RAG助手（改进检索版）
import streamlit as st
import os
import requests
import PyPDF2
from docx import Document
import hashlib

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
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("""
<div class="main-header">
    <h1>📚 Simple RAG Assistant</h1>
    <p>基于DeepSeek的智能文档问答助手 | 上传文档，开始提问</p>
</div>
""", unsafe_allow_html=True)

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# 侧边栏
with st.sidebar:
    st.markdown("## 🔑 API设置")

    # DeepSeek API密钥输入
    api_key = st.text_input(
        "DeepSeek API密钥",
        type="password",
        placeholder="sk-...",
        help="在 https://platform.deepseek.com/ 获取",
        value=st.session_state.api_key
    )

    if api_key:
        st.session_state.api_key = api_key
        # 简单验证API密钥格式
        if api_key.startswith("sk-"):
            st.session_state.api_key_valid = True
            st.markdown("""
            <div class="success-box">
                ✅ API密钥已设置
            </div>
            """, unsafe_allow_html=True)
        else:
            st.session_state.api_key_valid = False
            st.markdown("""
            <div class="warning-box">
                ❌ API密钥格式不正确
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 📁 文档上传")

    # 文件上传
    uploaded_files = st.file_uploader(
        "选择文件（可多选）",
        type=['txt', 'pdf', 'docx', 'md', 'py', 'js', 'html', 'css', 'cpp', 'java', 'json', 'csv'],
        accept_multiple_files=True,
        help="支持多种格式：文本、PDF、Word、代码文件等"
    )

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.documents:
                try:
                    with st.spinner(f"正在处理 {file.name}..."):
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

                        # 分块处理（按段落）
                        chunks = [c.strip() for c in content.split('\n\n') if len(c.strip()) > 50]
                        if not chunks:  # 如果没有分段，按句子分
                            chunks = [c.strip() for c in content.split('。') if len(c.strip()) > 30]

                        # 如果还是没分块，按固定长度分
                        if not chunks:
                            chunk_size = 200
                            chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]

                        st.session_state.documents[file.name] = {
                            'content': content,
                            'chunks': chunks,
                            'type': file.name.split('.')[-1],
                            'size': len(content)
                        }
                        st.success(f"✅ 已加载: {file.name} ({len(chunks)}个段落)")
                except Exception as e:
                    st.error(f"❌ 读取失败 {file.name}: {str(e)}")

    # 已加载文档列表
    if st.session_state.documents:
        st.markdown("### 📋 已加载文档")
        for name in list(st.session_state.documents.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {name[:30]}...")
            with col2:
                if st.button("❌", key=f"del_{name}"):
                    del st.session_state.documents[name]
                    st.rerun()

    # 清空所有
    if st.session_state.documents and st.button("🗑️ 清空所有文档", use_container_width=True):
        st.session_state.documents = {}
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ 使用说明")
    st.info("""
    1. 输入DeepSeek API密钥
    2. 上传文档（支持多选）
    3. 在下方提问
    4. AI会基于文档内容回答
    """)

    st.markdown("### 🔗 链接")
    st.markdown("[GitHub仓库](https://github.com/rachelwhy/Simple-RAG-Assistant)")

# 主界面 - 左右两列
col1, col2 = st.columns([2, 1])

with col2:
    if st.session_state.documents:
        st.markdown("### 📊 文档统计")
        total_docs = len(st.session_state.documents)
        total_chunks = sum(len(info['chunks']) for info in st.session_state.documents.values())
        total_chars = sum(info['size'] for info in st.session_state.documents.values())

        # 显示统计信息
        st.metric("文档数量", total_docs)
        st.metric("文本段落", total_chunks)
        st.metric("总字符数", f"{total_chars:,}")

        # 文档类型分布
        if total_docs > 0:
            st.markdown("### 📑 文档类型")
            types = {}
            for info in st.session_state.documents.values():
                types[info['type']] = types.get(info['type'], 0) + 1
            for t, count in types.items():
                st.text(f"• {t}: {count}个")

with col1:
    st.markdown("### 💬 智能问答")

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ⚠️ 重要：chat_input 必须放在所有容器外面
if prompt := st.chat_input("请输入您的问题..."):
    # 检查API密钥
    if not st.session_state.get('api_key_valid', False):
        st.warning("⚠️ 请在左侧输入有效的DeepSeek API密钥")
    elif not st.session_state.documents:
        st.warning("⚠️ 请先在左侧上传文档")
    else:
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("🤔 DeepSeek正在思考..."):
                try:
                    # 1. 检索相关文档内容 - 改进版
                    relevant_chunks = []

                    # 把问题分词
                    prompt_words = prompt.lower().split()
                    # 去除常见停用词
                    stop_words = ['的', '了', '在', '是', '我', '你', '他', '这', '那', '和', '与', '或', '吗', '呢',
                                  '啊', '把', '被', '让', '给', '对', '对于', '关于']
                    prompt_words = [w for w in prompt_words if w not in stop_words and len(w) > 1]

                    # 如果没有有效关键词，就用原问题
                    if not prompt_words:
                        prompt_words = prompt.lower().split()

                    for name, info in st.session_state.documents.items():
                        for i, chunk in enumerate(info['chunks']):
                            chunk_lower = chunk.lower()
                            # 计算匹配分数
                            score = 0
                            matched_words = []
                            for word in prompt_words:
                                if word in chunk_lower:
                                    score += 1
                                    matched_words.append(word)

                            # 如果匹配到关键词，添加到结果
                            if score > 0:
                                # 计算匹配密度
                                density = score / len(prompt_words) if prompt_words else 0
                                relevant_chunks.append({
                                    'file': name,
                                    'content': chunk,
                                    'score': score,
                                    'density': density,
                                    'matched_words': matched_words,
                                    'chunk_id': i
                                })

                    # 按相关性排序（先按匹配词数，再按密度）
                    relevant_chunks.sort(key=lambda x: (x['score'], x['density']), reverse=True)
                    top_chunks = relevant_chunks[:5]  # 取前5个

                    # 构建上下文
                    if top_chunks:
                        context = "\n\n---\n\n".join([f"【来自文档: {c['file']}】\n{c['content']}"
                                                      for c in top_chunks])
                        # 显示找到的相关信息
                        st.markdown(f"""
                        <div class="info-box">
                            ℹ️ 找到 {len(top_chunks)} 个相关段落
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        context = "没有找到直接相关的文档内容"
                        st.markdown("""
                        <div class="info-box">
                            ℹ️ 在文档中没有找到与问题直接相关的内容，我将尝试让AI基于文档整体理解回答。
                        </div>
                        """, unsafe_allow_html=True)

                        # 如果没有匹配的，用整个文档作为上下文
                        all_content = []
                        for name, info in st.session_state.documents.items():
                            all_content.append(f"【文档: {name}】\n{info['content'][:1000]}")  # 只取前1000字
                        context = "\n\n---\n\n".join(all_content)

                    # 2. 构建提示词 - 改进版
                    system_prompt = """你是一个专业的文档问答助手。请严格基于提供的文档内容回答问题。

重要规则：
1. 首先仔细阅读用户上传的文档内容
2. 如果文档中有相关信息，请直接引用并详细回答
3. 如果文档中没有直接答案，但可以通过文档内容合理推断，请说明你的推理过程
4. 只有当文档内容完全不相关或完全没有信息时，才说"根据当前文档，我无法回答这个问题"
5. 回答要详细、准确、有条理，使用中文
6. 尽可能引用文档中的原话"""

                    user_prompt = f"""请仔细阅读以下文档内容，然后回答问题。

文档内容：
{context}

问题：{prompt}

请基于文档内容详细回答："""

                    # 3. 调用DeepSeek API
                    headers = {
                        "Authorization": f"Bearer {st.session_state.api_key}",
                        "Content-Type": "application/json"
                    }

                    data = {
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,  # 提高温度，让回答更灵活
                        "max_tokens": 3000,
                        "stream": False
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

                        # 添加引用来源
                        if top_chunks:
                            answer += "\n\n---\n"
                            answer += "📖 **参考来源**\n"
                            for i, chunk in enumerate(top_chunks[:3], 1):
                                file_name = chunk['file']
                                preview = chunk['content'][:150] + "..." if len(chunk['content']) > 150 else chunk[
                                    'content']
                                answer += f"{i}. **{file_name}**: {preview}\n\n"

                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"❌ API调用失败 (错误码: {response.status_code})"
                        try:
                            error_detail = response.json()
                            error_msg += f"\n详情: {error_detail}"
                        except:
                            pass
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

                except requests.exceptions.Timeout:
                    error_msg = "❌ API调用超时，请重试"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"❌ 发生错误: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# 底部
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    基于 DeepSeek API + Streamlit 构建 | 需要有效的API密钥
</div>
""", unsafe_allow_html=True)