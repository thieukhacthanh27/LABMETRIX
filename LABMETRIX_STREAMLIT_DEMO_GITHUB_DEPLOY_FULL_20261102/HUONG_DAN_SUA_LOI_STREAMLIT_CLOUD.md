# Sửa FileNotFoundError trên Streamlit Cloud

Lỗi: `st.image("assets/logo.png")` đọc ảnh theo thư mục chạy, trong khi mã nguồn nằm trong thư mục con của GitHub.

## Cập nhật nhanh trên GitHub
1. Mở repository `thieukhacthanh27/LABMETRIX`, nhánh `main`.
2. Vào `LABMETRIX_STREAMLIT_DEMO_GITHUB_DEPLOY_FULL_20261102/streamlit_app.py`.
3. Chọn biểu tượng chỉnh sửa, thay toàn bộ nội dung bằng file `streamlit_app.py` trong ZIP này, sau đó **Commit changes**.
4. Mở Streamlit Community Cloud > Manage app > Reboot nếu trang chưa tự cập nhật.

Nếu muốn tải toàn bộ lại, giải nén ZIP rồi upload các file bên trong thư mục mã nguồn vào đúng thư mục con ở GitHub, không tải nguyên ZIP.

File ZIP dùng để cập nhật repo, **không làm thay đổi dữ liệu hoặc ứng dụng đang chạy cho đến khi bạn commit lên GitHub**.

Lưu ý: SQLite lưu trên Streamlit Community Cloud có thể mất dữ liệu khi khởi động lại. Chỉ nhập dữ liệu DEMO.
