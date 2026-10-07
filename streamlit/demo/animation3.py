import streamlit as st

css_anim = """
<style>
@keyframes breathe {
  0% { transform: scale(1); opacity:0.8; }
  50% { transform: scale(1.02); opacity:1; }
  100% { transform: scale(1); opacity:0.8; }
}
.breathe-box{
  padding:20px;
  background:#e8f4ff;
  border-radius:12px;
  animation: breathe 2s infinite ease-in-out;
}
</style>
<div class="breathe-box">
  🌀 呼吸动画卡片
</div>
"""
st.html(css_anim)
