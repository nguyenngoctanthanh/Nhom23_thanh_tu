import tkinter as tk
from tkinter import messagebox, ttk
import hashlib
import json
import os
import uuid
import re
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import requests

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

DATA_FILE = "data/books.json"
USER_FILE = "data/users.json"
BORROW_FILE = "data/borrows.json"
BG_IMAGE = "bg3.jpg"
STATS_IMAGE = "data/stats.png"

os.makedirs("data", exist_ok=True)

def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Quản Lý Thư Viện")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.user_role = None
        self.username = None
        self.books = []
        self.borrows = []
        self.canvas = None
        self.load_data()
        self.login_screen()
        self.root.bind("<Configure>", self.handle_resize)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.books = json.load(f)
        else:
            self.books = []
        
        if os.path.exists(BORROW_FILE):
            with open(BORROW_FILE, "r", encoding="utf-8") as f:
                self.borrows = json.load(f)
        else:
            self.borrows = []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.books, f, indent=4, ensure_ascii=False)
        with open(BORROW_FILE, "w", encoding="utf-8") as f:
            json.dump(self.borrows, f, indent=4, ensure_ascii=False)
        if hasattr(self, 'users') and self.users:
            with open(USER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)

    def handle_resize(self, event):
        if not hasattr(self, 'canvas') or self.canvas is None or not self.canvas.winfo_exists():
            return
        
        try:
            win_width = self.root.winfo_width()
            win_height = self.root.winfo_height()
            if os.path.exists(BG_IMAGE):
                bg = Image.open(BG_IMAGE)
                bg = bg.resize((win_width, win_height), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(bg)
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
            else:
                self.canvas.delete("all")
                for i in range(win_height):
                    blue = int(255 * (i / win_height))
                    color = f"#{0:02x}{0:02x}{blue:02x}"
                    self.canvas.create_line(0, i, win_width, i, fill=color)
        except Exception as e:
            print(f"Error in handle_resize: {e}")

    def set_background(self):
        try:
            if os.path.exists(BG_IMAGE):
                bg = Image.open(BG_IMAGE)
                bg = bg.resize((self.root.winfo_width(), self.root.winfo_height()), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(bg)
                self.canvas = tk.Canvas(self.root, width=self.root.winfo_width(), height=self.root.winfo_height(), highlightthickness=0)
                self.canvas.pack(fill="both", expand=False)
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
            else:
                raise FileNotFoundError(f"Background image {BG_IMAGE} not found.")
        except Exception as e:
            print(f"Error setting background image: {e}. Using gradient.")
            self.canvas = tk.Canvas(self.root, width=self.root.winfo_width(), height=self.root.winfo_height(), highlightthickness=0)
            self.canvas.pack(fill="both", expand=False)
            for i in range(self.root.winfo_height()):
                blue = int(255 * (i / self.root.winfo_height()))
                color = f"#{0:02x}{0:02x}{blue:02x}"
                self.canvas.create_line(0, i, self.root.winfo_width(), i, fill=color)

    def login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.set_background()

        login_frame = ttk.Frame(self.root, padding=20, style="Login.TFrame")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        style = ttk.Style()
        style.configure("Login.TFrame", background="white")
        style.configure("TLabel", font=("Arial", 12), background="white")
        style.configure("TEntry", padding=5, font=("Arial", 11))
        style.configure("Login.TButton", font=("Arial", 11), background="#4CAF50", foreground="black")
        style.configure("Register.TButton", font=("Arial", 11), background="#2196F3", foreground="black")
        style.configure("Crawl.TButton", font=("Arial", 11), background="#FF9800", foreground="black")
        style.map("Login.TButton", background=[('active', '#388E3C')])
        style.map("Register.TButton", background=[('active', '#1976D2')])
        style.map("Crawl.TButton", background=[('active', '#F57C00')])

        login_frame.grid_columnconfigure(0, weight=1)
        login_frame.grid_columnconfigure(1, weight=1)
        login_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        ttk.Label(login_frame, text="HỆ THỐNG QUẢN LÝ THƯ VIỆN", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(login_frame, text="Tên Đăng Nhập").grid(row=1, column=0, pady=10, sticky="e")
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=1, column=1, pady=10, sticky="w")

        ttk.Label(login_frame, text="Mật Khẩu").grid(row=2, column=0, pady=10, sticky="e")
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=2, column=1, pady=10, sticky="w")

        self.show_password_var = tk.IntVar()
        ttk.Checkbutton(login_frame, text="Hiện Mật Khẩu", variable=self.show_password_var, command=self.toggle_password).grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(login_frame, text="Đăng Nhập", style="Login.TButton", command=self.login).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(login_frame, text="Đăng Ký", style="Register.TButton", command=self.register_screen).grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(login_frame, text="Crawl Books", style="Crawl.TButton", command=self.crawl_and_update).grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def crawl_and_update(self):
        try:
            api_key = "AIzaSyBrhZvBOwMOMFRTNbYdsN4OVmf7TDBmxCs"
            if not api_key:
                raise ValueError("API key không được cung cấp.")

            url = f"https://www.googleapis.com/books/v1/volumes?q=python+programming&key={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            if not items:
                messagebox.showinfo("Thông Báo", "Không tìm thấy sách nào.")
                return

            books_added = 0
            for item in items[:20]:  # Giới hạn lấy 20 cuốn sách
                volume_info = item.get("volumeInfo", {})
                title = volume_info.get("title", "Tiêu Đề Không Xác Định")
                authors = volume_info.get("authors", ["Tác Giả Không Xác Định"])
                category = volume_info.get("categories", ["Chung"])[0] if "categories" in volume_info else "Chung"
                publisher = volume_info.get("publisher", "NXB Không Xác Định")
                year = volume_info.get("publishedDate", "N/A")[:4]

                if not any(book["title"] == title for book in self.books):
                    self.books.append({
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "author": ", ".join(authors),
                        "category": category,
                        "status": "available",
                        "quantity": 1,
                        "publisher": publisher,
                        "year": year
                    })
                    books_added += 1

            if books_added == 0:
                messagebox.showinfo("Thông Báo", "Không có sách mới để thêm (tất cả đã tồn tại).")
            else:
                self.save_data()
                messagebox.showinfo("Thành Công", f"Đã thêm {books_added} cuốn sách thành công.")

            if hasattr(self, 'tree') and self.tree.winfo_exists():
                self.update_book_list()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi Kết Nối", f"Không thể kết nối đến Google Books API: {str(e)}")
        except ValueError as e:
            messagebox.showerror("Lỗi API Key", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi thu thập sách: {str(e)}")

    def register_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.set_background()
        reg_frame = ttk.Frame(self.root, padding=20, style="Login.TFrame")
        reg_frame.place(relx=0.5, rely=0.5, anchor="center")

        style = ttk.Style()
        style.configure("Login.TFrame", background="white")
        style.configure("TLabel", font=("Arial", 12), background="white")
        style.configure("TEntry", padding=5, font=("Arial", 11))

        reg_frame.grid_columnconfigure(0, weight=1)
        reg_frame.grid_columnconfigure(1, weight=1)
        reg_frame.grid_rowconfigure(tuple(range(9)), weight=1)

        self.reg_username = tk.StringVar()
        self.reg_password = tk.StringVar()
        self.reg_name = tk.StringVar()
        self.reg_phone = tk.StringVar()
        self.reg_email = tk.StringVar()
        self.reg_address = tk.StringVar()
        self.reg_role = tk.StringVar(value="docgia")

        fields = [
            ("Tên Đăng Nhập", self.reg_username),
            ("Mật Khẩu", self.reg_password),
            ("Họ Tên", self.reg_name),
            ("Số Điện Thoại", self.reg_phone),
            ("Email", self.reg_email),
            ("Địa Chỉ", self.reg_address),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(reg_frame, text=label).grid(row=i, column=0, pady=10, sticky="e")
            ttk.Entry(reg_frame, textvariable=var).grid(row=i, column=1, pady=10, sticky="w")

        ttk.Label(reg_frame, text="Vai Trò").grid(row=len(fields), column=0, pady=10, sticky="e")
        ttk.OptionMenu(reg_frame, self.reg_role, "docgia", "admin", "thuthu").grid(row=len(fields), column=1, pady=10, sticky="w")

        ttk.Button(reg_frame, text="Đăng Ký", style="Register.TButton", command=self.register).grid(row=len(fields)+1, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(reg_frame, text="Quay Lại", style="Login.TButton", command=self.login_screen).grid(row=len(fields)+2, column=0, columnspan=2, pady=10, sticky="ew")

    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()
        name = self.reg_name.get()
        phone = self.reg_phone.get()
        email = self.reg_email.get()
        address = self.reg_address.get()
        role = self.reg_role.get()

        if not all([username, password, name, phone, email, address, role]):
            messagebox.showwarning("Thiếu Thông Tin", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&]).+$", password):
            messagebox.showwarning("Mật Khẩu Không Hợp Lệ", "Mật khẩu phải chứa chữ cái, số và ký tự đặc biệt (@$!%*?&).")
            return

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            messagebox.showwarning("Email Không Hợp Lệ", "Vui lòng nhập email đúng định dạng (ví dụ: user@domain.com).")
            return

        if not re.match(r"^0[3928]\d{8}$", phone):
            messagebox.showwarning("Số Điện Thoại Không Hợp Lệ", "Số điện thoại phải có 10 chữ số và bắt đầu bằng 03, 09, 02 hoặc 08.")
            return

        self.users = []
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r", encoding="utf-8") as f:
                self.users = json.load(f)

        for user in self.users:
            if user["username"] == username:
                messagebox.showwarning("Lỗi", "Tên đăng nhập đã tồn tại.")
                return

        self.users.append({
            "username": username,
            "password": hash_password(password),
            "role": role,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address
        })

        self.save_data()
        messagebox.showinfo("Thành Công", "Đăng ký thành công. Vui lòng đăng nhập.")
        self.login_screen()

    def login(self):
        username = self.username_entry.get()
        password = hash_password(self.password_entry.get())

        if not os.path.exists(USER_FILE):
            messagebox.showerror("Lỗi", "Không có dữ liệu người dùng.")
            return

        with open(USER_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

        for user in users:
            if user["username"] == username and user["password"] == password:
                self.user_role = user["role"]
                self.username = username
                self.main_screen()
                return

        messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng.")

    def main_screen(self):
        self.root.unbind("<Configure>")
        self.canvas = None
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        main_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 14), background="#F0F8FF")
        style.configure("Title.TLabel", font=("Arial", 18, "bold"), foreground="#FFD700", background="#1E1E1E")
        style.configure("TButton", font=("Arial", 12), padding=10, background="#FFD700", foreground="black")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])

        title_frame = ttk.Frame(main_frame, style="Main.TFrame")
        title_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(title_frame, text="HỆ THỐNG QUẢN LÝ THƯ VIỆN", style="Title.TLabel").pack()

        welcome_frame = ttk.Frame(main_frame, style="Main.TFrame")
        welcome_frame.pack(fill="x", pady=10)
        ttk.Label(welcome_frame, text=f"Chào mừng, {self.username} ({self.user_role})", font=("Arial", 16, "bold")).pack()

        button_frame = ttk.Frame(main_frame, style="Main.TFrame")
        button_frame.pack(fill="both", expand=True, pady=10)

        button_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="button")
        button_frame.grid_rowconfigure((0, 1, 2), weight=1)

        if self.user_role == "admin":
            ttk.Label(welcome_frame, text="(Quản lý toàn bộ hệ thống)", font=("Arial", 12, "italic")).pack()
            ttk.Button(button_frame, text="Quản Lý Sách", command=self.manage_books).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            ttk.Button(button_frame, text="Thống Kê Sách", command=self.stats_screen).grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
            ttk.Button(button_frame, text="Quản Lý Mượn Sách", command=self.manage_borrows).grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        elif self.user_role == "thuthu":
            ttk.Label(welcome_frame, text="(Quản lý sách và mượn sách)", font=("Arial", 12, "italic")).pack()
            ttk.Button(button_frame, text="Quản Lý Sách", command=self.manage_books).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            ttk.Button(button_frame, text="Quản Lý Mượn Sách", command=self.manage_borrows).grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        elif self.user_role == "docgia":
            ttk.Label(welcome_frame, text="(Tìm kiếm và mượn sách)", font=("Arial", 12, "italic")).pack()
            ttk.Button(button_frame, text="Tìm Kiếm Sách", command=self.search_books_screen).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            ttk.Button(button_frame, text="Sách Đang Mượn", command=self.my_borrows).grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        logout_frame = ttk.Frame(main_frame, style="Main.TFrame")
        logout_frame.pack(fill="x", pady=10)
        ttk.Button(logout_frame, text="Đăng Xuất", command=self.login_screen).pack()

    def manage_books(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        book_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        book_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 12), background="#F0F8FF")
        style.configure("TEntry", padding=5, font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11), background="#FFD700", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#D3D3D3", foreground="black")
        style.configure("Treeview", font=("Arial", 11), rowheight=25, background="white", fieldbackground="white")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])
        style.map("Treeview", background=[('selected', '#ADD8E6')])

        book_frame.grid_columnconfigure(0, weight=1)
        book_frame.grid_columnconfigure(1, weight=1)
        book_frame.grid_rowconfigure(tuple(range(8)), weight=1)

        ttk.Label(book_frame, text="QUẢN LÝ SÁCH", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        columns = ("ID", "Tiêu Đề", "Tác Giả", "Thể Loại", "Trạng Thái", "Số Lượng", "NXB", "Năm SX")
        self.tree = ttk.Treeview(book_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")

        fields = [
            ("Tiêu Đề", "book_title"),
            ("Tác Giả", "book_author"),
            ("Thể Loại", "book_category"),
            ("Số Lượng", "book_quantity"),
            ("NXB", "book_publisher"),
            ("Năm SX", "book_year")
        ]

        for i, (label, var_name) in enumerate(fields, start=2):
            ttk.Label(book_frame, text=label).grid(row=i, column=0, pady=5, sticky="e")
            setattr(self, var_name, tk.StringVar())
            ttk.Entry(book_frame, textvariable=getattr(self, var_name)).grid(row=i, column=1, pady=5, sticky="w")

        button_frame = ttk.Frame(book_frame, style="Main.TFrame")
        button_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(button_frame, text="Thêm Sách", command=self.add_book).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Sửa Sách", command=self.edit_book).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Xóa Sách", command=self.delete_book).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Quay Lại", command=self.main_screen).grid(row=0, column=3, padx=5)

        self.update_book_list()

    def add_book(self):
        title = self.book_title.get()
        author = self.book_author.get()
        category = self.book_category.get()
        quantity = self.book_quantity.get()
        publisher = self.book_publisher.get()
        year = self.book_year.get()

        if not all([title, author, category, quantity, publisher, year]):
            messagebox.showwarning("Thiếu Thông Tin", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Số Lượng Không Hợp Lệ", "Số lượng phải là số nguyên dương.")
            return

        try:
            year = int(year)
            if year < 1800 or year > int(datetime.now().strftime("%Y")):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Năm SX Không Hợp Lệ", f"Năm SX phải là số từ 1800 đến {datetime.now().strftime('%Y')}.")
            return

        book = {
            "id": str(uuid.uuid4()),
            "title": title,
            "author": author,
            "category": category,
            "status": "available",
            "quantity": quantity,
            "publisher": publisher,
            "year": year
        }
        self.books.append(book)
        self.save_data()
        self.update_book_list()
        self.book_title.set("")
        self.book_author.set("")
        self.book_category.set("")
        self.book_quantity.set("")
        self.book_publisher.set("")
        self.book_year.set("")
        messagebox.showinfo("Thành Công", "Đã thêm sách thành công.")

    def edit_book(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cuốn sách để sửa.")
            return

        book_id = self.tree.item(selected)["values"][0]
        title = self.book_title.get()
        author = self.book_author.get()
        category = self.book_category.get()
        quantity = self.book_quantity.get()
        publisher = self.book_publisher.get()
        year = self.book_year.get()

        if not all([title, author, category, quantity, publisher, year]):
            messagebox.showwarning("Thiếu Thông Tin", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Số Lượng Không Hợp Lệ", "Số lượng phải là số nguyên dương.")
            return

        try:
            year = int(year)
            if year < 1800 or year > int(datetime.now().strftime("%Y")):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Năm SX Không Hợp Lệ", f"Năm SX phải là số từ 1800 đến {datetime.now().strftime('%Y')}.")
            return

        for book in self.books:
            if book["id"] == book_id:
                book["title"] = title
                book["author"] = author
                book["category"] = category
                book["quantity"] = quantity
                book["publisher"] = publisher
                book["year"] = year
                break

        self.save_data()
        self.update_book_list()
        self.book_title.set("")
        self.book_author.set("")
        self.book_category.set("")
        self.book_quantity.set("")
        self.book_publisher.set("")
        self.book_year.set("")
        messagebox.showinfo("Thành Công", "Đã cập nhật sách thành công.")

    def delete_book(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cuốn sách để xóa.")
            return

        book_id = self.tree.item(selected)["values"][0]
        if any(borrow["book_id"] == book_id and not borrow["returned"] for borrow in self.borrows):
            messagebox.showwarning("Lỗi", "Không thể xóa sách đang được mượn.")
            return

        self.books = [book for book in self.books if book["id"] != book_id]
        self.save_data()
        self.update_book_list()
        messagebox.showinfo("Thành Công", "Đã xóa sách thành công.")

    def update_book_list(self):
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for book in self.books:
            status = "Có Sẵn" if book["status"] == "available" else "Đang Mượn"
            self.tree.insert("", "end", values=(
                book["id"],
                book["title"],
                book["author"],
                book["category"],
                status,
                book["quantity"],
                book["publisher"],
                book["year"]
            ))

    def search_books_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        search_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        search_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 12), background="#F0F8FF")
        style.configure("TEntry", padding=5, font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11), background="#FFD700", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#D3D3D3", foreground="black")
        style.configure("Treeview", font=("Arial", 11), rowheight=25, background="white", fieldbackground="white")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])
        style.map("Treeview", background=[('selected', '#ADD8E6')])

        search_frame.grid_columnconfigure(0, weight=1)
        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_rowconfigure(tuple(range(7)), weight=1)

        ttk.Label(search_frame, text="TÌM KIẾM SÁCH", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(search_frame, text="ID").grid(row=1, column=0, pady=10, sticky="e")
        self.search_id = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_id).grid(row=1, column=1, pady=10, sticky="w")
        ttk.Label(search_frame, text="Từ Khóa").grid(row=2, column=0, pady=10, sticky="e")
        self.search_term = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_term).grid(row=2, column=1, pady=10, sticky="w")
        ttk.Label(search_frame, text="Thể Loại").grid(row=3, column=0, pady=10, sticky="e")
        self.search_category = tk.StringVar()
        categories = list(set(book["category"] for book in self.books)) + ["Tất Cả"]
        ttk.Combobox(search_frame, textvariable=self.search_category, values=categories).grid(row=3, column=1, pady=10, sticky="w")

        columns = ("ID", "Tiêu Đề", "Tác Giả", "Thể Loại", "Trạng Thái", "Số Lượng", "NXB", "Năm SX")
        self.search_tree = ttk.Treeview(search_frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=100, anchor="center")
        self.search_tree.grid(row=4, column=0, columnspan=2, pady=10, sticky="nsew")

        ttk.Button(search_frame, text="Tìm Kiếm", command=self.search_books).grid(row=5, column=0, pady=10)
        ttk.Button(search_frame, text="Mượn Sách", command=self.borrow_book).grid(row=5, column=1, pady=10)
        ttk.Button(search_frame, text="Quay Lại", command=self.main_screen).grid(row=6, column=0, columnspan=2, pady=10)

        self.search_books()

    def search_books(self):
        term = self.search_term.get().lower()
        book_id = self.search_id.get().lower()
        category = self.search_category.get()

        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        for book in self.books:
            if ((not term or term in book["title"].lower() or term in book["author"].lower()) and
                (not book_id or book_id in book["id"].lower()) and
                (category == "Tất Cả" or not category or book["category"] == category)):
                status = "Có Sẵn" if book["status"] == "available" else "Đang Mượn"
                self.search_tree.insert("", "end", values=(
                    book["id"],
                    book["title"],
                    book["author"],
                    book["category"],
                    status,
                    book["quantity"],
                    book["publisher"],
                    book["year"]
                ))

    def borrow_book(self):
        if self.user_role != "docgia":
            messagebox.showwarning("Không Có Quyền", "Chỉ độc giả mới có thể mượn sách.")
            return

        selected = self.search_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cuốn sách để mượn.")
            return

        book_id = self.search_tree.item(selected)["values"][0]
        book = next((b for b in self.books if b["id"] == book_id), None)
        if not book or book["status"] != "available":
            messagebox.showwarning("Lỗi", "Sách không có sẵn để mượn.")
            return

        borrow = {
            "id": str(uuid.uuid4()),
            "book_id": book_id,
            "username": self.username,
            "borrow_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "returned": False
        }
        self.borrows.append(borrow)
        book["status"] = "borrowed"
        self.save_data()
        self.search_books()
        messagebox.showinfo("Thành Công", "Đã mượn sách thành công.")

    def manage_borrows(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        borrow_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        borrow_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 12), background="#F0F8FF")
        style.configure("TButton", font=("Arial", 11), background="#FFD700", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#D3D3D3", foreground="black")
        style.configure("Treeview", font=("Arial", 11), rowheight=25, background="white", fieldbackground="white")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])
        style.map("Treeview", background=[('selected', '#ADD8E6')])

        borrow_frame.grid_columnconfigure(0, weight=1)
        borrow_frame.grid_columnconfigure(1, weight=1)
        borrow_frame.grid_rowconfigure((0, 1), weight=1)

        columns = ("ID", "Tiêu Đề Sách", "Tên Người Mượn", "Ngày Mượn", "Ngày Trả", "Trạng Thái")
        self.borrow_tree = ttk.Treeview(borrow_frame, columns=columns, show="headings")
        for col in columns:
            self.borrow_tree.heading(col, text=col)
            self.borrow_tree.column(col, width=100, anchor="center")
        self.borrow_tree.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")

        ttk.Label(borrow_frame, text="QUẢN LÝ MƯỢN SÁCH", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Button(borrow_frame, text="Trả Sách", command=self.return_book).grid(row=2, column=0, pady=10)
        ttk.Button(borrow_frame, text="Quay Lại", command=self.main_screen).grid(row=2, column=1, pady=10)

        self.update_borrow_list()

    def update_borrow_list(self):
        if not hasattr(self, 'borrow_tree') or not self.borrow_tree.winfo_exists():
            return
        for item in self.borrow_tree.get_children():
            self.borrow_tree.delete(item)
        for borrow in self.borrows:
            book = next((b for b in self.books if b["id"] == borrow["book_id"]), None)
            if book:
                status = "Đã Trả" if borrow["returned"] else "Chưa Trả"
                self.borrow_tree.insert("", "end", values=(
                    borrow["id"],
                    book["title"],
                    borrow["username"],
                    borrow["borrow_date"],
                    borrow["due_date"],
                    status
                ))

    def return_book(self):
        selected = self.borrow_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một khoản mượn để trả.")
            return

        borrow_id = self.borrow_tree.item(selected)["values"][0]
        borrow = next((b for b in self.borrows if b["id"] == borrow_id), None)
        if borrow and not borrow["returned"]:
            borrow["returned"] = True
            book = next((b for b in self.books if b["id"] == borrow["book_id"]), None)
            if book:
                book["status"] = "available"
            self.save_data()
            self.update_borrow_list()
            messagebox.showinfo("Thành Công", "Đã trả sách thành công.")
        else:
            messagebox.showwarning("Lỗi", "Khoản mượn đã được trả hoặc không tồn tại.")

    def my_borrows(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        my_borrow_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        my_borrow_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 12), background="#F0F8FF")
        style.configure("TButton", font=("Arial", 11), background="#FFD700", foreground="black")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#D3D3D3", foreground="black")
        style.configure("Treeview", font=("Arial", 11), rowheight=25, background="white", fieldbackground="white")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])
        style.map("Treeview", background=[('selected', '#ADD8E6')])

        my_borrow_frame.grid_columnconfigure(0, weight=1)
        my_borrow_frame.grid_columnconfigure(1, weight=1)
        my_borrow_frame.grid_rowconfigure((0, 1), weight=1)

        columns = ("ID", "Tiêu Đề Sách", "Ngày Mượn", "Ngày Trả", "Trạng Thái")
        self.my_borrow_tree = ttk.Treeview(my_borrow_frame, columns=columns, show="headings")
        for col in columns:
            self.my_borrow_tree.heading(col, text=col)
            self.my_borrow_tree.column(col, width=100, anchor="center")
        self.my_borrow_tree.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")

        ttk.Label(my_borrow_frame, text="SÁCH ĐANG MƯỢN", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Button(my_borrow_frame, text="Quay Lại", command=self.main_screen).grid(row=2, column=0, columnspan=2, pady=10)

        self.update_my_borrow_list()

    def update_my_borrow_list(self):
        if not hasattr(self, 'my_borrow_tree') or not self.my_borrow_tree.winfo_exists():
            return
        for item in self.my_borrow_tree.get_children():
            self.my_borrow_tree.delete(item)
        for borrow in self.borrows:
            if borrow["username"] == self.username and not borrow["returned"]:
                book = next((b for b in self.books if b["id"] == borrow["book_id"]), None)
                if book:
                    status = "Chưa Trả"
                    self.my_borrow_tree.insert("", "end", values=(
                        borrow["id"],
                        book["title"],
                        borrow["borrow_date"],
                        borrow["due_date"],
                        status
                    ))

    def stats_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        stats_frame = ttk.Frame(self.root, padding=20, style="Main.TFrame")
        stats_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Main.TFrame", background="#F0F8FF")
        style.configure("TLabel", font=("Arial", 12), background="#F0F8FF")
        style.configure("Title.TLabel", font=("Arial", 16, "bold"), foreground="#FFD700", background="#1E1E1E")
        style.configure("TButton", font=("Arial", 11), background="#FFD700", foreground="black")
        style.map("TButton", background=[('active', '#FFA500')], foreground=[('active', 'white')])

        ttk.Label(stats_frame, text="THỐNG KÊ SÁCH", style="Title.TLabel").pack(pady=10)

        if MATPLOTLIB_AVAILABLE:
            available = len([b for b in self.books if b["status"] == "available"])
            borrowed = len(self.books) - available

            plt.figure(figsize=(8, 6))
            plt.pie([available, borrowed], labels=["Có Sẵn", "Đang Mượn"], autopct="%1.1f%%", colors=["#4CAF50", "#F44336"])
            plt.title("Tỷ Lệ Sách Có Sẵn và Đang Mượn")
            plt.savefig(STATS_IMAGE)
            plt.close()

            if os.path.exists(STATS_IMAGE):
                stats_img = Image.open(STATS_IMAGE)
                stats_img = stats_img.resize((400, 300), Image.LANCZOS)
                self.stats_photo = ImageTk.PhotoImage(stats_img)
                stats_label = tk.Label(stats_frame, image=self.stats_photo)
                stats_label.image = self.stats_photo
                stats_label.pack(pady=10)
        else:
            ttk.Label(stats_frame, text="Matplotlib không được cài đặt. Không thể hiển thị thống kê.").pack(pady=10)

        ttk.Button(stats_frame, text="Quay Lại", command=self.main_screen).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()