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

# ================= إعدادات الخط العربي (Amiri) =================
FONT_FILE = 'Amiri-Regular.ttf' # تأكد من وجود الملف بهذا الاسم بجانب الكود

try:
    if os.path.exists(FONT_FILE):
        pdfmetrics.registerFont(TTFont('AmiriFont', FONT_FILE))
        AR_FONT = 'AmiriFont'
    else:
        AR_FONT = 'Helvetica' # حل مؤقت في حال فقدان الخط
        print("تنبيه: لم يتم العثور على ملف Amiri-Regular.ttf")
except Exception as e:
    AR_FONT = 'Helvetica'
    print(f"خطأ في تحميل الخط: {e}")

# ================= كلاس شاشة الدخول =================
class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("دخول النظام - جوهرة تعز مول")
        self.root.geometry("400x350")
        self.root.configure(bg="#2c3e50")

        tk.Label(root, text="نظام إدارة المول", font=("Arial", 20, "bold"), fg="#ecf0f1", bg="#2c3e50").pack(pady=30)
        
        tk.Label(root, text="اسم المستخدم:", fg="#bdc3c7", bg="#2c3e50").pack()
        self.ent_user = tk.Entry(root, justify='center', font=("Arial", 12))
        self.ent_user.pack(pady=5)
        
        tk.Label(root, text="كلمة المرور:", fg="#bdc3c7", bg="#2c3e50").pack()
        self.ent_pass = tk.Entry(root, show="*", justify='center', font=("Arial", 12))
        self.ent_pass.pack(pady=5)

        tk.Button(root, text="تسجيل الدخول", command=self.check_login, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=15).pack(pady=25)

    def check_login(self):
        # بيانات الدخول الخاصة بالأستاذ باسم
        if self.ent_user.get() == "basem" and self.ent_pass.get() == "1234":
            self.on_success()
        else:
            messagebox.showerror("خطأ في الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة!")

# ================= كلاس النظام الرئيسي =================
class JoharaMallSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام إدارة جوهرة تعز مول - الإصدار الاحترافي (Amiri Edition)")
        self.root.geometry("1100x850")
        self.db_name = "mall_management.db"
        self.init_db()

        # إنشاء التبويبات
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[10, 5])
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_treasury = ttk.Frame(self.notebook)
        self.tab_hr = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_treasury, text=" 💰 إدارة الخزينة ")
        self.notebook.add(self.tab_hr, text=" 👥 الموارد البشرية والسلف ")
        self.notebook.add(self.tab_reports, text=" 📊 التقارير والطباعة ")

        self.setup_treasury_ui()
        self.setup_hr_ui()
        self.setup_reports_ui()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, date TEXT, desc TEXT, type TEXT, amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, salary REAL, dept TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, emp_name TEXT, amount REAL, date TEXT)''')
        conn.commit()
        conn.close()

    # --- مساعدة لتنسيق النصوص العربية ---
    def format_ar(self, text):
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)

    # --- واجهة الخزينة ---
    def setup_treasury_ui(self):
        frame = tk.LabelFrame(self.tab_treasury, text="إضافة حركة نقدية جديدة", font=("Arial", 12, "bold"), padx=15, pady=15)
        frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(frame, text="البيان (الوصف):").grid(row=0, column=5, padx=5)
        self.ent_desc = tk.Entry(frame, justify='right', width=30)
        self.ent_desc.grid(row=0, column=4)

        tk.Label(frame, text="المبلغ (ريال):").grid(row=0, column=3, padx=5)
        self.ent_amt = tk.Entry(frame, justify='right', width=15)
        self.ent_amt.grid(row=0, column=2)

        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(frame, textvariable=self.type_var, values=["إيراد", "توريد للمدير عمار", "مصروف جانبي"], state="readonly")
        self.type_combo.grid(row=0, column=1, padx=10)
        self.type_combo.set("إيراد")
        
        tk.Button(frame, text="قيد العملية", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=self.add_transaction).grid(row=0, column=0, padx=10)

        # جدول الحركات
        self.tree_trans = ttk.Treeview(self.tab_treasury, columns=("ID", "Date", "Desc", "Type", "Amt"), show='headings')
        headings = ["م", "التاريخ والوقت", "البيان", "النوع", "المبلغ"]
        for col, txt in zip(self.tree_trans["columns"], headings):
            self.tree_trans.heading(col, text=txt)
            self.tree_trans.column(col, anchor="center")
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
            messagebox.showinfo("نجاح", "تم تسجيل العملية في الخزينة بنجاح")
        except:
            messagebox.showerror("خطأ", "يرجى التأكد من إدخال المبلغ بشكل صحيح")

    def refresh_treasury(self):
        for i in self.tree_trans.get_children(): self.tree_trans.delete(i)
        conn = sqlite3.connect(self.db_name)
        for row in conn.execute("SELECT * FROM transactions ORDER BY id DESC"): 
            self.tree_trans.insert("", 0, values=row)
        conn.close()

    # --- واجهة HR والسلف ---
    def setup_hr_ui(self):
        # إضافة موظف
        f1 = tk.LabelFrame(self.tab_hr, text="إضافة موظف جديد", font=("Arial", 12, "bold"), padx=15, pady=15)
        f1.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(f1, text="اسم الموظف:").grid(row=0, column=5)
        self.ent_emp_name = tk.Entry(f1, justify='right')
        self.ent_emp_name.grid(row=0, column=4, padx=5)

        tk.Label(f1, text="الراتب الأساسي:").grid(row=0, column=3)
        self.ent_emp_sal = tk.Entry(f1, justify='right')
        self.ent_emp_sal.grid(row=0, column=2, padx=5)

        self.emp_dept = tk.StringVar()
        depts = ["صالة الألعاب", "إدارة جوهرة تعز مول", "شركة الأمن النسيم", "شركة النظافة"]
        ttk.Combobox(f1, textvariable=self.emp_dept, values=depts, state="readonly").grid(row=0, column=1, padx=5)
        
        tk.Button(f1, text="حفظ الموظف", command=self.add_employee, bg="#2980b9", fg="white").grid(row=0, column=0, padx=10)

        # قيد السلف
        f2 = tk.LabelFrame(self.tab_hr, text="تسجيل سلفة مالية", font=("Arial", 12, "bold"), padx=15, pady=15)
        f2.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(f2, text="اسم الموظف المستلف:").grid(row=0, column=3)
        self.loan_name = tk.Entry(f2, justify='right', width=25)
        self.loan_name.grid(row=0, column=2, padx=5)
        
        tk.Label(f2, text="المبلغ:").grid(row=0, column=1)
        self.loan_amt = tk.Entry(f2, width=15)
        self.loan_amt.grid(row=0, column=0, padx=5)
        
        tk.Button(f2, text="اعتماد السلفة وخصمها من الخزينة", command=self.add_loan, bg="#d35400", fg="white", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=4, pady=15)

    def add_employee(self):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute("INSERT INTO employees (name, salary, dept) VALUES (?,?,?)",
                         (self.ent_emp_name.get(), float(self.ent_emp_sal.get()), self.emp_dept.get()))
            conn.commit()
            conn.close()
            messagebox.showinfo("HR", "تمت إضافة الموظف بنجاح")
        except:
            messagebox.showerror("خطأ", "تأكد من إدخال البيانات والراتب بشكل صحيح")

    def add_loan(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            name, amt = self.loan_name.get(), float(self.loan_amt.get())
            # قيد في السلف
            c.execute("INSERT INTO loans (emp_name, amount, date) VALUES (?,?,?)", (name, amt, datetime.now().strftime("%Y-%m-%d")))
            # قيد تلقائي في الخزينة كمصروف
            c.execute("INSERT INTO transactions (date, desc, type, amount) VALUES (?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d"), f"سلفة: {name}", "مصروف جانبي", amt))
            conn.commit()
            conn.close()
            self.refresh_treasury()
            messagebox.showinfo("السلف", f"تم قيد مبلغ {amt} سلفة على {name} وخصمها من الصندوق.")
        except:
            messagebox.showerror("خطأ", "فشل قيد السلفة. تأكد من البيانات.")

    # --- التقارير والطباعة ---
    def setup_reports_ui(self):
        f = tk.LabelFrame(self.tab_reports, text="مركز استخراج التقارير المعتمدة", font=("Arial", 14, "bold"), padx=30, pady=30)
        f.pack(pady=50, padx=50, fill=tk.X)

        tk.Label(f, text="اختر القسم المراد استخراج كشفه:", font=("Arial", 12)).pack(pady=10)
        self.rep_dept = tk.StringVar()
        depts = ["صالة الألعاب", "إدارة جوهرة تعز مول", "شركة الأمن النسيم", "شركة النظافة"]
        self.rep_combo = ttk.Combobox(f, textvariable=self.rep_dept, values=depts, state="readonly", width=40, font=("Arial", 12))
        self.rep_combo.pack(pady=10)
        self.rep_combo.set("صالة الألعاب")

        tk.Button(f, text="تصدير إلى إكسيل (Excel)", command=self.export_excel, bg="#27ae60", fg="white", width=35, font=("Arial", 11, "bold")).pack(pady=10)
        tk.Button(f, text="طباعة كشف PDF (خط الأميري)", command=self.export_pdf, bg="#c0392b", fg="white", width=35, font=("Arial", 11, "bold")).pack(pady=10)

    def get_payroll_data(self):
        dept = self.rep_dept.get()
        conn = sqlite3.connect(self.db_name)
        df_emp = pd.read_sql_query(f"SELECT name, salary FROM employees WHERE dept='{dept}'", conn)
        results = []
        for _, row in df_emp.iterrows():
            loan = conn.execute(f"SELECT SUM(amount) FROM loans WHERE emp_name='{row['name']}'").fetchone()[0] or 0
            results.append({
                "اسم الموظف": row['name'], 
                "الراتب الأساسي": row['salary'], 
                "إجمالي السلف": loan, 
                "صافي الراتب": row['salary'] - loan
            })
        conn.close()
        return pd.DataFrame(results)

    def export_excel(self):
        df = self.get_payroll_data()
        filename = f"Kashf_{self.rep_dept.get()}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False)
        os.startfile(filename)

    def export_pdf(self):
        df = self.get_payroll_data()
        filename = f"Kashf_{datetime.now().strftime('%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        
        # ترويسة التقرير
        c.setFont(AR_FONT, 24)
        c.drawCentredString(300, 800, self.format_ar("جوهرة تعز مول - كشف الرواتب الشهري"))
        c.setFont(AR_FONT, 16)
        c.drawCentredString(300, 770, self.format_ar(f"القسم: {self.rep_dept.get()} | التاريخ: {datetime.now().strftime('%Y-%m')}"))
        
        # الجدول
        y = 700
        c.setFont(AR_FONT, 14)
        c.drawString(450, 720, self.format_ar("اسم الموظف"))
        c.drawString(350, 720, self.format_ar("الراتب"))
        c.drawString(250, 720, self.format_ar("السلف"))
        c.drawString(150, 720, self.format_ar("الصافي"))
        c.line(50, 715, 550, 715)

        for _, row in df.iterrows():
            c.drawString(450, y, self.format_ar(row['اسم الموظف']))
            c.drawString(350, y, str(row['الراتب الأساسي']))
            c.drawString(250, y, str(row['إجمالي السلف']))
            c.drawString(150, y, str(row['صافي الراتب']))
            y -= 30
            if y < 50: # صفحة جديدة إذا انتهت المساحة
                c.showPage()
                y = 750
        
        c.save()
        os.startfile(filename)

# ================= تشغيل التطبيق =================
def run_main_app():
    login_win.destroy()
    main_root = tk.Tk()
    app = JoharaMallSystem(main_root)
    main_root.mainloop()

if __name__ == "__main__":
    login_win = tk.Tk()
    LoginWindow(login_win, run_main_app)
    login_win.mainloop()
