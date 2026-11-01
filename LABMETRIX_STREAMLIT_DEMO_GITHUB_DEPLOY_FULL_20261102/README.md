# LABMETRIX · Streamlit Online DEMO

> **Mã nguồn DEMO độc lập cho Streamlit Community Cloud.** Không phải bản sao nguyên xi của LABMETRIX FastAPI/legacy và không đủ điều kiện dùng làm LIMS vận hành thực tế, phiếu kiểm nghiệm hoặc chữ ký điện tử có giá trị pháp lý.

## 1. Chức năng bản này

- **Hợp đồng:** tạo/sửa, liên kết đơn, hạn trả.
- **Đơn quan trắc:** nhiều đơn theo hợp đồng, theo dõi trạng thái.
- **Mẫu:** thêm hàng loạt NT/NM/NS/KT/KLV/KXQ; tiếp nhận, theo dõi.
- **Chỉ tiêu/Kết quả:** bóc tách chỉ tiêu, chọn phương pháp, lưu kết quả mới không sửa giá trị gốc, QC thử nghiệm.
- **QA/QC & duyệt:** mô phỏng thứ tự QA → Trưởng phòng → Giám đốc và trả lại; không dùng chữ ký thật.
- **Tiến độ:** truy vết đơn → mẫu → chỉ tiêu → kết quả, cảnh báo trễ hạn.
- **Ảnh/PDF/DOCX:** chụp và tải lên tệp nhỏ (2 MB/tệp); nội dung lưu trong cùng cơ sở dữ liệu.
- **Thư viện:** phương pháp, thiết bị, hóa chất.
- **Bàn giao / công việc:** lập và xem biên bản bàn giao giả, giao việc.
- **Xuất hồ sơ:** Word, PDF, ZIP kèm ảnh; worklist CSV và nhập mẫu theo Excel/CSV.
- **Nhật ký:** xem lịch sử thao tác và kiểm tra xung đột khi sửa cùng một hồ sơ.
- **PC/Mobile:** cùng ứng dụng, giao diện responsive; cùng cơ sở dữ liệu trên máy chủ. Bấm tải lại để thấy thao tác từ thiết bị khác.

## 2. Đưa lên GitHub (không tải mã nguồn LAN, không gửi dữ liệu thật)

1. Tải ZIP này và giải nén. Mở GitHub, tạo repository mới, ví dụ `labmetrix-streamlit-demo`.
2. Chọn chế độ **Private** trước; upload các tệp trong thư mục này sao cho `streamlit_app.py` nằm ngay gốc repository. Đừng tải thư mục `.venv`, `runtime`, `secrets.toml` hoặc tệp dữ liệu lên.
3. **Không đưa dữ liệu, hồ sơ, chữ ký, mật khẩu hoặc ảnh khách hàng thật lên GitHub.** Toàn bộ dữ liệu khởi tạo trong mã là giả.

## 3. Triển khai Streamlit Community Cloud

1. Truy cập **https://share.streamlit.io/** và đăng nhập bằng GitHub.
2. Chọn **Create app** → repo `labmetrix-streamlit-demo` → branch `main` → Main file path `streamlit_app.py`.
3. Trong **Advanced settings**, chọn Python **3.12**, nhập Secrets nếu cần (xem bước 4), rồi **Deploy**.
4. Sau khi app chạy, cung cấp đường dẫn `*.streamlit.app` cho người tham gia DEMO. Có thể mở từ PC hoặc điện thoại.

## 4. Quan trọng: dữ liệu dùng chung và tính bền vững

**Mặc định app dùng SQLite trong `runtime/labmetrix_demo.sqlite3`. Trên Streamlit Community Cloud, ổ đĩa của app KHÔNG được bảo đảm lưu lâu dài.** Mọi người có thể thấy dữ liệu chung khi chạy trên cùng phiên máy chủ, nhưng dữ liệu có thể mất sau khi ứng dụng khởi động lại hoặc triển khai lại.

Để dùng thử nhiều người và giữ dữ liệu qua khởi động, tạo **cơ sở dữ liệu PostgreSQL riêng dành cho DEMO** tại nhà cung cấp phù hợp rồi dán vào **App settings → Secrets**:

```toml
DEMO_ACCESS_CODE = "ma-thu-nghiem-tu-ban-dat"
LABMETRIX_DATABASE_URL = "postgresql://<user>:<password>@<host>:5432/<database>?sslmode=require"
```

**Không ghi giá trị thật vào repository hoặc commit Secrets vào GitHub.** Hỗ trợ PostgreSQL qua SQLAlchemy + psycopg v3. Ảnh/PDF cũng lưu trong database để không lệ thuộc ổ tạm (tối đa 2 MB/tệp, cân nhắc giới hạn dung lượng của nhà cung cấp database). Nhớ sử dụng PostgreSQL chuyên cho dữ liệu giả; người truy cập app có thể xem các hồ sơ giả dùng chung.

`DEMO_ACCESS_CODE` là **cổng truy cập DEMO dùng chung**, không phải hệ thống tài khoản phân quyền. Người dùng tự chọn tên/vai trò mô phỏng, không có chứng thực danh tính.

## 5. Chạy trên PC Windows

Cài Python 3.12, sau đó mở PowerShell trong thư mục đã giải nén:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run streamlit_app.py
```

Bạn cũng có thể nhấp đúp `CHAY_STREAMLIT_WINDOWS.bat` để tự tạo môi trường và cài thư viện.

Cách khởi động này chỉ phục vụ Streamlit, **không dùng `CHAY_MAY_CHU_LABMETRIX.bat` hoặc IP cũ `192.168.0.100`**.

## 6. Kiểm thử và giới hạn hiện tại

Chạy: `python -m pytest tests -q` (cần `pip install pytest`).

Các phần **chưa kế thừa tương đương 1:1** với hệ thống FastAPI LAN: tích hợp biên bản gốc phức tạp, GC-MS bdf/MassHunter, SOP tính toán, phân quyền và chữ ký thật, xác nhận VILAS, migration toàn bộ dữ liệu legacy, lịch phân công đa tầng và quy trình khóa hồ sơ sau duyệt. Đây là **phiên bản đa phân hệ để nhiều người dùng thử**, không phải phần mềm đã nghiệm thu dùng hồ sơ thật.

Các giá trị kết quả không được sửa đè; nếu cần cập nhật, tạo bản kết quả mới, giữ bản trước và audit. Các quyền duyệt chỉ mô phỏng và không ngăn người biết mã DEMO đổi vai trò. Nếu cần bảo mật/phân quyền thật, phải triển khai hệ thống danh tính/roles ở tầng máy chủ và kiểm thử lại.

## 7. Lưu ý công khai ứng dụng

- Không đăng mã truy cập chung ở GitHub.
- Nếu dùng repo public, mọi nội dung repository đều công khai, dù bản thân app có mã truy cập.
- Có thể phát mã truy cập DEMO riêng qua nhóm nội bộ.
- Streamlit Community Cloud không phải nơi lưu trữ hồ sơ thử nghiệm quan trọng.
- Không khai báo hay tạo dữ liệu cá nhân thực trong form.

## Tham khảo chính thức

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
