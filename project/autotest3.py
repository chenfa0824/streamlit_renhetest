import streamlit as st
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from playwright.async_api import async_playwright

# ======================
# 页面配置
# ======================
st.set_page_config(page_title="MCP 黑科技：AI 操控浏览器", page_icon="🌐", layout="wide")
st.title("🌐 MCP 黑科技 · 自然语言指挥 AI 操作浏览器")
st.markdown("### 只需一句话，AI 自动帮你操作浏览器！")

# ======================
# LLM 配置（换成你的 Key）
# ======================
llm = ChatOpenAI(
    model="qwen3.5-plus",
    api_key="sk-2f1fbbaaa47840bbaba328c5e5f3659b",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1
)

# ======================
# MCP 核心：浏览器自动化工具
# ======================
browser = None
page = None


@tool
async def open_url(url: str):
    """打开指定网页"""
    global browser, page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(url)
    return f"已打开：{url}"


@tool
async def click(selector: str):
    """点击元素（CSS选择器）"""
    await page.click(selector)
    return f"已点击：{selector}"


@tool
async def input_text(selector: str, text: str):
    """输入文本"""
    await page.fill(selector, text)
    return f"已输入：{text} → {selector}"


@tool
async def get_text(selector: str):
    """获取文本"""
    text = await page.text_content(selector)
    return f"获取文本：{text}"


@tool
async def screenshot():
    """截图"""
    await page.screenshot(path="screenshot.png")
    return "已截图保存：screenshot.png"


@tool
async def close_browser():
    """关闭浏览器"""
    await browser.close()
    return "浏览器已关闭"


tools = [open_url, click, input_text, get_text, screenshot, close_browser]

# ======================
# MCP 智能体
# ======================
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是浏览器自动化专家，用自然语言指挥操作浏览器，严格调用工具。"),
    ("user", "{input}"),
    ("agent_scratchpad", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ======================
# 界面交互
# ======================
st.divider()
user_command = st.text_input("💬 输入自然语言指令（AI 自动操作浏览器）",
                             placeholder="例如：打开百度，搜索 人工智能，点击第一个结果，截图")

if st.button("🚀 执行 AI 指令", type="primary"):
    if not user_command:
        st.warning("请输入指令！")
    else:
        with st.spinner("🧠 AI 正在执行浏览器操作..."):
            result = asyncio.run(agent_executor.ainvoke({"input": user_command}))
            st.success("✅ 指令执行完成！")
            st.markdown(f"### 执行结果：\n{result['output']}")

            try:
                st.image("screenshot.png", caption="AI 操作截图")
            except:
                pass

st.divider()
st.markdown("""
### 📌 支持指令示例（直接复制使用）：
1. 打开百度，搜索 人工智能，点击第一个链接，截图
2. 打开 github.com，搜索 streamlit，获取第一条结果标题
3. 打开 豆瓣电影，搜索 奥本海默，获取评分
4. 打开 淘宝，搜索 手机，截图页面
""")

st.caption("✅ 基于 MCP + LangChain + Playwright + AI 浏览器自动化黑科技")
