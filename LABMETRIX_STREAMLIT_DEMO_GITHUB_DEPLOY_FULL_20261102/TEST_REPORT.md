# Báo cáo kiểm tra bản LABMETRIX Streamlit DEMO

- `python -m compileall -q streamlit_app.py db.py exports.py`: đạt.
- `python -m pytest tests -q`: 6/6 bài test API/kho dữ liệu đạt (SQLite).
- `python tests/smoke_stub.py`: 12/12 nhánh trang chạy được với stub giao diện (không phải trình duyệt Streamlit thực).
- Dữ liệu hợp đồng, đơn, mẫu, chỉ tiêu, kết quả tạo ở hai `Store` khác nhau cùng SQLite: kiểm tra đạt.
- Chống ghi đè qua `revision`: kiểm tra đạt.
- Tải ảnh/PDF: kiểm tra chữ ký tệp, giới hạn kích thước; lưu bản nháp và tạo ZIP đạt.
- Word/PDF cho đơn: tạo được dữ liệu byte không lỗi.
- **Chưa thực hiện:** chạy Streamlit Community Cloud thật, kiểm thử browser trên điện thoại, kết nối PostgreSQL thật. Môi trường làm việc không có gói Streamlit và không tải được gói qua mạng để chạy thử giao diện.
- **Chưa kế thừa đủ 1:1**: tính toán GC-MS bdf, biểu mẫu cố định gốc, phân quyền bảo mật thực, quy trình ký số chính thức, nhập Excel nguồn bất kỳ và những nghiệp vụ VILAS chuyên sâu.
- **Dữ liệu vận hành thực:** tuyệt đối không sử dụng.
