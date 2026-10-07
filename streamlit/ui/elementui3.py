import streamlit as st

# 注册一个内联组件
element_button = st.components.v2.component(
    name="element_plus_button",
    html="""
    <!-- 引入 Element Plus 的样式和 Vue -->
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <script src="https://unpkg.com/vue@3"></script>
    <script src="https://unpkg.com/element-plus"></script>

    <div id="app">
      <el-button type="primary" @click="handleClick">点击我</el-button>
    </div>
    """,
    js="""
    export default function ({ parentElement, setTriggerValue }) {
        const { createApp } = Vue;
        const { ElButton } = ElementPlus;

        const app = createApp({
            methods: {
                handleClick() {
                    // 触发事件，通知 Python 端
                    setTriggerValue("clicked", true);
                }
            }
        });
        app.use(ElementPlus);
        app.component('el-button', ElButton);
        app.mount(parentElement.querySelector('#app'));
    }
    """
)

# 在应用中使用
result = element_button(on_clicked_change=lambda: print("按钮被点击了"))