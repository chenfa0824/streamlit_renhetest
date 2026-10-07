# ============================================================
# Pandas 数据可视化完整 Demo
# 场景：某公司 2023 年各区域/各产品销售数据分析
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- 0. 全局配置 ----------
plt.rcParams['font.sans-serif'] = ['SimHei']      # 中文字体（Mac 用 'Arial Unicode MS'）
plt.rcParams['axes.unicode_minus'] = False        # 负号正常显示
plt.rcParams['figure.dpi'] = 110                  # 图片清晰度
plt.rcParams['axes.grid'] = True                  # 默认显示网格
plt.rcParams['grid.alpha'] = 0.3

np.random.seed(42)  # 保证结果可复现


# ============================================================
# 1. 构造模拟数据
# ============================================================
months = pd.date_range('2023-01-01', periods=12, freq='MS')
regions = ['华东', '华北', '华南', '西南']
products = ['手机', '电脑', '平板', '耳机']

records = []
for m in months:
    for r in regions:
        for p in products:
            base = {'手机': 500, '电脑': 300, '平板': 200, '耳机': 150}[p]
            region_factor = {'华东': 1.5, '华北': 1.2, '华南': 1.3, '西南': 0.8}[r]
            season = 1 + 0.3 * np.sin((m.month - 1) / 12 * 2 * np.pi)  # 季节性波动
            sales = base * region_factor * season * np.random.uniform(0.85, 1.15)
            price = {'手机': 3500, '电脑': 6000, '平板': 2500, '耳机': 800}[p]
            records.append({
                '日期': m,
                '月份': m.strftime('%m月'),
                '区域': r,
                '产品': p,
                '销量': int(sales),
                '单价': price,
                '销售额': int(sales * price),
                '利润': int(sales * price * np.random.uniform(0.15, 0.35))
            })

df = pd.DataFrame(records)
print("数据规模：", df.shape)
print(df.head())


# ============================================================
# 2. 数据聚合（透视表）
# ============================================================
# 按月 × 产品 的销售额
pivot_month_product = df.pivot_table(
    index='月份', columns='产品', values='销售额', aggfunc='sum'
)

# 按区域 汇总
region_summary = df.groupby('区域').agg(
    销售额=('销售额', 'sum'),
    利润=('利润', 'sum'),
    销量=('销量', 'sum')
).sort_values('销售额', ascending=False)

# 按月 汇总（用于趋势）
month_summary = df.groupby('日期').agg(
    销售额=('销售额', 'sum'),
    利润=('利润', 'sum')
).reset_index()


# ============================================================
# 3. 大屏多子图布局
# ============================================================
fig = plt.figure(figsize=(16, 12))
fig.suptitle('2023 年度销售数据分析看板', fontsize=20, fontweight='bold', y=0.98)

# ---------- 图1：折线图 - 月度销售额 & 利润趋势 ----------
ax1 = fig.add_subplot(3, 3, (1, 2))  # 占第1行前两格
ax1.plot(month_summary['日期'], month_summary['销售额'],
         marker='o', linewidth=2, color='#4C72B0', label='销售额')
ax1.plot(month_summary['日期'], month_summary['利润'],
         marker='s', linewidth=2, color='#DD8452', label='利润')
ax1.fill_between(month_summary['日期'], month_summary['销售额'], alpha=0.15, color='#4C72B0')
ax1.set_title('月度销售额与利润趋势', fontsize=13)
ax1.set_ylabel('金额（元）')
ax1.legend()
ax1.tick_params(axis='x', rotation=45)

# ---------- 图2：饼图 - 各产品销售额占比 ----------
ax2 = fig.add_subplot(3, 3, 3)
product_share = df.groupby('产品')['销售额'].sum()
ax2.pie(product_share, labels=product_share.index, autopct='%1.1f%%',
        startangle=90, colors=['#4C72B0', '#DD8452', '#55A868', '#C44E52'],
        wedgeprops={'edgecolor': 'white', 'linewidth': 2})
ax2.set_title('各产品销售额占比', fontsize=13)

# ---------- 图3：分组柱状图 - 各区域各产品销售额 ----------
ax3 = fig.add_subplot(3, 3, (4, 5))
pivot_region_product = df.pivot_table(
    index='区域', columns='产品', values='销售额', aggfunc='sum'
)
pivot_region_product.plot(kind='bar', ax=ax3, width=0.8, colormap='Set2')
ax3.set_title('各区域 × 各产品销售额', fontsize=13)
ax3.set_xlabel('')
ax3.set_ylabel('销售额（元）')
ax3.tick_params(axis='x', rotation=0)
ax3.legend(title='产品', fontsize=9)

# ---------- 图4：堆叠面积图 - 月度产品结构 ----------
ax4 = fig.add_subplot(3, 3, 6)
pivot_month_product.plot(kind='area', stacked=True, ax=ax4,
                         colormap='Spectral', alpha=0.85)
ax4.set_title('月度产品结构（堆叠）', fontsize=13)
ax4.set_xlabel('')
ax4.set_ylabel('销售额')
ax4.legend(fontsize=8, loc='upper left')

# ---------- 图5：直方图 - 单笔订单销量分布 ----------
ax5 = fig.add_subplot(3, 3, 7)
ax5.hist(df['销量'], bins=30, color='#55A868', edgecolor='white')
ax5.axvline(df['销量'].mean(), color='red', linestyle='--',
            label=f"均值={df['销量'].mean():.0f}")
ax5.set_title('销量分布直方图', fontsize=13)
ax5.set_xlabel('销量')
ax5.set_ylabel('频次')
ax5.legend()

# ---------- 图6：箱线图 - 各产品销售额分布 ----------
ax6 = fig.add_subplot(3, 3, 8)
df.boxplot(column='销售额', by='产品', ax=ax6,
           patch_artist=True,
           boxprops=dict(facecolor='#4C72B0', alpha=0.6))
ax6.set_title('各产品销售额箱线图', fontsize=13)
ax6.set_xlabel('')
ax6.set_ylabel('销售额')
plt.sca(ax6)
plt.title('各产品销售额箱线图', fontsize=13)
plt.suptitle('')  # 去掉 pandas 默认的标题

# ---------- 图7：散点图 - 销量 vs 销售额 ----------
ax7 = fig.add_subplot(3, 3, 9)
colors_map = {'手机': '#4C72B0', '电脑': '#DD8452', '平板': '#55A868', '耳机': '#C44E52'}
for prod, group in df.groupby('产品'):
    ax7.scatter(group['销量'], group['销售额'],
                s=18, alpha=0.5, label=prod, color=colors_map[prod])
ax7.set_title('销量 vs 销售额', fontsize=13)
ax7.set_xlabel('销量')
ax7.set_ylabel('销售额')
ax7.legend(fontsize=8)

plt.tight_layout(rect=[0, 0, 1, 0.96])  # 给大标题留空间
plt.savefig('sales_dashboard.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================
# 4. 单独绘制：相关性热力图（用 matplotlib 实现，无需 seaborn）
# ============================================================
fig2, ax = plt.subplots(figsize=(6, 5))
corr = df[['销量', '单价', '销售额', '利润']].corr()
im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
ax.set_xticks(range(len(corr)))
ax.set_yticks(range(len(corr)))
ax.set_xticklabels(corr.columns)
ax.set_yticklabels(corr.columns)
# 数值标注
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                ha='center', va='center', color='black', fontsize=11)
ax.set_title('指标相关性热力图', fontsize=14)
fig2.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout()
plt.show()


# ============================================================
# 5. 交互式图表（可选，需要 pip install plotly）
# ============================================================
try:
    import plotly.express as px

    fig3 = px.line(
        month_summary, x='日期', y=['销售额', '利润'],
        title='交互式月度趋势（Plotly）',
        markers=True
    )
    fig3.write_html('interactive_trend.html')
    print("✅ 交互式图表已保存为 interactive_trend.html")
except ImportError:
    print("ℹ️ 未安装 plotly，跳过交互式图表。可执行: pip install plotly")


# ============================================================
# 6. 输出文字分析结论
# ============================================================
print("\n" + "=" * 50)
print("📊 数据分析结论")
print("=" * 50)
print(f"全年总销售额：{df['销售额'].sum():,.0f} 元")
print(f"全年总利润：  {df['利润'].sum():,.0f} 元")
print(f"平均利润率：  {df['利润'].sum() / df['销售额'].sum() * 100:.1f}%")
print(f"\n销售冠军区域：{region_summary.index[0]}（{region_summary.iloc[0]['销售额']:,.0f} 元）")
print(f"最畅销产品：  {product_share.idxmax()}（{product_share.max():,.0f} 元）")
print(f"销售额最高月份：{month_summary.loc[month_summary['销售额'].idxmax(), '日期'].strftime('%Y-%m')}")