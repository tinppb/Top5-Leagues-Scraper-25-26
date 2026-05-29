import sys
import os
import json
import time
import pandas as pd
from curl_cffi import requests

# ==========================================
# 1. NHẬN LỆNH TỪ TERMINAL
# ==========================================
league_name = sys.argv[1] if len(sys.argv) > 1 else "Premier_League"
tour_id = sys.argv[2] if len(sys.argv) > 2 else "17"
season_id = sys.argv[3] if len(sys.argv) > 3 else "76986"
acc_type = sys.argv[4] if len(sys.argv) > 4 else "per90"
season_name = sys.argv[5] if len(sys.argv) > 5 else "25_26"

print(f"\n🚀 Đang khởi động cào dữ liệu ({acc_type.upper()}) cho giải: {league_name.replace('_', ' ')} (Mùa {season_name})...")

url = f"https://www.sofascore.com/api/v1/unique-tournament/{tour_id}/season/{season_id}/statistics"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
}

limit = 20
all_rows = []

os.makedirs("data/raw/full_stats", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

POSITIONS = {"G": "Goalkeeper", "D": "Defender", "M": "Midfielder", "F": "Forward"}

# ==========================================
# 2. VÒNG LẶP CÀO DỮ LIỆU VÀ XỬ LÝ
# ==========================================
for pos_code, pos_name in POSITIONS.items():
    print(f"\n👉 Bắt đầu quét nhóm cầu thủ: {pos_name}...")
    offset = 0
    
    while True:
        print(f"   Đang tải trang dữ liệu {pos_name} (Offset: {offset})...")
        params = {
            "limit": limit, "offset": offset, "order": "-rating", "accumulation": "total",
            "filters": f"position.in.{pos_code}",
            "fields": "goals,successfulDribblesPercentage,outfielderBlocks,penaltyWon,goalsFromOutsideTheBox,hitWoodwork,expectedGoals,totalShots,goalConversionPercentage,shotFromSetPiece,headedGoals,offsides,bigChancesMissed,shotsOnTarget,penaltiesTaken,freeKickGoal,leftFootGoals,penaltyConversion,successfulDribbles,shotsOffTarget,penaltyGoals,goalsFromInsideTheBox,rightFootGoals,setPieceConversion,tackles,errorLeadToGoal,cleanSheet,interceptions,errorLeadToShot,penaltyConceded,ownGoals,clearances,dribbledPast,bigChancesCreated,totalPasses,accurateFinalThirdPasses,accurateLongBalls,assists,accuratePassesPercentage,keyPasses,accurateLongBallsPercentage,accuratePasses,accurateOwnHalfPasses,accurateCrosses,passToAssist,inaccuratePasses,accurateOppositionHalfPasses,accurateCrossesPercentage,yellowCards,aerialDuelsWon,minutesPlayed,possessionLost,redCards,aerialDuelsWonPercentage,wasFouled,appearances,groundDuelsWon,totalDuelsWon,fouls,matchesStarted,groundDuelsWonPercentage,totalDuelsWonPercentage,dispossessed,rating"
        }

        try:
            response = requests.get(url, headers=headers, params=params, impersonate="chrome124")
            if response.status_code != 200: 
                print(f"❌ Lỗi HTTP {response.status_code}.")
                break
            
            data = response.json()
            
            # Lưu raw backup
            raw_filepath = f"data/raw/full_stats/{league_name}_{pos_name}_offset_{offset}.json"
            with open(raw_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            players = data.get("results", [])
            if not players: break
                
            # ==========================================
            # 3. TRANSFORM & CLEANING (ETL)
            # ==========================================
            for p in players:
                player_info = p.get("player", {})
                team_info = p.get("team", {})
                stats = p
                
                # CHÚ Ý: LÀM SẠCH TÊN ĐỘI BÓNG ĐỨC TẠI ĐÂY ("1. FC Köln" -> "FC Köln")
                team_name = team_info.get("name", "Unknown")
                if team_name.startswith("1. "):
                    team_name = team_name.replace("1. ", "", 1)
                
                appearances = stats.get("appearances", 0)
                minutes_played = stats.get("minutesPlayed", 0)

                # HÀM CHIA TRUNG BÌNH (Bỏ qua nếu là biến %)
                def calc(val, is_percentage=False):
                    if val is None: return 0
                    if is_percentage: return val # Cột % thì giữ nguyên
                    if acc_type == "perMatch" and appearances > 0:
                        return round(val / appearances, 2)
                    elif acc_type == "per90" and minutes_played > 0:
                        return round((val / minutes_played) * 90, 2)
                    return round(val, 2) if isinstance(val, float) else val

                # GÁN DỮ LIỆU
                all_rows.append({
                    "Player ID": player_info.get("id"),
                    "League": league_name.replace("_", " "),
                    "Season": season_name.replace("_", "/"),
                    "Team": team_name,  # TRUYỀN TÊN ĐÃ LÀM SẠCH (Tuyệt đối không bọc calc)
                    "Name": player_info.get("name"),
                    "Position": pos_name, 
                    "Sofascore Rating": stats.get("rating", 0),
                    
                    # Chỉ số Tấn công
                    "Goals": calc(stats.get("goals", 0)),
                    "xG": calc(stats.get("expectedGoals", 0)),
                    "Big chances missed": calc(stats.get("bigChancesMissed", 0)),
                    "Total shots": calc(stats.get("totalShots", 0)),
                    "Shots on target": calc(stats.get("shotsOnTarget", 0)),
                    "Shots off target": calc(stats.get("shotsOffTarget", 0)),
                    "Goal conversion %": calc(stats.get("goalConversionPercentage", 0), True),
                    "Succ. dribbles": calc(stats.get("successfulDribbles", 0)),
                    "Succ. dribbles %": calc(stats.get("successfulDribblesPercentage", 0), True),
                    "Goals inside box": calc(stats.get("goalsFromInsideTheBox", 0)),
                    "Goals outside box": calc(stats.get("goalsFromOutsideTheBox", 0)),
                    "Headed goals": calc(stats.get("headedGoals", 0)),
                    "Left-footed goals": calc(stats.get("leftFootGoals", 0)),
                    "Right-footed goals": calc(stats.get("rightFootGoals", 0)),
                    "Hit woodwork": calc(stats.get("hitWoodwork", 0)),
                    "Offsides": calc(stats.get("offsides", 0)),
                    "Penalties won": calc(stats.get("penaltyWon", 0)),
                    "Penalties taken": calc(stats.get("penaltiesTaken", 0)), 
                    "Penalty goals": calc(stats.get("penaltyGoals", 0)),
                    "Penalty conversion %": calc(stats.get("penaltyConversion", 0), True),
                    "Free kick goals": calc(stats.get("freeKickGoal", 0)),
                    "Shots from set piece": calc(stats.get("shotFromSetPiece", 0)),
                    "Set piece conv. %": calc(stats.get("setPieceConversion", 0), True),

                    # Chỉ số Phòng ngự
                    "Tackles": calc(stats.get("tackles", 0)),
                    "Interceptions": calc(stats.get("interceptions", 0)),
                    "Clearances": calc(stats.get("clearances", 0)),
                    "Blocked shots": calc(stats.get("outfielderBlocks", 0)),
                    "Dribbled past": calc(stats.get("dribbledPast", 0)),
                    "Errors leading to goal": calc(stats.get("errorLeadToGoal", 0)),
                    "Errors leading to shot": calc(stats.get("errorLeadToShot", 0)),
                    "Penalties committed": calc(stats.get("penaltyConceded", 0)),
                    "Own goals": calc(stats.get("ownGoals", 0)),
                    "Clean sheets": calc(stats.get("cleanSheet", 0)),

                    # Chỉ số Chuyền bóng
                    "Big chances created": calc(stats.get("bigChancesCreated", 0)),
                    "Assists": calc(stats.get("assists", 0)),
                    "Passes to assist": calc(stats.get("passToAssist", 0)),
                    "Key passes": calc(stats.get("keyPasses", 0)),
                    "Total passes": calc(stats.get("totalPasses", 0)),
                    "Accurate passes": calc(stats.get("accuratePasses", 0)),
                    "Inaccurate passes": calc(stats.get("inaccuratePasses", 0)),
                    "Accurate passes %": calc(stats.get("accuratePassesPercentage", 0), True),
                    "Passes in own half": calc(stats.get("accurateOwnHalfPasses", 0)),
                    "Passes in opp. half": calc(stats.get("accurateOppositionHalfPasses", 0)),
                    "Acc. final third passes": calc(stats.get("accurateFinalThirdPasses", 0)),
                    "Accurate crosses": calc(stats.get("accurateCrosses", 0)),
                    "Accurate crosses %": calc(stats.get("accurateCrossesPercentage", 0), True),
                    "Accurate long balls": calc(stats.get("accurateLongBalls", 0)),
                    "Accurate long balls %": calc(stats.get("accurateLongBallsPercentage", 0), True),

                    # Chỉ số Thể lực & Tranh chấp
                    "Appearances": appearances,
                    "Started": stats.get("matchesStarted", 0),
                    "Minutes played": minutes_played,
                    "Yellow cards": calc(stats.get("yellowCards", 0)),
                    "Red cards": calc(stats.get("redCards", 0)),
                    "Fouls": calc(stats.get("fouls", 0)),
                    "Was fouled": calc(stats.get("wasFouled", 0)),
                    "Possession lost": calc(stats.get("possessionLost", 0)),
                    "Dispossessed": calc(stats.get("dispossessed", 0)),
                    "Total duels won": calc(stats.get("totalDuelsWon", 0)),
                    "Total duels won %": calc(stats.get("totalDuelsWonPercentage", 0), True),
                    "Ground duels won": calc(stats.get("groundDuelsWon", 0)),
                    "Ground duels won %": calc(stats.get("groundDuelsWonPercentage", 0), True),
                    "Aerial duels won": calc(stats.get("aerialDuelsWon", 0)),
                    "Aerial duels won %": calc(stats.get("aerialDuelsWonPercentage", 0), True)
                })

            offset += limit
            time.sleep(1.5)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            break

# ==========================================
# 4. XUẤT CSV VÀ LƯU VÀO SQLITE
# ==========================================
if all_rows:
    df = pd.DataFrame(all_rows)
    df = df.sort_values(by="Sofascore Rating", ascending=False).reset_index(drop=True)
    df.index = range(1, len(df) + 1)
    df.index.name = "#"
    
    # 4.1 XUẤT CSV THEO MÙA GIẢI
    csv_filename = f"data/processed/{league_name}_{season_name}_{acc_type.upper()}_STATS.csv"
    df.to_csv(csv_filename, index=True, encoding='utf-8')
    print(f"\n✅ Đã lưu thành công {len(df)} cầu thủ vào: {csv_filename}")
    
    # 4.2 LƯU VÀO DATABASE SQLITE
    import sqlite3
    db_path = "data/processed/football_stats.db"
    try:
        conn = sqlite3.connect(db_path)
        # Lưu vào table có tên là acc_type (ví dụ: stats_per90)
        table_name = f"stats_{acc_type.lower()}"
        df.to_sql(name=table_name, con=conn, if_exists="append", index=False)
        print(f"✅ Đã backup thành công vào Database SQLite: {db_path} (Table: {table_name})")
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi khi lưu vào SQLite: {e}")