import pandas as pd
import os

# 1. Đọc dữ liệu GỐC (TOTAL)
df = pd.read_csv("data/processed/Ligue_1_TOTAL_STATS.csv", index_col=0)

# 2. KHAI BÁO VÙNG CẤM (Các cột không bao giờ được phép chia)
# Bao gồm: Thông tin định danh và các mốc thời gian gốc
cols_to_ignore = [
    'Player ID', 'League', 'Team', 'Name', 'Position', 'Sofascore Rating',
    'Appearances', 'Started', 'Minutes played'
]

# 3. TỰ ĐỘNG QUÉT TÌM CÁC CỘT CẦN CHIA 
# Điều kiện: Cột không nằm trong 'vùng cấm' VÀ tên cột không chứa dấu '%' VÀ không chứa chữ 'Percentage'
cols_to_divide = [
    col for col in df.columns 
    if col not in cols_to_ignore 
    and '%' not in col 
    and 'Percentage' not in col
]

# =========================================================
# TẠO BẢN PER MATCH (Chỉ chia những cột nằm trong cols_to_divide)
# =========================================================
df_perMatch = df.copy()
df_perMatch = df_perMatch[df_perMatch['Appearances'] > 0] # Lọc người có đá để tránh lỗi chia cho 0

for col in cols_to_divide:
    df_perMatch[col] = round(df_perMatch[col] / df_perMatch['Appearances'], 2)

# Các cột % (như "Goal conversion %") sẽ tự động ĐƯỢC BÊ NGUYÊN XI từ df gốc sang df_perMatch
df_perMatch.to_csv("data/processed/Ligue_1_PERMATCH_STATS.csv")
print("✅ Đã tạo xong bản Per Match (Giữ nguyên các cột %)")

# =========================================================
# TẠO BẢN PER 90 MINS
# =========================================================
df_per90 = df.copy()
df_per90 = df_per90[df_per90['Minutes played'] >= 90] # Lọc người đá tối thiểu 90 phút

for col in cols_to_divide:
    df_per90[col] = round((df_per90[col] / df_per90['Minutes played']) * 90, 2)

df_per90.to_csv("data/processed/Ligue_1_PER90_STATS.csv")
print("✅ Đã tạo xong bản Per 90 (Giữ nguyên các cột %)")