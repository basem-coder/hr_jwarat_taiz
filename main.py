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

# --- إعدادات الخط العربي لـ PDF ---
try:
    pdfmetrics.registerFont(TTFont('ArabicFont', 'arial.ttf'))
except:
    print("تنبيه: ملف arial.ttf غير موجود.")

# ================= كلاس شاشة الدخول =================
class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("دخول النظام - جوهرة تعز مول")
        self.root.geometry("400x300")
        self.root.configure(bg="#2c3e50")

        tk.Label(root, text="تسجيل الدخول", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(pady=20)
        
        tk.Label(root, text="اسم المستخدم:", fg="white", bg="#2c3e50").pack()
        self.ent_user = tk.Entry(root, justify='center')
        self.ent_user.pack(pady=5)
        
        tk.Label(root, text="كلمة المرور:", fg="white", bg="#2c3e50").pack()
        self.ent_pass = tk.Entry(root, show="*", justify='center')
        self.ent_pass.pack(pady=5)

        tk.Button(root, text="دخول", command=self.check_login, bg="#27ae60", fg="white", width=15).pack(pady=20)

    def check_login(self):
        # يمكنك تغيير اسم المستخدم وكلمة المرور هنا
        if self.ent_user.get() == "basem" and self.ent_pass.get() == "1234":
            self.on_success()
        else:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة!")

# ================= كلاس النظام الرئيسي =================
class JoharaMallSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام الإدارة المتكامل - جوهرة تعز مول (الإصدار النهائي)")
        self.root.geometry("1100x800")
        self.db_name = "mall_management.db"
        self.init_db()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_treasury = ttk.Frame(self.notebook)
        self.tab_hr = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_treasury, text=" إدارة الخزينة ")
        self.notebook.add(self.tab_hr, text=" الموارد البشرية والسلف ")
        self.notebook.add(self.tab_reports, text=" التقارير والطباعة ")

        self.setup_treasury_ui()
        self.setup_hr_ui()
        self.setup_reports_ui()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, date TEXT, desc TEXT, type TEXT, amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, job TEXT, salary REAL, dept TEXT, phone TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, emp_name TEXT, amount REAL, date TEXT)''')
        conn.commit()
        conn.close()

    # --- واجهة الخزينة ---
    def setup_treasury_ui(self):
        frame = tk.LabelFrame(self.tab_treasury, text="إضافة حركة مالية", padx=10, pady=10)
        frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(frame, text="البيان:").grid(row=0, column=5)
        self.ent_desc = tk.Entry(frame, justify='right')
        self.ent_desc.grid(row=0, column=4, padx=5)

        tk.Label(frame, text="المبلغ:").grid(row=0, column=3)
        self.ent_amt = tk.Entry(frame, justify='right')
        self.ent_amt.grid(row=0, column=2, padx=5)

        self.type_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self.type_var, values=["إيراد", "توريد للمدير عمار", "مصروف جانبي"], state="readonly").grid(row=0, column=1)
        
        tk.Button(frame, text="حفظ العملية", bg="#27ae60", fg="white", command=self.add_transaction).grid(row=0, column=0, padx=10)

        self.tree_trans = ttk.Treeview(self.tab_treasury, columns=("ID", "Date", "Desc", "Type", "Amt"), show='headings')
        for col, txt in zip(self.tree_trans["columns"], ["م", "التاريخ", "البيان", "النوع", "المبلغ"]):
            self.tree_trans.heading(col, text=txt)
        self.tree_trans.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        self.refresh_treasury()

    def add_transaction(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("INSERT INTO transactions (date, desc, type, amount) VALUES (?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d %H:%M"), self.ent_desc.get(), self.type_var.get(), float(self.ent_amt.get())))
            conn.commit()
            conn.close()
            self.refresh_treasury()
            messagebox.showinfo("نجاح", "تم الحفظ بنجاح")
        except:
            messagebox.showerror("خطأ", "تأكد من إدخال بيانات صحيحة")

    def refresh_treasury(self):
        for i in self.tree_trans.get_children(): self.tree_trans.delete(i)
        conn = sqlite3.connect(self.db_name)
        for row in conn.execute("SELECT * FROM transactions ORDER BY id DESC"): self.tree_trans.insert("", 0, values=row)
        conn.close()

    # --- واجهة HR والسلف ---
    def setup_hr_ui(self):
        f1 = tk.LabelFrame(self.tab_hr, text="إدارة الموظفين", padx=10, pady=10)
        f1.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(f1, text="الاسم:").grid(row=0, column=5)
        self.ent_emp_name = tk.Entry(f1, justify='right')
        self.ent_emp_name.grid(row=0, column=4, padx=5)

        tk.Label(f1, text="الراتب الأساسي:").grid(row=0, column=3)
        self.ent_emp_sal = tk.Entry(f1, justify='right')
        self.ent_emp_sal.grid(row=0, column=2, padx=5)

        self.emp_dept = tk.StringVar()
        depts = ["صالة الألعاب", "إدارة جوهرة تعز مول", "شركة الأمن النسيم", "شركة النظافة"]
        ttk.Combobox(f1, textvariable=self.emp_dept, values=depts, state="readonly").grid(row=0, column=1)
        
        tk.Button(f1, text="إضافة موظف", command=self.add_employee, bg="#2980b9", fg="white").grid(row=0, column=0, padx=10)

        f2 = tk.LabelFrame(self.tab_hr, text="تسجيل سلفة", padx=10, pady=10)
        f2.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(f2, text="اسم الموظف:").grid(row=0, column=3)
        self.loan_name = tk.Entry(f2, justify='right')
        self.loan_name.grid(row=0, column=2)
        
        tk.Label(f2, text="مبلغ السلفة:").grid(row=0, column=1)
        self.loan_amt = tk.Entry(f2, width=10)
        self.loan_amt.grid(row=0, column=0)
        
        tk.Button(f2, text="قيد السلفة وخصمها من الخزينة", command=self.add_loan, bg="#d35400", fg="white").grid(row=1, column=0, pady=10)

    def add_employee(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("INSERT INTO employees (name, salary, dept) VALUES (?,?,?)",
                     (self.ent_emp_name.get(), float(self.ent_emp_sal.get()), self.emp_dept.get()))
        conn.commit()
        conn.close()
        messagebox.showinfo("HR", "تم الحفظ")

    def add_loan(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        name, amt = self.loan_name.get(), float(self.loan_amt.get())
        c.execute("INSERT INTO loans (emp_name, amount, date) VALUES (?,?,?)", (name, amt, datetime.now().strftime("%Y-%m-%d")))
        c.execute("INSERT INTO transactions (date, desc, type, amount) VALUES (?,?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d"), f"سلفة: {name}", "مصروف جانبي", amt))
        conn.commit()
        conn.close()
        self.refresh_treasury()
        messagebox.showinfo("سلف", "تم القيد والخصم")

    # --- التقارير والطباعة ---
    def setup_reports_ui(self):
        f = tk.LabelFrame(self.tab_reports, text="استخراج الكشوفات والتقارير", padx=20, pady=20)
        f.pack(pady=20, padx=20, fill=tk.X)

        tk.Label(f, text="اختر القسم:").pack()
        self.rep_dept = tk.StringVar()
        depts = ["صالة الألعاب", "إدارة جوهرة تعز مول", "شركة الأمن النسيم", "شركة النظافة"]
        ttk.Combobox(f, textvariable=self.rep_dept, values=depts, state="readonly", width=30).pack(pady=10)

        tk.Button(f, text="تصدير كشف الراتب الموحد (Excel)", command=self.export_excel, bg="#27ae60", fg="white", width=30).pack(pady=5)
        tk.Button(f, text="طباعة كشف الراتب الموحد (PDF)", command=self.export_pdf, bg="#c0392b", fg="white", width=30).pack(pady=5)

    def get_payroll_df(self):
        dept = self.rep_dept.get()
        conn = sqlite3.connect(self.db_name)
        df_emp = pd.read_sql_query(f"SELECT name, salary FROM employees WHERE dept='{dept}'", conn)
        results = []
        for _, row in df_emp.iterrows():
            loan = conn.execute(f"SELECT SUM(amount) FROM loans WHERE emp_name='{row['name']}'").fetchone()[0] or 0
            results.append({"الموظف": row['name'], "الراتب": row['salary'], "السلف": loan, "الصافي": row['salary']-loan})
        conn.close()
        return pd.DataFrame(results)

    def export_excel(self):
        df = self.get_payroll_df()
        path = f"Kashf_{self.rep_dept.get()}.xlsx"
        df.to_excel(path, index=False)
        os.startfile(path)

    def export_pdf(self):
        df = self.get_payroll_df()
        path = f"Kashf_{datetime.now().strftime('%H%M%S')}.pdf"
        c = canvas.Canvas(path, pagesize=A4)
        def ar(t): return get_display(arabic_reshaper.reshape(str(t)))

        c.setFont('ArabicFont', 18)
        c.drawCentredString(300, 800, ar("جوهرة تعز مول - كشف رواتب"))
        c.setFont('ArabicFont', 12)
        c.drawCentredString(300, 780, ar(f"قسم: {self.rep_dept.get()} | التاريخ: {datetime.now().strftime('%Y-%m')}"))
        
        y = 720
        c.drawString(450, 740, ar("الموظف"))
        c.drawString(350, 740, ar("الراتب"))
        c.drawString(250, 740, ar("السلف"))
        c.drawString(150, 740, ar("الصافي"))
        c.line(50, 735, 550, 735)

        for _, row in df.iterrows():
            c.drawString(450, y, ar(row['الموظف']))
            c.drawString(350, y, str(row['الراتب']))
            c.drawString(250, y, str(row['السلف']))
            c.drawString(150, y, str(row['الصافي']))
            y -= 25
        c.save()
        os.startfile(path)

# ================= التشغيل الرئيسي =================
def start_app():
    login_root.destroy() # إغلاق نافذة الدخول
    main_root = tk.Tk()
    app = JoharaMallSystem(main_root)
    main_root.mainloop()

if __name__ == "__main__":
    login_root = tk.Tk()
    LoginWindow(login_root, start_app)
    login_root.mainloop()
