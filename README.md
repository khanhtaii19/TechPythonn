# Tech Store (Flask)

Du an website ban hang cong nghe bang Flask.

## Tinh nang hien tai
- Dang ky / dang nhap tai khoan.
- Danh sach san pham + tim kiem.
- Loc san pham theo category.
- Du lieu mau: toi thieu 5 category, 20 san pham/category.
- Chi tiet san pham.
- Nhieu model/variant trong 1 san pham (mau, phien ban, ngon ngu...).
- Gio hang co so luong theo tung san pham.
- Them vao gio khong can tai lai trang (AJAX).
- Mua ngay tren trang chi tiet san pham (ty le nut 9/1 voi them gio) va card danh sach (8/2).
- Xoa san pham khoi gio.
- Dat hang tao `Order` + `OrderItem`, tru ton kho.
- Gui email xac nhan kem chi tiet don hang.
- Lich su don hang + trang chi tiet don.
- Trang tin tuc (danh sach + chi tiet bai viet).
- Trang quan tri admin (ton kho + dashboard don 7 ngay).

## Cai dat nhanh
1. Tao virtual env va cai thu vien:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Tao file `.env` tu `.env.example` va sua gia tri.
3. Chay migration:
   ```powershell
   flask db upgrade
   ```
4. Seed du lieu mau:
   ```powershell
   python seed_data.py
   ```
5. Chay app:
   ```powershell
   python tech_store.py
   ```

## Bien moi truong quan trong
- `SECRET_KEY`
- `DATABASE_URL` (mac dinh SQLite neu khong khai bao)
- `MAIL_USERNAME`, `MAIL_PASSWORD`
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`

## Ghi chu
- Cac form thay doi du lieu dung `POST + CSRF`.
- Gio hang session tu ban cu (dang list) van duoc doc va tu chuyen sang dinh dang moi.
