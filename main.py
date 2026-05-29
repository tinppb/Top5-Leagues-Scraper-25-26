import subprocess
import sys
import time

# ==========================================
# 1. TỪ ĐIỂN TOP 5 GIẢI ĐẤU CÁC MÙA (25/26, 24/25, 23/24)
# ==========================================
TOP_5_LEAGUES = {
    "Premier_League": ("17", {"25_26": "76986", "24_25": "61627", "23_24": "52186"}),
    "La_Liga": ("8", {"25_26": "77559", "24_25": "61643", "23_24": "52376"}),
    "Serie_A": ("23", {"25_26": "76457", "24_25": "63515", "23_24": "52760"}),     
    "Bundesliga": ("35", {"25_26": "77333", "24_25": "63516", "23_24": "52608"}),  
    "Ligue_1": ("34", {"25_26": "77356", "24_25": "61736", "23_24": "52571"})      
}

def main():
    # Nhận kiểu thống kê từ Terminal. Nếu không gõ gì, MẶC ĐỊNH sẽ là per90
    acc_type = sys.argv[1] if len(sys.argv) > 1 else "per90"

    # Kiểm tra xem người dùng gõ lệnh có chuẩn không
    if acc_type not in ["total", "perMatch", "per90"]:
        print(f"❌ Kiểu thống kê '{acc_type}' không hợp lệ!")
        print("👉 Vui lòng chọn một trong các kiểu: total, perMatch, per90")
        sys.exit()

    print("="*60)
    print(f"🤖 PIPELINE: BẮT ĐẦU CÀO DỮ LIỆU {acc_type.upper()} CHO 5 GIẢI ĐẤU")
    print("="*60)

    total_tasks = len(TOP_5_LEAGUES) * 3
    current_task = 1

    # ==========================================
    # 2. VÒNG LẶP ĐIỀU PHỐI CÁC GIẢI ĐẤU
    # ==========================================
    for league_name, (tour_id, seasons) in TOP_5_LEAGUES.items():
        for season_name, season_id in seasons.items():
            print(f"\n[{current_task}/{total_tasks}] Tiến trình: {league_name} | Mùa: {season_name} | Chế độ: {acc_type.upper()}...")
            
            # Cấu trúc lệnh gửi đi: python crawler/full_stats.py [Giải] [TourID] [SeasonID] [per90/total/perMatch] [SeasonName]
            command = [
                sys.executable, 
                "crawler/full_stats.py", 
                league_name, 
                tour_id, 
                season_id, 
                acc_type,
                season_name
            ]
            
            try:
                # Kích hoạt file phụ bếp chạy
                subprocess.run(command, check=True)
                print(f"✅ Hoàn thành xuất sắc giải: {league_name} (Mùa {season_name})!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Gặp lỗi khi đang xử lý giải {league_name} (Mùa {season_name}): {e}")
                
            # Thời gian nghỉ giãn cách giữa các giải đấu để an toàn cho IP của bạn
            if current_task < total_tasks:
                print("⏳ Đang nghỉ 8 giây để làm mát Server...")
                time.sleep(8)
                
            current_task += 1

    print("\n" + "="*60)
    print(f"🎉 CHIẾN DỊCH HOÀN TẤT! TOÀN BỘ FILE _{acc_type.upper()} ĐÃ NẰM TRONG DATA/PROCESSED/ 🎉")
    print("="*60)

if __name__ == "__main__":
    main()