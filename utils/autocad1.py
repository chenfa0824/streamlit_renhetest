from pyautocad import Autocad, APoint

# 连接或创建 AutoCAD 实例
acad = Autocad(create_if_not_exists=True)
acad.prompt("Hello, AutoCAD from Python\n")
print(f"当前图纸: {acad.doc.Name}")

# 绘制一条直线
p1 = APoint(0, 0)
p2 = APoint(100, 50)
line = acad.model.AddLine(p1, p2)
line.Color = 1  # 红色

# 绘制一个圆
center = APoint(50, 50)
circle = acad.model.AddCircle(center, 25)

# 添加文字
text = acad.model.AddText("自动生成", APoint(10, 10), 5)