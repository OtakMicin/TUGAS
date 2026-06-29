from logging import info

from flask import Flask, flash, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from difflib import get_close_matches
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import wikipediaapi
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)   
app.secret_key = 'healthtech_ultimate_key'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

excel_path = os.path.join(BASE_DIR, "chatbot_dataset.xlsx")
medicine_path = os.path.join(BASE_DIR, "medicine_dataset_100.xlsx")
medicine_df = pd.read_excel(medicine_path)
print(excel_path)
print(os.path.exists(excel_path))

chatbot_df = pd.read_excel(excel_path)
db_path = os.path.join(BASE_DIR, "instance", "healthtech.db")

print(db_path)
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config['SESSION_PERMANENT'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(app.config["SQLALCHEMY_DATABASE_URI"])
db = SQLAlchemy(app)


print("Current Working Directory:", os.getcwd())
print("App Directory:", os.path.dirname(os.path.abspath(__file__)))
print("Database Exists:", os.path.exists("instance/healthtech.db"))
print("Absolute DB:", os.path.abspath("instance/healthtech.db"))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Arahkan ke fungsi login jika user belum masuk

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# GUNAKAN SATU SAJA YANG SEPERTI INI:
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    foto_profil = db.Column(db.String(200), default='https://via.placeholder.com/150')

    # Tambahkan ini di dalam class User agar tidak error lagi
    __table_args__ = {'extend_existing': True}
    

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    kota = db.Column(db.String(50), nullable=False)
    doctors = db.relationship('Doctor', backref='hospital', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

    spesialis = db.Column(db.String(100), nullable=False)     
    spesialis_en = db.Column(db.String(100), nullable=False)   

    biaya = db.Column(db.Integer, default=100000)
    tersedia = db.Column(db.Boolean, default=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150))
    kategori = db.Column(db.String(100))
    kandungan = db.Column(db.String(200))
    dosis = db.Column(db.String(100))
    kegunaan = db.Column(db.Text)
    efek_samping = db.Column(db.Text)
    aturan_pakai = db.Column(db.Text)
    harga = db.Column(db.Integer)
    stok = db.Column(db.Integer)
    resep = db.Column(db.String(20))
    gambar = db.Column(db.String(255))
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    medicine_id = db.Column(
        db.Integer,
        db.ForeignKey("medicine.id")
    )

    jumlah = db.Column(db.Integer, default=1)

    medicine = db.relationship("Medicine")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey("user.id"))

    total = db.Column(db.Integer)

    metode = db.Column(db.String(50))

    alamat = db.Column(db.Text)

    status = db.Column(db.String(30), default="Berhasil")

    tanggal = db.Column(db.DateTime,
                        default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    tanggal_janji = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Dijadwalkan')
    doctor = db.relationship('Doctor', backref='appointments', lazy=True)

class Reminder(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    title = db.Column(db.String(100))

    reminder_date = db.Column(db.Date)

    reminder_time = db.Column(db.Time)

    status = db.Column(
        db.Boolean,
        default=False
    )

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.id'),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)

    comment = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pesan_user = db.Column(db.Text, nullable=False)
    balasan_ai = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class HealthTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    makan_kali = db.Column(db.Integer, default=0)
    tidur_jam = db.Column(db.Float, default=0)
    olahraga_kalori = db.Column(db.Integer, default=0)
    tanggal = db.Column(db.Date, default=datetime.now().date())

class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.now
    )

    ip_address = db.Column(db.String(100))

    device = db.Column(db.String(255))

with app.app_context():
    db.create_all()

    if not Hospital.query.first():

        # ======================
        # HOSPITAL
        # ======================
        rs1 = Hospital(
            nama="RS Pusat Medika",
            alamat="Jl. Sudirman No. 1",
            kota="Jakarta"
        )

        rs2 = Hospital(
            nama="RS Sehat Bandung",
            alamat="Jl. Asia Afrika No. 10",
            kota="Bandung"
        )

        rs3 = Hospital(
            nama="RS Harapan Medika",
            alamat="Jl. Gatot Subroto No. 12",
            kota="Surabaya"
        )

        db.session.add_all([rs1, rs2, rs3])
        db.session.commit()

        # ======================
        # DOCTOR
        # ======================
        doctors = [

            Doctor(
                nama="dr. Andi Pratama, Sp.PD",
                spesialis="Penyakit Dalam",
                spesialis_en="Internal Medicine",
                biaya=150000,
                hospital_id=rs1.id
            ),

            Doctor(
                nama="dr. Budi Santoso, Sp.JP",
                spesialis="Jantung",
                spesialis_en="Cardiology",
                biaya=200000,
                hospital_id=rs1.id
            ),

            Doctor(
                nama="dr. Siti Aminah, Sp.A",
                spesialis="Anak",
                spesialis_en="Pediatrics",
                biaya=125000,
                hospital_id=rs2.id
            ),

            Doctor(
                nama="dr. Kevin Wijaya, Sp.THT",
                spesialis="THT",
                spesialis_en="ENT",
                biaya=170000,
                hospital_id=rs2.id
            ),

            Doctor(
                nama="dr. Maria Natalia, Sp.M",
                spesialis="Mata",
                spesialis_en="Ophthalmology",
                biaya=180000,
                hospital_id=rs1.id
            ),

            Doctor(
                nama="dr. Rina Kusuma, Sp.KK",
                spesialis="Kulit",
                spesialis_en="Dermatology",
                biaya=180000,
                hospital_id=rs3.id
            ),

            Doctor(
                nama="dr. Dimas Saputra, Sp.P",
                spesialis="Paru",
                spesialis_en="Pulmonology",
                biaya=190000,
                hospital_id=rs3.id
            ),

            Doctor(
                nama="dr. Cindy Lestari, Sp.S",
                spesialis="Saraf",
                spesialis_en="Neurology",
                biaya=200000,
                hospital_id=rs2.id
            ),

            Doctor(
                nama="dr. Farhan Akbar, Sp.OG",
                spesialis="Kandungan",
                spesialis_en="Obstetrics & Gynecology",
                biaya=220000,
                hospital_id=rs3.id
            ),

            Doctor(
                nama="dr. Yoga Prasetyo, Sp.Ort",
                spesialis="Ortopedi",
                spesialis_en="Orthopedics",
                biaya=230000,
                hospital_id=rs1.id
            ),

            Doctor(
                nama="dr. Bella Christy, Sp.U",
                spesialis="Urologi",
                spesialis_en="Urology",
                biaya=200000,
                hospital_id=rs2.id
            ),

            Doctor(
                nama="dr. Samuel Jonathan, Sp.B",
                spesialis="Bedah Umum",
                spesialis_en="General Surgery",
                biaya=250000,
                hospital_id=rs3.id
            ),
        ]

        db.session.add_all(doctors)
        db.session.commit()

with app.app_context():
    db.create_all()
    if Medicine.query.count() < len(medicine_df):

        for _, row in medicine_df.iterrows():

            med = Medicine(

                nama=row["nama"],
                kategori=row["kategori"],
                kandungan=row["kandungan"],
                dosis=row["dosis"],
                kegunaan=row["kegunaan"],
                efek_samping=row["efek_samping"],
                aturan_pakai=row["aturan_pakai"],
                harga=row["harga"],
                stok=row["stok"],
                resep=row["resep"],
                gambar=row["gambar"]

            )

            db.session.add(med)
        print("Jumlah baris Excel:", len(medicine_df))
        db.session.commit()
        print("Jumlah Medicine di DB:", Medicine.query.count())

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    lang = session.get("lang", "id")  
    print("LANG SESSION:", session.get("lang"))

    articles_raw = [
        {
            "id": 1,
            "title": {"id": "Tidur", "en": "Sleep"},
            "desc": {
                "id": "Tidur 7-8 jam sehari kunci imunitas tubuh tetap prima.",
                "en": "Sleeping 7-8 hours a day is key to maintaining a strong immune system."
            },
            "image": "https://awsimages.detik.net.id/community/media/visual/2020/04/26/f1997b75-0fa4-4848-845e-2233e597b96e_169.jpeg?w=600&q=90",
        },
        {
            "id": 2,
            "title": {"id": "Air minum", "en": "Drinking Water"},
            "desc": {
                "id": "Hidrasi cukup membantu ginjal bekerja lebih maksimal.",
                "en": "Proper hydration helps the kidneys function more efficiently."
            },
            "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkq8nRGTyDOtc619tW53eiaZfEcBzHU5rfcA&s",
        },
        {
            "id": 3,
            "title": {"id": "Nutrisi", "en": "Nutrition"},
            "desc": {
                "id": "Sayuran hijau mengandung serat tinggi untuk pencernaan.",
                "en": "Green vegetables contain high fiber for digestion."
            },
            "image": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=500",
        }
    ]

    articles = []
    for a in articles_raw:
        articles.append({
            "id": a["id"],
            "title": a["title"][lang],
            "desc": a["desc"][lang],
            "image": a["image"]
        })
    
    return render_template('home.html', articles=articles, current_lang=lang)

@app.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    wiki_titles = {
        1: {"id": "Tidur", "en": "Sleep"},
        2: {"id": "Air minum", "en": "Water"},
        3: {"id": "Nutrisi", "en": "Nutrition"},
        4: {"id": "Olahraga", "en": "Exercise"},
        5: {"id": "Stres", "en": "Stress"},
        6: {"id": "Hipertensi", "en": "Hypertension"},
        7: {"id": "Diabetes", "en": "Diabetes"}
    }

    if article_id not in wiki_titles:
        return "Artikel tidak ditemukan", 404

    lang = session.get("lang", "id")

    wiki_title = wiki_titles[article_id][lang]
    wiki_lang = "id" if lang == "id" else "en"

    try:
        wiki = wikipediaapi.Wikipedia(
            language=wiki_lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='HealthTechApp/1.0 (contact@example.com)'
        )

        page = wiki.page(wiki_title)

        if page.exists():
            content = page.summary

            if len(content) > 2500:
                content = content[:2500].rsplit(' ', 1)[0] + "..."

            content = f"<strong>{content}</strong>"

            if lang == "id":
                content += f"<br><br>📖 <strong>Sumber:</strong> Wikipedia - {page.title}<br>🔗 <a href='{page.fullurl}' target='_blank'>Baca lengkap</a>"
            else:
                content += f"<br><br>📖 <strong>Source:</strong> Wikipedia - {page.title}<br>🔗 <a href='{page.fullurl}' target='_blank'>Read more</a>"

            article = {
                "id": article_id,
                "title": page.title,
                "content": content
            }

            return render_template('article_detail.html', article=article)

        else:
            return f"Page '{wiki_title}' not found", 404

    except Exception as e:
        return f"Error: {str(e)}", 500
        
@app.route("/medicine")
@login_required
def medicine():

    medicines = Medicine.query.all()

    return render_template(
        "medicine.html",
        medicines=medicines
    )

@app.route("/cart/add/<int:id>", methods=["POST"])
@login_required
def add_cart(id):

    cart = Cart.query.filter_by(
        user_id=session["user_id"],
        medicine_id=id
    ).first()

    if cart:

        cart.jumlah += 1

    else:

        cart = Cart(
            user_id=session["user_id"],
            medicine_id=id,
            jumlah=1
        )

        db.session.add(cart)

    db.session.commit()

    flash("Obat berhasil ditambahkan ke keranjang.")

    return redirect(url_for("medicine"))

@app.route("/cart")
@login_required
def cart():

    carts = Cart.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total = sum(
        c.medicine.harga * c.jumlah
        for c in carts
    )

    return render_template(
        "cart.html",
        carts=carts,
        total=total
    )

@app.route("/cart/delete/<int:id>")
@login_required
def delete_cart(id):

    cart = Cart.query.get_or_404(id)

    db.session.delete(cart)

    db.session.commit()

    flash("Obat berhasil dihapus.")

    return redirect(url_for("cart"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session.permanent = True

            if remember:
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                app.permanent_session_lifetime = timedelta(minutes=60)

            session['user_id'] = user.id
            session['user_nama'] = user.nama

            # Simpan riwayat login
            log = LoginLog(
                user_id=user.id,
                timestamp=datetime.now(),
                ip_address=request.remote_addr,
                device=request.user_agent.string
            )

            db.session.add(log)
            db.session.commit()

            return redirect(url_for('home'))

        elif not email or not password:
            flash("Email dan password wajib diisi!", "warning")

        else:
            flash("Email atau password salah!", "danger")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        db.session.add(User(nama=nama, email=email, password=hashed_pw))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/profile")
@login_required
def profile():

    user = User.query.get(session["user_id"])

    login_logs = LoginLog.query.filter_by(
        user_id=user.id
    ).order_by(
        LoginLog.timestamp.desc()
    ).all()

    return render_template(
        "profile.html",
        user=user,
        login_logs=login_logs
    )

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    user = User.query.get(session["user_id"])

    if request.method == "POST":

        user.nama = request.form["nama"]
        user.email = request.form["email"]
        foto = request.files.get("foto")

        if foto and foto.filename != "":

            filename = secure_filename(foto.filename)

            foto.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            user.foto_profil = filename

        db.session.commit()

        session["user_nama"] = user.nama

        flash("Profil berhasil diperbarui.", "success")

        return redirect(url_for("profile"))

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chatbot_reply():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').lower().strip()
        user_name = session.get('user_nama', 'Teman')



        if 'chat_step' not in session:
            session['chat_step'] = 1
            session['last_complaint'] = ""

        kata_umum = ["sakit", "nyeri", "tidak enak badan", "kurang sehat", "tolong"]
        if session['chat_step'] == 1:
            if user_msg in kata_umum or len(user_msg) < 4:
                return jsonify({"response": f"Halo {user_name}! Saya mengerti Anda merasa tidak nyaman. Agar saya bisa membantu lebih tepat, boleh tahu di bagian mana yang terasa sakit? (Misalnya: sakit perut atau pusing)"})
            

            session['last_complaint'] = user_msg
            session['chat_step'] = 2
            return jsonify({"response": f"Terima kasih infonya. Saya mencatat keluhan **{user_msg}**. Sudah berapa lama ini dirasakan? Ada gejala lain?"})
        else:
            complaint_awal = session.get('last_complaint', '')
            session['chat_step'] = 1 
            
            for _, row in chatbot_df.iterrows():

                keywords = str(row["keyword"]).lower().split(",")

                for key in keywords:

                    key = key.strip()

                    if key in complaint_awal or key in user_msg:

                        return jsonify({
                                "response": f"""
                            {row['jawaban_bot']}

                            <br><br>

                            Semoga lekas sembuh, {user_name}! 😊
                            """,
                                "finished": True
                        })
                return jsonify({
                    "response": "Maaf, saya belum menemukan informasi mengenai keluhan tersebut.",
                    "finished": True
                })
    except Exception as e:
        return jsonify({
            "response": "Maaf saya belum menemukan penyakit yang sesuai...",
            "finished": True
        }), 500


@app.route('/set-language/<lang>')
@login_required
def set_language(lang):
    if lang in ['id', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route("/calendar")
@login_required
def calendar():

    reminders = Reminder.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "calendar.html",
        reminders=reminders
    )

@app.route("/complete-reminder/<int:id>")
@login_required
def complete_reminder(id):

    reminder = Reminder.query.get_or_404(id)

    reminder.status = True

    db.session.commit()

    return redirect("/calendar")

@app.route("/undo-reminder/<int:id>")
@login_required
def undo_reminder(id):

    reminder = Reminder.query.get_or_404(id)

    reminder.status = False

    db.session.commit()

    return redirect("/calendar")

@app.route("/add-reminder", methods=["POST"])
@login_required
def add_reminder():

    reminder = Reminder(

        user_id=session["user_id"],

        title=request.form["title"],

        reminder_date=datetime.strptime(
            request.form["date"],
            "%Y-%m-%d"
        ).date(),

        reminder_time=datetime.strptime(
            request.form["time"],
            "%H:%M"
        ).time(),

        status=False

    )

    db.session.add(reminder)
    db.session.commit()

    return redirect("/calendar")

@app.route('/ai-check')
@login_required
def ai_check():
    chats = ChatHistory.query.filter_by(user_id=session['user_id']).order_by(ChatHistory.timestamp.asc()).all()
    return render_template('ai_check.html', chats=chats)

@app.route("/api/reset-chat", methods=["POST"])
@login_required
def reset_chat():

    session["chat_step"] = 1
    session["last_complaint"] = ""

    return jsonify({"success":True})


@app.route('/doctor')
@login_required
def doctor():
    doctors = Doctor.query.all()

    print("===== DOCTOR DATA =====")
    for d in doctors:
        print(d.nama)
        print("ID :", d.spesialis)
        print("EN :", d.spesialis_en)
        print("----------------")

    return render_template("doctor.html", doctors=doctors)

@app.route('/booking/<int:doctor_id>', methods=['POST'])
@login_required
def book_appointment(doctor_id):
    tanggal = request.form.get('tanggal')
    waktu = request.form.get('waktu')
    tgl_obj = datetime.strptime(f"{tanggal} {waktu}", '%Y-%m-%d %H:%M')
    db.session.add(Appointment(user_id=session['user_id'], doctor_id=doctor_id, tanggal_janji=tgl_obj))
    db.session.commit()
    return redirect(url_for('my_appointments'))

@app.route('/appointments')
@login_required
def my_appointments():

    appointments = Appointment.query.filter_by(
        user_id=session['user_id']
    ).all()

    all_doctors = Doctor.query.limit(3).all()

    ratings = Rating.query.all()

    rated_appointment_ids = [
        r.appointment_id for r in ratings
    ]

    return render_template(
        "appointments.html",
        appointments=appointments,
        recommended_doctors=all_doctors,
        ratings=ratings,
        rated_appointment_ids=rated_appointment_ids
    )

@app.route('/submit-rating/<int:appointment_id>', methods=['POST'])
@login_required
def submit_rating(appointment_id):

    appointment = Appointment.query.get_or_404(appointment_id)

    new_rating = Rating(
        appointment_id=appointment.id,
        doctor_id=appointment.doctor_id,
        user_id=session['user_id'],
        rating=int(request.form.get("rating")),
        comment=request.form.get("comment")
    )

    db.session.add(new_rating)
    db.session.commit()

    flash("Terima kasih atas ulasannya!", "success")

    return redirect(url_for("my_appointments"))

@app.route('/healthy', methods=['GET', 'POST'])
@login_required
def healthy():
    today = datetime.now().date()

    track = HealthTrack.query.filter_by(user_id=session['user_id'], tanggal=today).first()
    if not track:
        track = HealthTrack(user_id=session['user_id'], tanggal=today)
        db.session.add(track)
        db.session.commit()

    if request.method == 'POST':
        track.makan_kali = int(request.form.get('makan', 0))
        track.tidur_jam = float(request.form.get('tidur', 0))
        track.olahraga_kalori = int(request.form.get('olahraga', 0))
        db.session.commit()
        return redirect(url_for('healthy'))

    labels = []
    values = []
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        labels.append(target_date.strftime('%a'))
        record = HealthTrack.query.filter_by(user_id=session['user_id'], tanggal=target_date).first()
        values.append(record.olahraga_kalori if record else 0)

    progress = min(int((track.olahraga_kalori / 1000) * 100), 100)
    
    return render_template('healthy.html', track=track, labels=labels, values=values, progress=progress)

@app.route('/health-history')
@login_required
def health_history():
    date_str = request.args.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()

    record = HealthTrack.query.filter_by(user_id=session['user_id'], tanggal=target_date).first()

    all_history = HealthTrack.query.filter_by(user_id=session['user_id']).order_by(HealthTrack.tanggal.desc()).all()
    
    return render_template('history.html', record=record, target_date=target_date, all_history=all_history)

@app.route('/maps')
@login_required
def maps():
    hospitals = Hospital.query.all()
    return render_template('maps.html', hospitals=hospitals)

if __name__ == '__main__':
    app.run(debug=True)