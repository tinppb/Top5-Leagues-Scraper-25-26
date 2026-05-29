# Top 5 European Leagues Stats Scraper (23/24 - 25/26)

Dự án thu thập tự động dữ liệu thống kê cầu thủ của **Top 5 giải vô địch quốc gia hàng đầu Châu Âu** (Premier League, La Liga, Serie A, Bundesliga, Ligue 1) qua các mùa giải 2023/2024, 2024/2025, và 2025/2026 từ hệ thống dữ liệu nội bộ của Sofascore. Toàn bộ dữ liệu được tự động phân trang, làm sạch, tính toán các chỉ số nâng cao (Per Match, Per 90) và xuất ra file định dạng CSV cùng cơ sở dữ liệu SQLite sẵn sàng cho việc phân tích dữ liệu (Data Analysis).

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
3. **Phục vụ phân tích chuyên sâu:** Tạo ra bộ dataset khổng lồ (hơn 60 chỉ số) gộp chung cả Tấn công, Phòng ngự, Chuyền bóng. Đặc biệt, hệ thống tự động hỗ trợ quy đổi chỉ số sang Trung bình mỗi trận (Per Match) và Trung bình mỗi 90 phút (Per 90) và lưu trữ đồng thời dưới dạng CSV và SQLite.

---

## Yêu Cầu & Cài Đặt

**1. Môi trường yêu cầu**
- Python 3.8 trở lên.

**2. Mạng & Kết nối (Quan trọng)**
- Bạn CẦN sử dụng **Cloudflare WARP (1.1.1.1)** hoặc **VPN** khi chạy dự án này. Do một số nhà mạng có thể chặn truy cập vào máy chủ Sofascore, hoặc IP thường của bạn bị giới hạn khu vực.

**3. Clone dự án về máy**
```bash
git clone https://github.com/tinppb/Top5-Leagues-Scraper-25-26.git
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

Kịch bản giờ đây được thiết kế thành một **Pipeline tự động (All-in-One)** quét qua tất cả 5 giải đấu lớn trong 3 mùa giải (25/26, 24/25, 23/24). Bạn chỉ cần chạy file `main.py` và truyền vào kiểu thống kê mong muốn. 

Cú pháp:
`python main.py [Kiểu_Thống_Kê]`

*(Lưu ý: Kiểu thống kê hỗ trợ: `total`, `perMatch`, `per90` - Mặc định nếu không nhập sẽ là `per90`)*

**Ví dụ 1: Lấy dữ liệu Tổng (Total) cho toàn bộ 5 giải và 3 mùa**
```bash
python main.py total
```

**Ví dụ 2: Lấy dữ liệu Trung bình mỗi trận (Per Match)**
```bash
python main.py perMatch
```

**Ví dụ 3: Lấy dữ liệu Trung bình mỗi 90 phút (Per 90 - Mặc định)**
```bash
python main.py per90
```

**Kết quả Đầu Ra:** 
- Dữ liệu thô JSON backup tại `data/raw/full_stats/`.
- File CSV sạch theo từng giải đấu và mùa giải tại `data/processed/` (VD: `Premier_League_25_26_PER90_STATS.csv`).
- Cơ sở dữ liệu chung SQLite được lưu tại `data/processed/football_stats.db`, trong đó dữ liệu được phân chia theo từng bảng (ví dụ: `stats_per90`, `stats_total`).

---

## Kiến Trúc Dự Án
Dữ liệu được tổ chức và thu thập qua một Pipeline tự động:
- **Orchestrator (`main.py`):** Tập lệnh điều phối tự động chạy qua 5 giải đấu x 3 mùa giải, và gọi lệnh tới Worker để lấy dữ liệu. Quản lý thời gian giãn cách giữa các requests để tránh bị chặn IP.
- **Worker (`crawler/full_stats.py`):** Kịch bản độc lập quét qua 4 vị trí (Thủ môn, Hậu vệ, Tiền vệ, Tiền đạo), ép Server trả về 60+ chỉ số.
- **Data Transformation:** Tích hợp bộ xử lý tự động chia trung bình dựa trên số trận/phút thi đấu, đồng thời thông minh giữ nguyên các cột định dạng phần trăm (%).
- **Data Layer (`data/`):** Tách biệt rõ ràng giữa Dữ liệu thô (`raw/` JSON) dùng để đối chiếu backup, và Dữ liệu đã xử lý lưu song song ở `processed/` thành CSV và Database SQLite dành cho phân tích.

---

## Luồng Dữ Liệu
Quy trình xử lý dữ liệu của hệ thống tuân theo các bước sau:
1. **Khởi tạo Request:** Gửi HTTP GET request tới endpoint của Sofascore kèm các headers (User-Agent thực) và thông số `impersonate="chrome124"` qua `curl_cffi`.
2. **Xử lý Phân trang:** Vòng lặp `while True` liên tục tăng biến `offset` lên 20. Vòng lặp dừng khi API trả về danh sách rỗng `[]`.
3. **Backup Raw Data:** Toàn bộ dữ liệu JSON trả về ở mỗi trang được lưu thành file tĩnh tại `data/raw/full_stats/` để dự phòng.
4. **Data Parsing & Transform (ETL):** Trích xuất thông tin Cầu thủ. Kích hoạt hàm tính toán nội bộ để tự động chia các thông số Tấn công/Phòng ngự/Chuyền bóng theo biến `perMatch` hoặc `per90`.
5. **Xuất Output đa định dạng:** Chuyển đổi dữ liệu sang Pandas DataFrame, sắp xếp theo điểm Rating giảm dần và lưu song song ra file CSV (`utf-8`) và Database SQLite (`football_stats.db`).

---

## Từ Điển Dữ Liệu
Các file CSV và SQLite đầu ra chứa hơn 60 biến số gộp chung, bao gồm các trường dữ liệu tiêu biểu:

* **Định danh chung:** `#` (Xếp hạng), `League`, `Season`, `Team`, `Name`, `Position` (Tự động gán nhãn vị trí), `Sofascore Rating`.
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
TOP 5 LEAGUE EU/
│
├── .venv/                    # Môi trường ảo 
├── crawler/                  
│   ├── full_stats.py         # Worker: Thu thập, tính toán 60+ chỉ số và xuất Data
│   └── ...                   # Các file modules khác
│
├── data/                     
│   ├── processed/            # Dữ liệu CSV và file SQLite (football_stats.db)
│   └── raw/                  
│
├── main.py                   # Orchestrator: Quản lý chạy Auto toàn bộ 5 Giải đấu & 3 Mùa Giải
├── get_seasons.py            # Hỗ trợ lấy mapping ID các mùa giải  
├── README.md                 
├── requirements.txt
└── transform.py              


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
- **Khắc phục:** Script `main.py` và `full_stats.py` đã tự động chèn `time.sleep()`. Nếu vẫn bị, bạn có thể tăng thời gian `sleep()` trong mã nguồn lên.

**4. Cột dữ liệu toàn số 0**
- **Nguyên nhân:** Tên tham số khai báo trong `fields` không khớp với Database của Sofascore.
- **Khắc phục:** Code hiện tại đã được fix chuẩn xác 100% các keys. Nếu xuất hiện ở cột mới muốn thêm vào, hãy tự in JSON cục bộ (`print(json.dumps(data))`) để dò tìm tên biến thực tế.
