from flask import Flask, flash, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from difflib import get_close_matches
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import wikipediaapi

app = Flask(__name__)
app.secret_key = 'healthtech_ultimate_key'
app.config['SESSION_PERMANENT'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthtech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    biaya = db.Column(db.Integer, default=100000)
    tersedia = db.Column(db.Boolean, default=True) # Tambahkan ini
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    tanggal_janji = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Dijadwalkan')
    doctor = db.relationship('Doctor', backref='appointments', lazy=True)

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

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Berhasil')


with app.app_context():
    db.create_all()
    if not Hospital.query.first():
        rs1 = Hospital(nama="RS Pusat Medika", alamat="Jl. Sudirman No. 1", kota="Jakarta")
        rs2 = Hospital(nama="RS Sehat Bandung", alamat="Jl. Asia Afrika No. 10", kota="Bandung")
        db.session.add_all([rs1, rs2])
        db.session.commit()
        d1 = Doctor(nama="dr. Andi Pratama, Sp.PD", spesialis="Penyakit Dalam", biaya=150000, hospital_id=rs1.id)
        d2 = Doctor(nama="dr. Budi Santoso, Sp.Jp", spesialis="Jantung", biaya=200000, hospital_id=rs1.id)
        d3 = Doctor(nama="dr. Siti Aminah, Sp.A", spesialis="Anak", biaya=125000, hospital_id=rs2.id)
        db.session.add_all([d1, d2, d3])
        db.session.commit()

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
    # ✅ WAJIB ADA
    lang = session.get("lang", "id")  # ambil bahasa dari session
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

    # ✅ ambil bahasa
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

            # potong biar tidak terlalu panjang
            if len(content) > 2500:
                content = content[:2500].rsplit(' ', 1)[0] + "..."

            # ✅ bikin bold + rapih (pakai HTML)
            content = f"<strong>{content}</strong>"

            # footer bilingual
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
        
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
#         remember = request.form.get('remember') # Ambil nilai checkbox
        
#         user = User.query.filter_by(email=email).first()
        
#         if user and check_password_hash(user.password, password):
#             session.permanent = True # Aktifkan permanen
#             if remember:
#                 # Ingat selama 30 hari
#                 app.permanent_session_lifetime = timedelta(days=30)
#             else:
#                 # Ingat hanya selama browser terbuka
#                 app.permanent_session_lifetime = timedelta(minutes=60)
                
#             session['user_id'] = user.id
#             session['user_nama'] = user.nama
#             return redirect(url_for('home'))
            
#     return render_template('login.html')

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

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session.get('user_id'))
    
    if user is None:
        session.clear() 
        return redirect(url_for('login'))
        
    login_logs = LoginHistory.query.filter_by(user_id=user.id).order_by(LoginHistory.timestamp.desc()).limit(5).all()
    return render_template('profile.html', user=user, login_logs=login_logs)

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

        medical_db = {
            # Sistem Pencernaan
            "lambung": {"diag": "Gastritis (Maag)", "obat": "Antasida, Omeprazole", "tips": "Hindari kopi, pedas, dan asam."},
            "perut": {"diag": "Dispepsia / Gangguan Pencernaan", "obat": "Promag, Mylanta", "tips": "Makan porsi kecil tapi sering."},
            "diare": {"diag": "Gastroenteritis", "obat": "Oralit, Diapet, Attapulgite", "tips": "Banyak minum cairan agar tidak dehidrasi."},
            "sembelit": {"diag": "Konstipasi", "obat": "Microlax, Dulcolax", "tips": "Perbanyak makan serat dan buah pepaya."},
            "wasir": {"diag": "Hemoroid (Ambeien)", "obat": "Ambeven, Ardium", "tips": "Jangan duduk terlalu lama dan jangan mengejan."},

            # Sistem Pernapasan & Kepala
            "pusing": {"diag": "Cephalgia (Sakit Kepala)", "obat": "Paracetamol, Ibuprofen", "tips": "Istirahat di ruang gelap."},
            "migrain": {"diag": "Sakit Kepala Sebelah", "obat": "Bodrex Migra, Sumatriptan", "tips": "Kurangi paparan cahaya gadget."},
            "flu": {"diag": "Influenza", "obat": "Panadol Flu, Decolgen", "tips": "Istirahat total dan minum Vitamin C."},
            "batuk": {"diag": "Iritasi Tenggorokan / Bronkitis", "obat": "OBH Combi, Siladex, Lasal", "tips": "Minum air hangat, hindari gorengan."},
            "sesak": {"diag": "Gejala Asma / Gangguan Napas", "obat": "Ventolin (Inhaler)", "tips": "🚨 Segera ke RS jika sesak makin berat."},
            "pilek": {"diag": "Rhinitis", "obat": "Rhinos SR, Tremenza", "tips": "Gunakan masker dan hindari debu."},

            # Mulut, Mata, Telinga
            "gigi": {"diag": "Pulpitis (Sakit Gigi)", "obat": "Cataflam, Asam Mefenamat", "tips": "Kumur air garam hangat."},
            "sariawan": {"diag": "Stomatitis", "obat": "Aloclair, Kenalog in Orabase", "tips": "Perbanyak Vitamin C."},
            "mata": {"diag": "Iritasi Mata / Konjungtivitis", "obat": "Insto, Rohto, Cendo Xitrol", "tips": "Jangan dikucek."},
            "telinga": {"diag": "Otitis / Infeksi Telinga", "obat": "Vital Ear Oil", "tips": "Jangan dibersihkan dengan cotton bud."},

            # Kulit & Kelainan Otot
            "gatal": {"diag": "Dermatitis / Alergi", "obat": "CTM, Incidal, Kalpanax (jamur)", "tips": "Jaga kebersihan kulit."},
            "keseleo": {"diag": "Sprain (Cedera Ligamen)", "obat": "Voltaren Gel, Counterpain", "tips": "Gunakan metode R.I.C.E."},
            "pegal": {"diag": "Myalgia (Nyeri Otot)", "obat": "Hot In Cream, Salonpas", "tips": "Lakukan peregangan ringan."},
            "anemia": {"diag": "Kekurangan Sel Darah Merah", "obat": "Sangobion, Sangobion", "tips": "Makan daging merah dan bayam."},

            # Kelainan / Penyakit Kronis (Edukasi)
            "hipertensi": {"diag": "Tekanan Darah Tinggi", "obat": "Amlodipine (Resep Dokter)", "tips": "Kurangi konsumsi garam."},
            "diabetes": {"diag": "Gula Darah Tinggi", "obat": "Metformin (Resep Dokter)", "tips": "Kurangi konsumsi gula."},
            "asam urat": {"diag": "Gout Arthritis", "obat": "Allopurinol", "tips": "Hindari jeroan dan kacang-kacangan."}
        }

        # Inisialisasi Session
        if 'chat_step' not in session:
            session['chat_step'] = 1
            session['last_complaint'] = ""

        # --- LOGIKA AI SUPER SABAR & PINTAR ---
        
        # 1. Menangani Kata Umum (Agar Tidak Langsung "Mengusir")
        kata_umum = ["sakit", "nyeri", "tidak enak badan", "kurang sehat", "tolong"]
        if session['chat_step'] == 1:
            if user_msg in kata_umum or len(user_msg) < 4:
                return jsonify({"response": f"Halo {user_name}! Saya mengerti Anda merasa tidak nyaman. Agar saya bisa membantu lebih tepat, boleh tahu di bagian mana yang terasa sakit? (Misalnya: sakit perut atau pusing)"})
            
            # Jika user memberikan detail
            session['last_complaint'] = user_msg
            session['chat_step'] = 2
            return jsonify({"response": f"Terima kasih infonya. Saya mencatat keluhan **{user_msg}**. Sudah berapa lama ini dirasakan? Ada gejala lain?"})

        # 2. Tahap Analisis (AI Sabar Mencocokkan Data)
        else:
            complaint_awal = session.get('last_complaint', '')
            session['chat_step'] = 1 # Reset flow
            
            # Cari di Database
            for key, info in medical_db.items():
                if key in complaint_awal or key in user_msg:
                    return jsonify({"response": f"Berdasarkan keluhan Anda, berikut analisis saya:<br><br>" \
                                              f"🩺 **Diagnosa:** {info['diag']}<br>" \
                                              f"💊 **Obat:** {info['obat']}<br>" \
                                              f"📝 **Saran:** {info['tips']}<br><br>" \
                                              f"Semoga lekas sembuh, {user_name}!"})

            # Jika Benar-benar Tidak Ada (AI Tetap Sopan)
            return jsonify({"response": "Saya memahami keluhan Anda cukup spesifik. Karena keterbatasan AI, saya sarankan Anda berkonsultasi langsung dengan spesialis kami di menu **Cari RS** untuk hasil yang lebih akurat."})

    except Exception as e:
        return jsonify({"response": "Maaf, dr. AI sedang memproses data medis."}), 500

# @app.route('/set-language/<lang>')
# @login_required
# def set_language(lang):
#     if lang in ['id', 'en']:
#         session['lang'] = lang
#         session.modified = True  # ✅ Force save session
        
#         # ✅ AJAX Support untuk select onchange
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return jsonify({
#                 'status': 'success', 
#                 'lang': lang,
#                 'message': 'Bahasa berhasil diubah!'
#             })
    
    # # Normal redirect
    # referrer = request.referrer
    # if referrer and 'set-language' not in referrer.lower() and 'login' not in referrer.lower():
    #     return redirect(referrer)
    
    # return redirect(url_for('home'))

@app.route('/set-language/<lang>')
@login_required
def set_language(lang):
    if lang in ['id', 'en']:
        session['lang'] = lang

    # BALIK KE HALAMAN SEBELUMNYA
    return redirect(request.referrer or url_for('home'))



@app.route('/ai-check')
@login_required
def ai_check():
    chats = ChatHistory.query.filter_by(user_id=session['user_id']).order_by(ChatHistory.timestamp.asc()).all()
    return render_template('ai_check.html', chats=chats)

@app.route('/doctor')
@login_required
def doctor():
    doctors = Doctor.query.all()
    return render_template('doctor.html', doctors=doctors)

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
    appointments = Appointment.query.filter_by(user_id=session['user_id']).all()
    
    # Ambil data dokter untuk kolom kanan
    all_doctors = Doctor.query.limit(3).all()
    
    # Pastikan mengirimkan variabel 'recommended_doctors'
    return render_template('appointments.html', 
                           appointments=appointments, 
                           recommended_doctors=all_doctors)

@app.route('/submit-rating/<int:appointment_id>', methods=['POST'])
@login_required
def submit_rating(appointment_id):
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    # Simpan ke tabel Rating (Pastikan Anda sudah membuat model Rating di database)
    # Contoh logic:
    # new_rating = Rating(user_id=session['user_id'], appointment_id=appointment_id, skor=rating, pesan=comment)
    # db.session.add(new_rating)
    # db.session.commit()
    return redirect(url_for('my_appointments'))

@app.route('/healthy', methods=['GET', 'POST'])
@login_required
def healthy():
    today = datetime.now().date()
    
    # Ambil atau buat data hari ini
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

    # Logika Isi Otomatis Grafik 7 Hari
    labels = []
    values = []
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        labels.append(target_date.strftime('%a')) # Nama hari (Sen, Sel, dst)
        
        # Cari data di database, jika tidak ada isi 0
        record = HealthTrack.query.filter_by(user_id=session['user_id'], tanggal=target_date).first()
        values.append(record.olahraga_kalori if record else 0)

    progress = min(int((track.olahraga_kalori / 1000) * 100), 100)
    
    return render_template('healthy.html', track=track, labels=labels, values=values, progress=progress)

@app.route('/health-history')
@login_required
def health_history():
    # Ambil tanggal dari filter, jika tidak ada gunakan hari ini
    date_str = request.args.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()

    # Cari data di tanggal tersebut
    record = HealthTrack.query.filter_by(user_id=session['user_id'], tanggal=target_date).first()
    
    # Ambil semua daftar tanggal yang pernah diisi untuk navigasi cepat
    all_history = HealthTrack.query.filter_by(user_id=session['user_id']).order_by(HealthTrack.tanggal.desc()).all()
    
    return render_template('history.html', record=record, target_date=target_date, all_history=all_history)

@app.route('/maps')
@login_required
def maps():
    hospitals = Hospital.query.all()
    return render_template('maps.html', hospitals=hospitals)

if __name__ == '__main__':
    app.run(debug=True)