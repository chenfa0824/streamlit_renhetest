import streamlit as st
import json

st.set_page_config(page_title="Streamlit + ElementPlus Demo", layout="wide")
st.title("Streamlit 集成 Element Plus Demo")

# 保存前端传回的数据
if "ep_result" not in st.session_state:
    st.session_state["ep_result"] = {}

# 【核心】Vue3 + ElementPlus HTML代码
HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ElementPlus Demo</title>
  <!-- CDN引入Vue3 + ElementPlus -->
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css">
  <script src="https://unpkg.com/element-plus/dist/index.full.js"></script>
  <!-- ElementPlus Icons -->
  <link rel="stylesheet" href="https://unpkg.com/@element-plus/icons-vue/dist/index.css" />
  <script src="https://unpkg.com/@element-plus/icons-vue/dist/index.iife.js"></script>
</head>
<body style="margin:0;padding:16px;background:#fff;">
<div id="app">
  <el-card header="ElementPlus表单组件" style="max-width:700px;">
    <el-form :model="form" label-width="80px">
      <el-form-item label="用户名">
        <el-input v-model="form.username" placeholder="请输入用户名"></el-input>
      </el-form-item>
      <el-form-item label="选择城市">
        <el-select v-model="form.city" placeholder="请选择">
          <el-option label="北京" value="beijing"></el-option>
          <el-option label="上海" value="shanghai"></el-option>
          <el-option label="武汉" value="wuhan"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="form.date" type="date" placeholder="选择日期"></el-date-picker>
      </el-form-item>
      <el-form-item label="开关">
        <el-switch v-model="form.enable"></el-switch>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm">提交到Streamlit</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>

    <el-divider></el-divider>
    <h4>表格示例</h4>
    <el-table :data="tableData" border stripe style="width:100%">
      <el-table-column prop="name" label="姓名"></el-table-column>
      <el-table-column prop="age" label="年龄"></el-table-column>
      <el-table-column prop="address" label="地址"></el-table-column>
    </el-table>
  </el-card>
</div>

<script>
const { createApp } = Vue
const { ElMessage } = ElementPlus
const app = createApp({
  setup() {
    const form = Vue.ref({
      username: '',
      city: '',
      date: '',
      enable: false
    })
    const tableData = Vue.ref([
      {name:'张三',age:22,address:'北京市'},
      {name:'李四',age:25,address:'上海市'},
      {name:'王五',age:28,address:'武汉市'},
    ])

    // 提交：postMessage发送数据给streamlit
    const submitForm = () => {
      const payload = {
        type: "ep_submit",
        data: form.value
      }
      window.parent.postMessage(payload, "*")
      ElMessage.success("数据已提交！")
    }
    const resetForm = () => {
      form.value = {username:'',city:'',date:'',enable:false}
    }
    return {form, tableData, submitForm, resetForm}
  }
})
app.use(ElementPlus)
app.mount('#app')

// 监听streamlit传回的数据（Python向前端传参）
window.addEventListener('message', (event)=>{
  if(event.data?.type === "set_form"){
    const newForm = event.data.data
    const vm = document.querySelector('#app').__vue_app._instance.exposed
    vm.form = newForm
  }
})
</script>
</body>
</html>
"""

# 渲染iframe内的ElementPlus页面
from streamlit import components
components.v1.html(
    HTML,
    height=720,
    scrolling=True
)

# ========== 监听前端postMessage消息（双向通信核心）==========
# 注意：streamlit components v1的消息监听需要使用session_state + 回调
# 简易方案：增加一个按钮触发读取，或者用streamlit-javascript监听
# 这里做简化：增加一个刷新按钮，模拟接收前端提交的数据
st.subheader("Python端接收结果")
if st.button("读取前端提交的数据"):
    st.json(st.session_state["ep_result"])

# 向前端发送数据（回填表单示例）
st.subheader("Python向前端回填表单")
fill_name = st.text_input("预填用户名", value="测试用户")
if st.button("发送数据到ElementPlus表单"):
    # 向iframe发送message
    components.v1.html(
        """
        <script>
        window.postMessage({
            type:"set_form",
            data:{
                username:"""+json.dumps(fill_name)+""",
                city:"wuhan",
                date:"2026-09-30",
                enable:true
            }
        }, "*")
        </script>
        """,
        height=0
    )
    st.success("已向前端表单回填数据")

# 展示说明
with st.expander("说明"):
    st.markdown("""
- 原理：`components.v1.html` 创建iframe嵌入Vue3+ElementPlus
- 双向通信：`postMessage` 在iframe和主页面之间传递JSON数据
- 优点：不用打包前端工程，一行CDN引入所有资源
- 缺点：iframe有独立上下文，样式隔离；复杂业务建议单独开发Vue组件包
""")
