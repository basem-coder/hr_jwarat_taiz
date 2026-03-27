import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime
import os
import threading
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# --- إعدادات الخط العربي لـ PDF (ضروري لطباعة العربي) ---
try:
    # تأكد من وجود ملف arial.ttf في مجلد البرنامج
    pdfmetrics.registerFont(TTFont('ArabicFont', 'arial.ttf'))
except Exception as e:
    print(f"تنبيه: لم يتم تحميل الخط العربي: {e}")

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("Johara Taiz Mall Management System (v1.0) - Login")
        self.root.geometry("400x300")
        self.root.configure(bg="#213145")

        tk.Label(root, text="💎 وتسجيل الدخول", font=("Arial", 18, "bold"), fg="white", bg="#213145").pack(pady=20)
        
        tk.Label(root, text="اسم المستخدم:", fg="white", bg="#213145").pack()
        self.ent_user = tk.Entry(root, justify='center', font=("Arial", 12))
        self.ent_user.pack(pady=5)
        
        tk.Label(root, text="كلمة المرور:", fg="white", bg="#213145").pack()
        self.ent_pass = tk.Entry(root, show="*", justify='center', font=("Arial", 12))
        self.ent_pass.pack(pady=5)

        tk.Button(root, text="دخول", command=self.check_login, bg="#1E8449", fg="white", font=("Arial", 11), width=15).pack(pady=25)

    def check_login(self):
        # يمكنك تغيير اسم المستخدم وكلمة المرور هنا
        if self.ent_user.get() == "basem" and self.ent_pass.get() == "1234":
            self.on_success()
        else:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة!")

class JoharaMallSystem:
    def __init__(self, root):
        self.root = root
        # العنوان العلوي مطابق للصورة
        self.root.title("Johara Taiz Mall Management System (v1.0)")
        self.root.geometry("1100x800")
        self.db_name = "mall_management.db"
        self.init_db()

        # الألوان المعتمدة في التصميم (داكنة)
        self.bg_color = "#FFFFFF" # الخلفية البيضاء الأساسية للأقسام
        self.side_bg = "#213145" # لون الخلفية الداكن للأشرطة
        self.green_tab = "#117A65" # اللون الأخضر الداكن للتبويبات النشطة

        # --- إنشاء شريط العنوان العلوي الداكن ---
        top_bar = tk.Frame(self.root, bg=self.side_bg, height=60)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Label(top_bar, text="💎 Johara Taiz Mall", font=("Arial", 16, "bold"), fg="white", bg=self.side_bg).pack(side=tk.RIGHT, padx=20)
        
        # التاريخ والوقت العلوي (نموذجي)
        now_str = datetime.now().strftime("%Y - 05:23 |جمعة، 27 مارس 2026صباحاً")
        tk.Label(top_bar, text=now_str, font=("Arial", 12), fg="white", bg=self.side_bg).pack(side=tk.LEFT, padx=20)

        # --- إنشاء الأقسام الأربعة (Tabs) في الجهة اليمنى ---
        tabs_frame = tk.Frame(self.root, bg=self.side_bg, height=50)
        tabs_frame.pack(side=tk.TOP, fill=tk.X)
        tabs_frame.pack_propagate(False)

        # تصميم التبويبات مطابق للصورة
        tabs_data = [
            ("👤 الإعدادات & الأمان 4", "#0D0D0D", 1),
            ("📊 التقارير & الطباعة 3", "#0D0D0D", 1),
            ("👥 الموارد البشرية & السلف 2", "#0D0D0D", 1),
            ("💰 إدارة الخزينة 1", self.green_tab, 2)
        ]
        
        # إنشاء التبويبات كأزرار (لأن Kivy/Flet تناسب الأقسام الجانبية أكثر من ttk.Notebook في هذا التصميم المخصص)
        self.frames = {}
        for text, color, colspan in tabs_data:
            btn = tk.Button(tabs_frame, text=text, font=("Arial", 12, "bold"), fg="white", bg=color, bd=0, activebackground=color, activeforeground="white")
            btn.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- محتوى البرنامج الأوسط الأساسي ---
        main_content = tk.Frame(self.root, bg=self.bg_color)
        main_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # === 1. الملخص اللحظي (الجهة اليسرى) ===
        summary_left = tk.Frame(main_content, bg=self.bg_color, width=220)
        summary_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.create_summary_block(summary_left, "صافي العهدة الحالية", "1,250,000 ريال")
        self.create_summary_block(summary_left, "إجمالي إيرادات الشهر", "1,200,000 ريال")
        self.create_summary_block(summary_left, "إجمالي مصروفات الشهر", "500,000 ريال")
        
        tk.Label(summary_left, text="", bg=self.bg_color, height=2).pack() # فاصل

        self.create_summary_block(summary_left, "صافي العهدة الحالية", "1,250,000 ريال")
        self.create_summary_block(summary_left, "إجمالي إيرادات الشهر", "110,000 ريال")
        self.create_summary_block(summary_left, "إجمالي مصروفات الشهر", "20,000 ريال")

        # === 2. قسم الإدخال المخصص (في المنتصف) ===
        input_mid = tk.LabelFrame(main_content, text="إضافة حركة نقدية جديدة", font=("Arial", 12, "bold"), bg=self.bg_color)
        input_mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # نموذج الإدخال مطابق للصورة
        tk.Label(input_mid, text="التاريخ والوقت", bg=self.bg_color).pack(anchor="w", padx=20, pady=2)
        self.ent_date = tk.Entry(input_mid, justify='right', font=("Arial", 11))
        self.ent_date.insert(0, "التاريخ الحالي 2026") # نموذج
        self.ent_date.pack(fill=tk.X, padx=20)

        tk.Label(input_mid, text="(البيان (الاسم الدقيق", bg=self.bg_color).pack(anchor="w", padx=20, pady=2)
        self.ent_desc = tk.Entry(input_mid, justify='right', font=("Arial", 11))
        self.ent_desc.insert(0, "إيجار محل 102") # نموذج
        self.ent_desc.pack(fill=tk.X, padx=20)

        tk.Label(input_mid, text="(المبلغ (ريال", bg=self.bg_color).pack(anchor="w", padx=20, pady=2)
        self.ent_amt = tk.Entry(input_mid, justify='right', font=("Arial", 11))
        self.ent_amt.insert(0, "150,000") # نموذج
        self.ent_amt.pack(fill=tk.X, padx=20)

        tk.Label(input_mid, text="نوع العملية", bg=self.bg_color).pack(anchor="w", padx=20, pady=2)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(input_mid, textvariable=self.type_var, values=["إيراد", "مصروف", "توريد للمدير عمار"], state="readonly", font=("Arial", 11))
        self.type_combo.set("إيراد")
        self.type_combo.pack(fill=tk.X, padx=20)

        # زر قيد العملية الأوسع مطابق للصورة
        self.btn_save = tk.Button(input_mid, text="قيد العملية", command=self.add_transaction, bg="#1E8449", fg="white", font=("Arial", 12, "bold"))
        self.btn_save.pack(fill=tk.X, padx=20, pady=20)

        # === 3. جدول الحركات (في الجهة اليمنى) ===
        table_right = tk.LabelFrame(main_content, text="سجل الحركات الأخيرة", font=("Arial", 12, "bold"), bg=self.bg_color)
        table_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # إنشاء الجدول بنفس الأعمدة في الصورة (م، التاريخ، البيان، النوع، المبلغ)
        columns = ("ID", "Date", "Desc", "Type", "Amt")
        self.tree = ttk.Treeview(table_right, columns=columns, show='headings', height=15)
        
        # تنسيق رؤوس الأعمدة
        self.tree.heading("ID", text="م")
        self.tree.heading("Date", text="التاريخ")
        self.tree.heading("Desc", text="البيان")
        self.tree.heading("Type", text="النوع")
        self.tree.heading("Amt", text="(المبلغ (ريال")

        # تنسيق الأعمدة
        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Date", width=90, anchor="center")
        self.tree.column("Desc", width=120, anchor="center")
        self.tree.column("Type", width=70, anchor="center")
        self.tree.column("Amt", width=70, anchor="center")

        # تخصيص ألوان الأسطر المقلوبة مطابق للصورة (إيراد = أخضر، مصروف = أحمر)
        self.tree.tag_configure("إيراد", foreground="#1E8449", font=("Arial", 10, "bold"))
        self.tree.tag_configure("مصروف", foreground="#CB4335", font=("Arial", 10, "bold"))
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # تمرير الجدول
        sb = ttk.Scrollbar(table_right, orient=tk.VERTICAL, command=self.tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=sb.set)

        # إضافة بيانات عينة لمطابقة الصورة تماماً (مؤقتاً)
        self.add_mock_data()

        # --- إنشاء شريط الحالة السفلي الداكن ---
        status_bar = tk.Frame(self.root, bg=self.side_bg, height=40)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(status_bar, text="المستخدم الحالي: باسم حقيس (نائب المدير العام)", font=("Arial", 11), fg="white", bg=self.side_bg).pack(side=tk.RIGHT, padx=20)
        tk.Label(status_bar, text="✅ تم النسخ الاحتياطي بنجاح", font=("Arial", 11), fg="#1E8449", bg=self.side_bg).pack(side=tk.LEFT, padx=20)

    # دالة مساعدة لإنشاء قسم ملخص لحظي
    def create_summary_block(self, parent, title, value):
        tk.Label(parent, text=title, font=("Arial", 11, "bold"), fg="black", bg=self.bg_color).pack(pady=(5,0))
        tk.Label(parent, text=value, font=("Arial", 14), fg="black", bg=self.bg_color).pack()

    # إنشاء قاعدة البيانات (SQLite)
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, desc TEXT, type TEXT, amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, salary REAL, dept TEXT)''')
        conn.commit()
        conn.close()

    # دالة الحفظ
    def add_transaction(self):
        try:
            date_str = datetime.now().strftime("%Y - 05:23") # التاريخ الحالي مطابق للتنسيق
            desc = self.ent_desc.get()
            amt_str = self.ent_amt.get().replace(",","") # إزالة الفواصل
            amt = float(amt_str)
            ttype = self.type_var.get()

            # الحفظ في SQLite
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("INSERT INTO transactions (date, desc, type, amount) VALUES (?,?,?,?)", (date_str, desc, ttype, amt))
            conn.commit()
            conn.close()

            self.refresh_tree()
            messagebox.showinfo("نجاح", "تم قيد العملية في الخزينة")

        except Exception as e:
            messagebox.showerror("خطأ", f"تأكد من إدخال بيانات صحيحة: {e}")

    def refresh_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY id DESC")
        for row in c.fetchall():
            self.tree.insert("", 0, values=row, tags=(row[3],))
        conn.close()

    # إضافة بيانات عينة لمطابقة الصورة تماماً (يمكن حذفها عند بدء التشغيل الفعلي)
    def add_mock_data(self):
        # م البيانات لتظهر نفس الأسطر الموضحة في الصورة
        mock_entries = [
            ("2026", "سلفة ضياء", "إيراد", "150,000",1),
            ("2026", "إيجار محل 102", "إيراد", "25,000",2),
            ("2026", "إيجار محل 102", "إيراد", "150,000",3),
            ("2026", "سلفة ضياء", "مصروف", "25,000",4),
            ("2026", "إيجار محل 102", "إيراد", "150,000",5),
            ("2026", "سلفة ضياء", "مصروف", "25,000",6),
            ("2026", "إيجار محل 102", "إيراد", "150,000",7),
            ("2026", "سلفة ضياء", "مصروف", "25,000",8),
            ("2026", "إيجار محل 102", "إيراد", "150,000",9),
            ("2026", "سلفة ضياء", "مصروف", "25,000",10),
            ("2026", "إيجار محل 102", "إيراد", "150,000",11),
            ("2026", "سلفة ضياء", "إيراد", "150,000",12),
        ]
        
        # الترتيب في الصورة يبدأ من الأحدث إلى الأقدم
        for date, desc, ttype, amt, i in reversed(mock_entries):
            # م (م الرقم التسلسلي هو ID)
            self.tree.insert("", 0, values=(i, date, desc, ttype, amt), tags=(ttype,))

def run_main_app():
    login_win.destroy()
    main_root = tk.Tk()
    app = JoharaMallSystem(main_root)
    main_root.mainloop()

if __name__ == "__main__":
    login_win = tk.Tk()
    LoginWindow(login_win, run_main_app)
    login_win.mainloop()
