import streamlit as st
import streamlit.components.v1 as components

# Element Plus + Vue3 CDN Demo：按钮+输入框
vue_element_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>ElementPlus Demo</title>
  <!-- Vue3 CDN -->
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <!-- Element Plus CDN -->
  <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css">
  <script src="https://unpkg.com/element-plus/dist/index.full.js"></script>
</head>
<body>
  <div id="app">
    <el-input v-model="inputVal" placeholder="请输入内容"></el-input>
    <el-button type="primary" @click="sendData">提交</el-button>
  </div>
<script>
const { createApp } = Vue;
const { ElInput, ElButton } = ElementPlus;
const app = createApp({
  components:{ ElInput, ElButton },
  data(){
    return { inputVal: '' }
  },
  methods:{
    sendData(){
      // 把数据传回Streamlit
      window.parent.postMessage({type:'element_data', value: this.inputVal}, '*')
    }
  }
})
app.use(ElementPlus).mount('#app')
</script>
</body>
</html>
"""

st.title("Streamlit + ElementPlus CDN Demo")
# 渲染Vue页面，高度按需调整
return_val = components.html(vue_element_html, height=200)
st.write("前端返回数据：", return_val)
