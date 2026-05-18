# ⚽ Top 5 European Leagues 25/26 Stats Scraper

Dự án thu thập tự động dữ liệu thống kê cầu thủ của **Top 5 giải vô địch quốc gia hàng đầu Châu Âu** (Premier League, La Liga, Serie A, Bundesliga, Ligue 1) mùa giải 2025/2026 từ hệ thống dữ liệu nội bộ của Sofascore. Toàn bộ dữ liệu được tự động phân trang, làm sạch, tính toán các chỉ số nâng cao (Per Match, Per 90) và xuất ra file định dạng CSV sẵn sàng cho việc phân tích dữ liệu (Data Analysis).

---

## Mục Lục
- [Mục Tiêu Dự Án](#mục-tiêu-dự-án)
- [Yêu Cầu & Cài Đặt](#yêu-cầu--cài-đặt)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
- [Kiến Trúc Dự Án](#kiến-trúc-dự-án)
- [Luồng Dữ Liệu](#luồng-dữ-liệu)
- [Từ Điển Dữ Liệu](#từ-điển-dữ-liệu)
- [Thông Tin API](#thông-tin-api)
- [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
- [Khắc Phục Sự Cố](#khắc-phục-sự-cố)

---

## Mục Tiêu Dự Án
Các trang thống kê thể thao lớn thường bảo vệ dữ liệu rất nghiêm ngặt bằng các công nghệ chống Bot (như Cloudflare, Akamai). Dự án này ra đời nhằm:
1. **Mục đích học tập:** Áp dụng kỹ thuật Web Scraping nâng cao, vượt qua hệ thống chống Bot bằng cách giả mạo TLS fingerprint của trình duyệt thực.
2. **Cung cấp dữ liệu sạch:** Lấy trực tiếp dữ liệu thô (Raw JSON) chuẩn xác 100% từ API nội bộ mà không cần cào (parse) mã nguồn HTML phức tạp.
3. **Phục vụ phân tích chuyên sâu:** Tạo ra bộ dataset khổng lồ (hơn 60 chỉ số) gộp chung cả Tấn công, Phòng ngự, Chuyền bóng. Đặc biệt, hệ thống tự động hỗ trợ quy đổi chỉ số sang Trung bình mỗi trận (Per Match) và Trung bình mỗi 90 phút (Per 90).

---

## Yêu Cầu & Cài Đặt

**1. Môi trường yêu cầu**
- Python 3.8 trở lên.

**2. Mạng & Kết nối (Quan trọng)**
- Bạn CẦN sử dụng **Cloudflare WARP (1.1.1.1)** hoặc **VPN** khi chạy dự án này. Do một số nhà mạng có thể chặn truy cập vào máy chủ Sofascore, hoặc IP thường của bạn bị giới hạn khu vực.

**3. Clone dự án về máy**
```bash
git clone [https://github.com/tinppb/Top5-Leagues-Scraper-25-26.git](https://github.com/tinppb/Top5-Leagues-Scraper-25-26.git)
cd Top5-Leagues-Scraper-25-26
```

**4. Tạo và kích hoạt môi trường ảo**
```bash
python -m venv .venv
# Dành cho Windows:
.venv\Scripts\activate
# Dành cho MacOS/Linux:
source .venv/bin/activate
```

**5. Cài đặt các thư viện cần thiết**
```bash
pip install -r requirements.txt
```

---

## Hướng Dẫn Sử Dụng

Kịch bản giờ đây được thiết kế gộp (All-in-One) và nhận 4 tham số đầu vào. Cú pháp: 
`python crawler/full_stats.py [Tên_Giải] [Tournament_ID] [Season_ID] [Kiểu_Thống_Kê]`

*(Lưu ý: Kiểu thống kê hỗ trợ: `total`, `perMatch`, `per90`)*

**Ví dụ 1: Lấy dữ liệu Tổng cả mùa giải của Premier League (Mặc định)**
```bash
python crawler/full_stats.py Premier_League 17 76986 total
```

**Ví dụ 2: Lấy dữ liệu Trung bình mỗi trận của La Liga**
```bash
python crawler/full_stats.py La_Liga 8 77559 perMatch
```

**Ví dụ 3: Lấy dữ liệu Trung bình mỗi 90 phút (Chuyên dùng cho Scouting)**
```bash
python crawler/full_stats.py Premier_League 17 76986 per90
```

**Kết quả:** Dữ liệu Raw (JSON) được backup tại `data/raw/`. File CSV sạch, đã được tính toán toán học, lưu tại `data/processed/` với tên file tương ứng (VD: `Premier_League_PER90_STATS.csv`).

---

## Kiến Trúc Dự Án
Dự án được cấu trúc lại để tối ưu hóa quy trình Data Engineering (ETL):
- **Worker (`crawler/full_stats.py`):** Kịch bản All-in-One độc lập. Nó sẽ quét qua 4 vị trí (Thủ môn, Hậu vệ, Tiền vệ, Tiền đạo), ép Server trả về 60+ chỉ số.
- **Data Transformation:** Tích hợp bộ xử lý tự động chia trung bình dựa trên số trận/phút thi đấu, đồng thời thông minh giữ nguyên các cột định dạng phần trăm (%).
- **Data Layer (`data/`):** Tách biệt rõ ràng giữa Dữ liệu thô (`raw/` JSON) dùng để đối chiếu backup và Dữ liệu đã xử lý (`processed/` CSV) dành cho End-user.

---

## Luồng Dữ Liệu
Quy trình xử lý dữ liệu của hệ thống tuân theo các bước sau:
1. **Khởi tạo Request:** Gửi HTTP GET request tới endpoint của Sofascore kèm các headers (User-Agent thực) và thông số `impersonate="chrome124"` qua `curl_cffi`.
2. **Xử lý Phân trang:** Vòng lặp `while True` liên tục tăng biến `offset` lên 20. Vòng lặp dừng khi API trả về danh sách rỗng `[]`.
3. **Backup Raw Data:** Toàn bộ dữ liệu JSON trả về ở mỗi trang được lưu thành file tĩnh tại `data/raw/` để dự phòng.
4. **Data Parsing & Transform (ETL):** Trích xuất thông tin Cầu thủ. Kích hoạt hàm tính toán nội bộ để tự động chia các thông số Tấn công/Phòng ngự/Chuyền bóng nếu người dùng chọn mode `perMatch` hoặc `per90`.
5. **Xuất CSV:** Chuyển đổi dữ liệu sang Pandas DataFrame, sắp xếp theo điểm Rating giảm dần, đánh số thứ tự (Rank/Index) và lưu thành file CSV định dạng chuẩn `utf-8-sig`.

---

## Từ Điển Dữ Liệu
Các file CSV đầu ra chứa hơn 60 biến số gộp chung, bao gồm các trường dữ liệu tiêu biểu:

* **Định danh chung:** `#` (Xếp hạng), `League`, `Team`, `Name`, `Position` (Tự động gán nhãn vị trí), `Sofascore Rating`.
* **Attack (Tấn công):** `Goals`, `Expected goals (xG)`, `Big chances missed`, `Succ. dribbles`, `Total shots`, `Goal conversion %`.
* **Defense (Phòng ngự):** `Tackles`, `Interceptions`, `Clearances`, `Errors leading to goal`, `Blocked shots`.
* **Passing (Chuyền bóng):** `Big chances created`, `Assists`, `Accurate passes`, `Accurate passes %`, `Key passes`.
* **Chỉ số gốc & Tranh chấp:** `Appearances` (Số trận), `Minutes played`, `Total saves`, `Total duels won`, `Ground duels won`.

---

## Thông Tin API
- **Base URL (Động):** `https://www.sofascore.com/api/v1/unique-tournament/{tour_id}/season/{season_id}/statistics`
- **Phương thức:** `GET`
- **Tham số chính (Parameters):**
  - `limit`: Số lượng bản ghi mỗi trang (Mặc định: 20).
  - `offset`: Điểm bắt đầu của trang (0, 20, 40...).
  - `order`: Tiêu chí sắp xếp (`-rating`). Dấu `-` biểu thị sắp xếp giảm dần.
  - `accumulation`: Luôn đặt là `total` để ép Server trả số gốc, việc chia trung bình được code xử lý nội bộ.
  - `fields`: Ép API trả về đích danh 60+ cột dữ liệu cần thiết.
  - `filters`: Lọc dữ liệu ngay từ phía Server. (VD: `position.in.G` dùng để lấy chính xác danh sách các Thủ môn).

*Lưu ý: API này là tài sản nội bộ của Sofascore. Việc truy cập thông qua script chỉ phục vụ mục đích học tập và nghiên cứu cá nhân.*

---

## Cấu Trúc Thư Mục

```text
TOP 5 LEAGUE EU(25_26)/
│
├── .venv/                    # Môi trường ảo 
├── crawler/                  
│   ├── attack.py             
│   ├── defense.py            
│   ├── full_stats.py         # Tổng hợp 40+ chỉ số
│   ├── goalkeeping.py        
│   └── passing.py            
│
├── data/                     
│   ├── processed/            # Dữ liệu CSV 
│   └── raw/                  # Backup dữ liệu JSON thô từ API
│
├── logs/                     
├── notebooks/       
│
├── .gitignore
├── main.py                  
├── README.md                 
├── requirements.txt
└── transform.py              
```

---

## Khắc Phục Sự Cố

**1. Lỗi kết nối, Timeout hoặc văng lỗi HTTP 403 Forbidden**
- **Nguyên nhân:** Địa chỉ IP mạng của bạn đang bị chặn truy cập vào Sofascore, hoặc nhà mạng (ISP) chặn kết nối.
- **Khắc phục:** Hãy bật phần mềm **Cloudflare WARP (1.1.1.1)** hoặc **VPN** trên máy tính rồi chạy lại script.

**2. Lỗi `ModuleNotFoundError: No module named 'curl_cffi'` khi chạy code**
- **Nguyên nhân:** Code không tìm thấy thư viện trong môi trường ảo.
- **Khắc phục:** Đảm bảo đã kích hoạt môi trường ảo (ví dụ: `.venv\Scripts\activate`) trước khi chạy lệnh.

**3. Code chạy bị treo hoặc báo lỗi HTTP 429 Too Many Requests**
- **Nguyên nhân:** Gửi request quá nhanh khiến cơ chế Anti-Bot phát hiện. 
- **Khắc phục:** Tuyệt đối giữ nguyên hàm gọi qua thư viện `curl_cffi`. Đảm bảo trong code luôn có lệnh `time.sleep()` để mô phỏng thao tác của người thật.

**4. Cột dữ liệu toàn số 0**
- **Nguyên nhân:** Tên tham số khai báo trong `fields` không khớp với Database của Sofascore.
- **Khắc phục:** Code hiện tại đã được fix chuẩn xác 100% các keys. Nếu xuất hiện ở cột mới muốn thêm vào, hãy tự in JSON cục bộ (`print(json.dumps(data))`) để dò tìm tên biến thực tế.