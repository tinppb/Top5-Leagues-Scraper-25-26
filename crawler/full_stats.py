import sys
import os
import json
import time
import pandas as pd
from curl_cffi import requests

# ==========================================
# 1. CẤU HÌNH THÔNG SỐ GIẢI ĐẤU
# ==========================================
league_name = sys.argv[1] if len(sys.argv) > 1 else "Premier_League"
tour_id = sys.argv[2] if len(sys.argv) > 2 else "17"
season_id = sys.argv[3] if len(sys.argv) > 3 else "76986"

print(f"\n🚀 Đang khởi động cào TẤT CẢ CHỈ SỐ cho giải: {league_name.replace('_', ' ')}...")

url = f"https://www.sofascore.com/api/v1/unique-tournament/{tour_id}/season/{season_id}/statistics"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
}

limit = 20
all_rows = []

os.makedirs("data/raw/full_stats", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# TỪ ĐIỂN VỊ TRÍ ĐỂ CHẠY VÒNG LẶP
POSITIONS = {
    "G": "Goalkeeper",
    "D": "Defender",
    "M": "Midfielder",
    "F": "Forward"
}

# ==========================================
# 2. VÒNG LẶP CÀO DỮ LIỆU (CHIA THEO TỪNG VỊ TRÍ)
# ==========================================
for pos_code, pos_name in POSITIONS.items():
    print(f"\n👉 Bắt đầu quét nhóm cầu thủ: {pos_name}...")
    offset = 0
    
    while True:
        print(f"   Đang tải trang dữ liệu {pos_name} (Offset: {offset})...")
        
        params = {
            "limit": limit,
            "offset": offset,
            "order": "-rating", 
            "accumulation": "total",
            "filters": f"position.in.{pos_code}", # <--- TUYỆT CHIÊU: ÉP LỌC VỊ TRÍ TỪ SERVER
            "fields": "goals,successfulDribblesPercentage,outfielderBlocks,penaltyWon,goalsFromOutsideTheBox,hitWoodwork,expectedGoals,totalShots,goalConversionPercentage,shotFromSetPiece,headedGoals,offsides,bigChancesMissed,shotsOnTarget,penaltiesTaken,freeKickGoal,leftFootGoals,penaltyConversion,successfulDribbles,shotsOffTarget,penaltyGoals,goalsFromInsideTheBox,rightFootGoals,setPieceConversion,tackles,errorLeadToGoal,cleanSheet,interceptions,errorLeadToShot,penaltyConceded,ownGoals,clearances,dribbledPast,bigChancesCreated,totalPasses,accurateFinalThirdPasses,accurateLongBalls,assists,accuratePassesPercentage,keyPasses,accurateLongBallsPercentage,accuratePasses,accurateOwnHalfPasses,accurateCrosses,passToAssist,inaccuratePasses,accurateOppositionHalfPasses,accurateCrossesPercentage,yellowCards,aerialDuelsWon,minutesPlayed,possessionLost,redCards,aerialDuelsWonPercentage,wasFouled,appearances,groundDuelsWon,totalDuelsWon,fouls,matchesStarted,groundDuelsWonPercentage,totalDuelsWonPercentage,dispossessed,rating"
        }

        try:
            response = requests.get(url, headers=headers, params=params, impersonate="chrome124")
            
            if response.status_code != 200:
                print(f"❌ Lỗi {response.status_code}. Dừng cào.")
                break
                
            data = response.json()
            
            # Lưu Backup JSON thô
            raw_filepath = f"data/raw/full_stats/{league_name}_{pos_name}_offset_{offset}.json"
            with open(raw_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            players = data.get("results", [])
            
            if not players: 
                break # Hết cầu thủ ở vị trí này thì thoát vòng lặp while, chuyển sang vị trí tiếp theo
                
            # ==========================================
            # 3. BÓC TÁCH VÀ GẮN NHÃN DỮ LIỆU
            # ==========================================
            for p in players:
                player_info = p.get("player", {})
                team_info = p.get("team", {})
                stats = p
                
                all_rows.append({
                    "Player ID": player_info.get("id"),
                    "League": league_name.replace("_", " "),
                    "Team": team_info.get("name"),
                    "Name": player_info.get("name"),
                    
                    # VÌ TA ĐÃ LỌC TỪ REQUEST, TA BIẾT CHẮC CHẮN VỊ TRÍ LÀ GÌ MÀ KHÔNG CẦN TÌM:
                    "Position": pos_name, 
                    
                    "Sofascore Rating": stats.get("rating", 0),
                    
                    # --- Nhóm Attack ---
                    "Goals": stats.get("goals", 0),
                    "xG": stats.get("expectedGoals", 0),
                    "Big chances missed": stats.get("bigChancesMissed", 0),
                    "Total shots": stats.get("totalShots", 0),
                    "Shots on target": stats.get("shotsOnTarget", 0),
                    "Shots off target": stats.get("shotsOffTarget", 0),
                    "Goal conversion %": stats.get("goalConversionPercentage", 0),
                    "Succ. dribbles": stats.get("successfulDribbles", 0),
                    "Succ. dribbles %": stats.get("successfulDribblesPercentage", 0),
                    "Goals inside box": stats.get("goalsFromInsideTheBox", 0),
                    "Goals outside box": stats.get("goalsFromOutsideTheBox", 0),
                    "Headed goals": stats.get("headedGoals", 0),
                    "Left-footed goals": stats.get("leftFootGoals", 0),
                    "Right-footed goals": stats.get("rightFootGoals", 0),
                    "Hit woodwork": stats.get("hitWoodwork", 0),
                    "Offsides": stats.get("offsides", 0),
                    "Penalties won": stats.get("penaltyWon", 0),
                    "Penalties taken": stats.get("penaltiesTaken", 0), 
                    "Penalty goals": stats.get("penaltyGoals", 0),
                    "Penalty conversion %": stats.get("penaltyConversion", 0),
                    "Free kick goals": stats.get("freeKickGoal", 0),
                    "Shots from set piece": stats.get("shotFromSetPiece", 0),
                    "Set piece conv. %": stats.get("setPieceConversion", 0),

                    # --- Nhóm Defense ---
                    "Tackles": stats.get("tackles", 0),
                    "Interceptions": stats.get("interceptions", 0),
                    "Clearances": stats.get("clearances", 0),
                    "Blocked shots": stats.get("outfielderBlocks", 0),
                    "Dribbled past": stats.get("dribbledPast", 0),
                    "Errors leading to goal": stats.get("errorLeadToGoal", 0),
                    "Errors leading to shot": stats.get("errorLeadToShot", 0),
                    "Penalties committed": stats.get("penaltyConceded", 0),
                    "Own goals": stats.get("ownGoals", 0),
                    "Clean sheets": stats.get("cleanSheet", 0),

                    # --- Nhóm Passing ---
                    "Big chances created": stats.get("bigChancesCreated", 0),
                    "Assists": stats.get("assists", 0),
                    "Passes to assist": stats.get("passToAssist", 0),
                    "Key passes": stats.get("keyPasses", 0),
                    "Total passes": stats.get("totalPasses", 0),
                    "Accurate passes": stats.get("accuratePasses", 0),
                    "Inaccurate passes": stats.get("inaccuratePasses", 0),
                    "Accurate passes %": stats.get("accuratePassesPercentage", 0),
                    "Passes in own half": stats.get("accurateOwnHalfPasses", 0),
                    "Passes in opp. half": stats.get("accurateOppositionHalfPasses", 0),
                    "Acc. final third passes": stats.get("accurateFinalThirdPasses", 0),
                    "Accurate crosses": stats.get("accurateCrosses", 0),
                    "Accurate crosses %": stats.get("accurateCrossesPercentage", 0),
                    "Accurate long balls": stats.get("accurateLongBalls", 0),
                    "Accurate long balls %": stats.get("accurateLongBallsPercentage", 0),

                    # --- Nhóm Other (Thể lực & Tranh chấp) ---
                    "Appearances": stats.get("appearances", 0),
                    "Started": stats.get("matchesStarted", 0),
                    "Minutes played": stats.get("minutesPlayed", 0),
                    "Yellow cards": stats.get("yellowCards", 0),
                    "Red cards": stats.get("redCards", 0),
                    "Fouls": stats.get("fouls", 0),
                    "Was fouled": stats.get("wasFouled", 0),
                    "Possession lost": stats.get("possessionLost", 0),
                    "Dispossessed": stats.get("dispossessed", 0),
                    "Total duels won": stats.get("totalDuelsWon", 0),
                    "Total duels won %": stats.get("totalDuelsWonPercentage", 0),
                    "Ground duels won": stats.get("groundDuelsWon", 0),
                    "Ground duels won %": stats.get("groundDuelsWonPercentage", 0),
                    "Aerial duels won": stats.get("aerialDuelsWon", 0),
                    "Aerial duels won %": stats.get("aerialDuelsWonPercentage", 0)
                })

            offset += limit
            time.sleep(1.5) # Nghỉ 1.5s để tránh bị block

        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            break

# ==========================================
# 4. XUẤT RA FILE CSV
# ==========================================
if all_rows:
    df = pd.DataFrame(all_rows)
    df.index = range(1, len(df) + 1)
    df.index.name = "#"
    
    # Sort lại theo Rating để danh sách xuất ra đẹp mắt như cũ
    df = df.sort_values(by="Sofascore Rating", ascending=False).reset_index(drop=True)
    df.index = range(1, len(df) + 1)
    df.index.name = "#"

    csv_filename = f"data/processed/{league_name}_FULL_STATS.csv"
    df.to_csv(csv_filename, index=True, encoding='utf-8-sig')
    print(f"\n✅ Đã quét xong! Lưu thành công {len(df)} cầu thủ vào: {csv_filename}")
    print("Mở file CSV lên để chiêm ngưỡng kiệt tác nhé!")
else:
    print("\n⚠️ Không có dữ liệu nào được thu thập.")