from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename
import time

def get_db_connection(max_retries=3):
    """إنشاء اتصال بقاعدة البيانات مع إعادة المحاولة عند الفشل"""
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('database.db', timeout=20)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # وضع الكتابة المحسّن
            return conn
        except sqlite3.DatabaseError as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)  # انتظر ثانية قبل إعادة المحاولة
    return None

import sqlite3
import os
import time

def init_db():
    """تهيئة قاعدة البيانات بشكل آمن ومضمون"""
    print("جاري تهيئة قاعدة البيانات...")
    
    # حذف الملف القديم إذا كان موجوداً (للتأكد)
    if os.path.exists('database.db'):
        try:
            os.remove('database.db')
            print("تم حذف ملف قاعدة البيانات القديم")
        except:
            print("لا يمكن حذف الملف القديم، سيتم استبداله")
    
    # إنشاء اتصال جديد بقاعدة البيانات
    try:
        conn = sqlite3.connect('database.db', timeout=30)
        c = conn.cursor()
        
        # إنشاء جدول المستخدمين
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile_image TEXT DEFAULT 'default.png',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ تم إنشاء جدول users")
        
        # إنشاء جدول المواد
        c.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                grade INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        print("✓ تم إنشاء جدول subjects")
        
        # التأكد من وجود العمود profile_image (للتوافق)
        try:
            c.execute("SELECT profile_image FROM users LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE users ADD COLUMN profile_image TEXT DEFAULT 'default.png'")
            print("✓ تم إضافة عمود profile_image")
        
        # حفظ التغييرات
        conn.commit()
        
        # التحقق من نجاح الإنشاء
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if c.fetchone():
            print("✓ جدول users موجود ويعمل")
        else:
            print("✗ خطأ: جدول users لم يتم إنشاؤه!")
        
        conn.close()
        print("✓ تم تهيئة قاعدة البيانات بنجاح")
        return True
        
    except Exception as e:
        print(f"✗ خطأ في تهيئة قاعدة البيانات: {e}")
        return False

def get_db():
    """إنشاء اتصال آمن بقاعدة البيانات"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('database.db', timeout=30)
            conn.row_factory = sqlite3.Row  # للوصول إلى الأعمدة بالاسم
            return conn
        except sqlite3.OperationalError as e:
            if attempt == max_retries - 1:
                print(f"فشل الاتصال بقاعدة البيانات بعد {max_retries} محاولات")
                raise e
            print(f"محاولة الاتصال {attempt + 1} فشلت، إعادة المحاولة...")
            time.sleep(1)
    return None

app = Flask(__name__)
app.secret_key = os.urandom(24)

# استدعاء الدالة عند بدء التشغيل
with app.app_context():
    if not init_db():
        print("فشل تهيئة قاعدة البيانات، جاري محاولة مرة أخرى...")
        time.sleep(2)
        init_db()

# إعدادات رفع الصور
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('الرجاء تسجيل الدخول أولاً', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("home.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = None
        try:
            conn = get_db()
            if not conn:
                flash('خطأ في الاتصال بقاعدة البيانات', 'danger')
                return render_template("register.html")
            
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            conn.commit()
            flash('تم التسجيل بنجاح! يمكنك تسجيل الدخول الآن', 'success')
            return redirect('/login')
            
        except sqlite3.IntegrityError:
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = None
        try:
            conn = get_db()
            if not conn:
                flash('خطأ في الاتصال بقاعدة البيانات', 'danger')
                return render_template("login.html")
            
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            
            if user and check_password_hash(user[3], password):  # user[3] هو كلمة المرور
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash(f'مرحباً {user[1]}! تم تسجيل الدخول بنجاح', 'success')
                return redirect('/dashboard')
            else:
                flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
                
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template("login.html")


@app.route('/logout')
def logout_user():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, subject_name, grade FROM subjects WHERE user_id=? ORDER BY grade ASC", (user_id,))
    subjects = c.fetchall()
    c.execute("SELECT COUNT(*) FROM subjects WHERE user_id=?", (user_id,))
    total_subjects = c.fetchone()[0]
    if total_subjects > 0:
        c.execute("SELECT AVG(grade) FROM subjects WHERE user_id=?", (user_id,))
        avg_grade = round(c.fetchone()[0], 1)
    else:
        avg_grade = 0
    conn.close()
    return render_template("dashboard.html",
                           subjects=subjects,
                           username=session['username'],
                           total_subjects=total_subjects,
                           avg_grade=avg_grade,
                           rest_day=session.get('rest_day'))

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    subject_name = request.form['subject_name']
    grade = int(request.form['grade'])
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO subjects (user_id, subject_name, grade) VALUES (?, ?, ?)",
              (session['user_id'], subject_name, grade))
    conn.commit()
    conn.close()
    flash('تم إضافة المادة بنجاح', 'success')
    return redirect('/dashboard')

@app.route('/edit_subject/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    subject_name = request.form['subject_name']
    grade = int(request.form['grade'])
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE subjects SET subject_name=?, grade=? WHERE id=? AND user_id=?",
              (subject_name, grade, subject_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('تم تعديل المادة بنجاح', 'success')
    return redirect('/dashboard')

@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM subjects WHERE id=? AND user_id=?", (subject_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('تم حذف المادة بنجاح', 'success')
    return redirect('/dashboard')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    if request.method == 'POST':
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET profile_image=? WHERE id=?", (filename, user_id))
                conn.commit()
                conn.close()
                flash('تم تحديث الصورة الشخصية', 'success')
        return redirect('/profile')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, email, profile_image FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    c.execute("SELECT subject_name, grade FROM subjects WHERE user_id=? ORDER BY grade DESC", (user_id,))
    subjects = c.fetchall()
    conn.close()

    username, email, profile_image = user
    
    if subjects:
        grades = [grade for _, grade in subjects]
        count = len(subjects)
        average = sum(grades) / count
        max_grade = max(grades)
        min_grade = min(grades)
        excellent = sum(1 for g in grades if g >= 90)
        very_good = sum(1 for g in grades if 80 <= g < 90)
        good = sum(1 for g in grades if 70 <= g < 80)
        pass_grade = sum(1 for g in grades if 60 <= g < 70)
        fail = sum(1 for g in grades if g < 60)

        if average >= 90:
            bar_color = '#28a745'
        elif average >= 80:
            bar_color = '#17a2b8'
        elif average >= 70:
            bar_color = '#ffc107'
        elif average >= 60:
            bar_color = '#fd7e14'
        else:
            bar_color = '#dc3545'
    else:
        count = 0
        average = 0
        max_grade = min_grade = 0
        excellent = very_good = good = pass_grade = fail = 0
        bar_color = '#6c757d'

    stats = {
        'count': count,
        'average': round(average, 2),
        'max': max_grade,
        'min': min_grade,
        'excellent': excellent,
        'very_good': very_good,
        'good': good,
        'pass': pass_grade,
        'fail': fail
    }

    return render_template('profile.html',
                           username=username,
                           email=email,
                           profile_image=profile_image,
                           stats=stats,
                           bar_color=bar_color,
                           subjects=subjects)

@app.route('/set_rest_day', methods=['POST'])
@login_required
def set_rest_day():
    rest_day = request.form.get('rest_day')
    if rest_day == "":
        rest_day = None
    session['rest_day'] = rest_day
    flash('تم تحديد يوم العطلة بنجاح', 'success')
    return redirect('/weekly_plan')

@app.route('/weekly_plan')
@login_required
def weekly_plan():
    user_id = session['user_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT subject_name, grade FROM subjects WHERE user_id=?", (user_id,))
    subjects = c.fetchall()
    conn.close()

    if not subjects:
        flash('أضف مواد أولاً لإنشاء الخطة الأسبوعية', 'info')
        return redirect('/dashboard')

    weighted_subjects = []
    total_weight = 0
    for name, grade in subjects:
        if grade < 50:
            weight = 4
        elif grade < 65:
            weight = 3
        elif grade < 80:
            weight = 2
        else:
            weight = 1
        weighted_subjects.append((name, weight, grade))
        total_weight += weight

    weekly_minutes = 14 * 60  # 840 دقيقة
    subject_minutes = {}
    for name, weight, grade in weighted_subjects:
        minutes = round((weight / total_weight) * weekly_minutes)
        subject_minutes[name] = {
            'minutes': minutes,
            'grade': grade,
            'priority': 'عالية' if weight >= 3 else 'متوسطة' if weight == 2 else 'منخفضة'
        }

    all_days = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    rest_day = session.get('rest_day')
    study_days = [day for day in all_days if day != rest_day] if rest_day else all_days
    num_study_days = len(study_days)

    schedule = {day: [] for day in all_days}
    for day in study_days:
        for name, data in subject_minutes.items():
            daily_minutes = round(data['minutes'] / num_study_days)
            if daily_minutes > 0:
                priority_class = "high-priority" if data['priority'] == 'عالية' else "medium-priority" if data['priority'] == 'متوسطة' else "low-priority"
                schedule[day].append({
                    'name': name,
                    'minutes': daily_minutes,
                    'grade': data['grade'],
                    'priority': data['priority'],
                    'class': priority_class
                })

    return render_template("weekly_plan.html",
                           schedule=schedule,
                           all_days=all_days,
                           rest_day=rest_day,
                           subject_minutes=subject_minutes,
                           total_minutes=weekly_minutes)

@app.route('/study_plan')
@login_required
def study_plan():
    return redirect('/weekly_plan')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)



# التحقق من قاعدة البيانات عند بدء التشغيل
@app.before_request
def before_request():
    """التحقق من وجود قاعدة البيانات قبل كل طلب"""
    if not os.path.exists('database.db'):
        print("⚠️ قاعدة البيانات غير موجودة، جاري إنشائها...")
        init_db()