import pandas as pd

# 读取Excel文件，跳过前两行，读取数据部分
# 表头优化，取消合并单元格
file_path = "1.xlsx"

# 先读取前两行，获取原始列名
df_header = pd.read_excel(file_path, header=None, nrows=2)

# 读取数据（从第3行开始）
df_data = pd.read_excel(file_path, header=None, skiprows=2)

# 构建新列名
new_columns = []
for col_idx in range(df_header.shape[1]):
    val_row1 = df_header.iloc[0, col_idx]
    val_row2 = df_header.iloc[1, col_idx]

    # 如果第一行或第二行是NaN，用另一个填充
    if pd.isna(val_row1) and pd.isna(val_row2):
        new_columns.append(f"Unnamed_{col_idx}")
    elif pd.isna(val_row2):
        # 第二行为空 → 保留第一行（合并单元格场景）
        new_columns.append(str(val_row1))
    else:
        # 第二行有值 → 使用第二行
        new_columns.append(str(val_row2))

# 去重处理：如果列名重复，追加序号
seen = {}
for i, col in enumerate(new_columns):
    if col in seen:
        seen[col] += 1
        new_columns[i] = f"{col}_{seen[col]}"
    else:
        seen[col] = 0

# 替换列名
df_data.columns = new_columns

# 删除全为空的行和列（可选）
df_data.dropna(how='all', axis=0, inplace=True)
df_data.dropna(how='all', axis=1, inplace=True)

# 保存为新文件
output_path = "1_处理后.xlsx"
df_data.to_excel(output_path, index=False)

print(f"处理完成！文件已保存为: {output_path}")