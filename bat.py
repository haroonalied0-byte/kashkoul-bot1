import os
import sys
import time
import random
import sqlite3
import threading
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# سيرفر وهمي لتشغيل Web Service على Render بدون مشاكل
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# استيراد مكتبات البوت والـ Gemini
try:
    import telebot
except ImportError:
    os.system(f"{sys.executable} -m pip install pytelegrambotapi")
    import telebot

try:
    from google import genai
    from google.genai import types
except ImportError:
    os.system(f"{sys.executable} -m pip install google-genai")
    from google import genai
    from google.genai import types

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from io import BytesIO

TOKEN = "8874853282:AAGM0P7LTIglCOmA1S7JC9pJ_dBJfVl-Ips"
ADMIN_ID = 8159938802
YOUR_USFRNAMF = "KASHKOUL QPU"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
bot = telebot.TeleBot(TOKEN)
QR_IMAGE_PATH = 'sham_cash.jpg'
COMM_TREE_PATH = 'Communications_Tree.pdf'
COMM_TREE_FILE_ID = None  

# تهيئة عميل جيميناي بالطريقة القياسية
try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"AI Client Init Error: {e}")
    ai_client = None

AVAILABLE_SUBJECTS = [
    "الفيزياء 1", "الفيزياء 2", "الفيزياء 3",
    "رياضيات 1", "رياضيات 2", "رياضيات 3",
    "رسم هندسي", "برمجة وفسيوة",
    "شبكات اتصالات رقمية", "اتصالات تماثلية",
    "أنظمة التشغيل", "أنظمة التحكم",
    "أنظمة الرادار", "الاتصال بالأقمار الصناعية",
    "أنظمة الشبكات", "إدارة الشبكات",
    "مشروع التخرج 1", "مشروع التخرج 2",
    "متطلبات الكلية الإجبارية", "متطلبات التخصص"
]

AZKAR_LIST = [
    "[ سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ ]",
    "[ لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ ]",
    "[ أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ ]",
    "[ سُبْحَانَ اللَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا اللَّهُ، وَاللَّهُ أَكْبَرُ ]",
    "[ اللَّهُمَّ صَلِّ وَسَلِّمْ وَبارِكْ عَلَى نَبِيِّنَا مُحَمَّدٍ ]"
]

# دالة الاستعلام الرسمية والمحدثة بالنموذج الصحيح gemini-3.8-flash
def ask_real_gemini(prompt_text):
    if not ai_client:
        return "عذراً، لم يتم تهيئة اتصال الذكاء الاصطناعي."
    try:
        response = ai_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt_text
        )
        if response and response.text:
            return response.text
        else:
            return "لم يتم استلام رد من النموذج."
    except Exception as e:
        return f"عذراً، حدث خطأ أثناء الاتصال: {e}"

def init_db():
    conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT,
            week_number INTEGER,
            secure_link TEXT,
            UNIQUE(course_name, week_number)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_name TEXT,
            week_number INTEGER,
            file_id TEXT,
            order_code TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id INTEGER,
            course_name TEXT,
            UNIQUE(user_id, course_name)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS smart_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day_name TEXT,
            subject_name TEXT,
            lecture_type TEXT,
            hall_name TEXT,
            start_time TEXT,
            end_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

user_pending_orders = {}
user_states = {}
user_last_message = {}

def generate_sorted_code():
    digits = sorted(random.sample(range(1, 10), 3))
    return "".join(map(str, digits))

def get_main_inline_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("تصفح المواد", callback_data="browse_subjects"),
        InlineKeyboardButton("التنبيه الذكي", callback_data="schedule_menu")
    )
    markup.row(
        InlineKeyboardButton("حاسبة المعدل", callback_data="gpa_calculator"),
        InlineKeyboardButton("الخدمات الخاصة", callback_data="special_services_menu")
    )
    markup.row(
        InlineKeyboardButton("شجرة المواد", callback_data="show_comm_tree"),
        InlineKeyboardButton("أذكر الله", callback_data="say_azkar")
    )
    markup.row(
        InlineKeyboardButton("🤖 محادثة الذكاء الاصطناعي", callback_data="ai_chat_start")
    )
    markup.row(
        InlineKeyboardButton("نبذة عن البوت", callback_data="bot_about")
    )
    return markup

def get_special_services_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📊 العروض التقديمية", callback_data="srv_ppt"),
        InlineKeyboardButton("🎓 مشاريع التخرج", callback_data="srv_graduation_writing")
    )
    markup.row(
        InlineKeyboardButton("📝 حل الواجبات", callback_data="srv_tasks"),
        InlineKeyboardButton("🌐 الترجمة", callback_data="srv_translate")
    )
    markup.row(
        InlineKeyboardButton("📁 تحويل الصيغ", callback_data="srv_convert"),
        InlineKeyboardButton("💻 مشاريع برمجة", callback_data="srv_final_prog")
    )
    markup.row(
        InlineKeyboardButton("📄 تصميم السيرة الذاتية", callback_data="srv_cv")
    )
    markup.row(
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    return markup

def get_admin_inline_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("لوحة الطالب", callback_data="admin_to_student"),
        InlineKeyboardButton("التحقق من الإيصالات", callback_data="admin_check_receipts")
    )
    markup.row(
        InlineKeyboardButton("إضافة رابط", callback_data="admin_add_link_menu"),
        InlineKeyboardButton("عرض الروابط", callback_data="admin_show_links_menu")
    )
    return markup

def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def send_or_replace_message(chat_id, text, reply_markup=None, parse_mode=None, is_photo=False, photo_path=None, protect_content=False):
    if chat_id in user_last_message:
        safe_delete_message(chat_id, user_last_message[chat_id])
    
    try:
        if is_photo and photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as p:
                img_bytes = BytesIO(p.read())
                img_bytes.name = "sham_cash.jpg"
                msg = bot.send_document(chat_id, img_bytes, caption=text, parse_mode=parse_mode, reply_markup=reply_markup, protect_content=protect_content)
        else:
            msg = bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup, protect_content=protect_content)
        
        user_last_message[chat_id] = msg.message_id
        return msg
    except Exception as e:
        print(f"Error sending message: {e}")

def notify_subscribers_new_week(course_name, week_number, secure_link):
    try:
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM user_subscriptions WHERE course_name = ?", (course_name,))
        subs = cursor.fetchall()
        conn.close()

        for (u_id,) in subs:
            try:
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("رابط ملف الأسبوع الجديد", url=secure_link))
                bot.send_message(
                    u_id,
                    f"تنبيه هام! تم رفع محتوى جديد:\n\nالمقرر: {course_name}\nالأسبوع: {week_number}\n\nالمحتوى أصبح متاحاً وجاهزاً للمتابعة لضمان تفوقك!",
                    parse_mode="Markdown",
                    reply_markup=markup,
                    protect_content=True
                )
            except Exception:
                pass
    except Exception as e:
        print(f"Error in notification thread: {e}")

def schedule_notification_worker():
    notified_today = set()
    while True:
        try:
            now = datetime.now()
            days_map = {
                "Saturday": "السبت",
                "Sunday": "الأحد",
                "Monday": "الإثنين",
                "Tuesday": "الثلاثاء",
                "Wednesday": "الأربعاء",
                "Thursday": "الخميس",
                "Friday": "الجمعة"
            }
            today_day_name = days_map.get(now.strftime("%A"), "")
            today_date_str = now.strftime("%Y-%m-%d")

            conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, day_name, subject_name, lecture_type, hall_name, start_time, end_time FROM smart_schedule")
            all_schedules = cursor.fetchall()
            conn.close()

            for s_id, u_id, d_name, s_name, l_type, hall, start_t, end_t in all_schedules:
                if d_name and d_name.strip().lower() == today_day_name.lower():
                    try:
                        sh, sm = map(int, start_t.split(':'))
                        start_total_mins = sh * 60 + sm
                        current_total_mins = now.hour * 60 + now.minute

                        alert_before_mins = start_total_mins - 5
                        if current_total_mins == alert_before_mins:
                            notif_key = f"start_{s_id}_{today_date_str}"
                            if notif_key not in notified_today:
                                notified_today.add(notif_key)
                                alert_text = (
                                    f"⏰ **تنبيه بقرب موعد المحاضرة!**\n\n"
                                    f"📚 المادة: `{s_name}` ({l_type})\n"
                                    f"🏛️ القاعة: `{hall}`\n"
                                    f"⏳ الموعد: من `{start_t}` إلى `{end_t}`\n\n"
                                    f"جهز نفسك، المحاضرة ستبدأ خلال 5 دقائق! بالتوفيق يا بطل!"
                                )
                                markup = InlineKeyboardMarkup()
                                markup.row(InlineKeyboardButton("عرض جدولي الشخصي", callback_data="schedule_menu"))
                                bot.send_message(u_id, alert_text, parse_mode="Markdown", reply_markup=markup, protect_content=True)

                    except Exception as e:
                        print(f"Time parse error: {e}")

        except Exception as e:
            print(f"Error in schedule worker: {e}")
            
        time.sleep(30)

threading.Thread(target=schedule_notification_worker, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states.pop(chat_id, None)
    
    if chat_id == ADMIN_ID:
        send_or_replace_message(chat_id, "مرحباً بك في لوحة تحكم الإدارة:", reply_markup=get_admin_inline_keyboard())
        return

    welcome_text = (
        "مرحباً بك في بوت كشكول جامعي\n\n"
        "بوابتك الرسمية للحصول على الملفات والشروحات الدقيقة للمقررات الدراسية، بالإضافة إلى الخدمات الأكاديمية الاحترافية.\n\n"
        "اختر من الأزرار أدناه لاستعراض الخدمات:"
    )
    send_or_replace_message(chat_id, welcome_text, reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    text = message.text
    chat_id = message.chat.id
    state = user_states.get(chat_id, {}).get("step")

    if state == "ai_chatting":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إنهاء محادثة الذكاء الاصطناعي.", reply_markup=get_main_inline_keyboard())
            return
        
        reply_text = ask_real_gemini(text)
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ إنهاء محادثة الذكاء الاصطناعي", callback_data="main_menu"))
        
        safe_delete_message(chat_id, message.message_id)
        send_or_replace_message(chat_id, f"🤖 **جيميناي:**\n\n{reply_text}", reply_markup=markup, parse_mode="Markdown")
        return

    if chat_id == ADMIN_ID and user_states.get(chat_id, {}).get("step") == "waiting_for_bulk_week_links":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء العملية.", reply_markup=get_admin_inline_keyboard())
            return
        try:
            week_num = user_states.get(chat_id, {}).get("target_week")
            lines = text.strip().split('\n')
            conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
            cursor = conn.cursor()
            
            count = 0
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    c_name = parts[0].strip()
                    c_link = parts[1].strip()
                    cursor.execute('''
                        INSERT INTO course_links (course_name, week_number, secure_link) 
                        VALUES (?, ?, ?)
                        ON CONFLICT(course_name, week_number) 
                        DO UPDATE SET secure_link = ?
                    ''', (c_name, week_num, c_link, c_link))
                    conn.commit()
                    count += 1
                    threading.Thread(target=notify_subscribers_new_week, args=(c_name, week_num, c_link)).start()

            conn.close()
            user_states.pop(chat_id, None)
            
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("إدارة الروابط والأسابيع", callback_data="admin_add_link_menu"))
            markup.row(InlineKeyboardButton("⬅️ رجوع لوحة الإدارة", callback_data="main_menu"))
            
            send_or_replace_message(chat_id, f"تم بنجاح تحديث وإضافة روابط (الأسبوع {week_num}) لـ ({count}) مادة وإرسال الإشعارات للمشتركين!", reply_markup=markup)
        except Exception as e:
            send_or_replace_message(chat_id, f"حدث خطأ في الصيغة: {e}\nأرسل كل مادة في سطر بالشكل:\n`اسم المادة | الرابط`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    if state == "waiting_for_schedule_details":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء إضافة المحاضرة.", reply_markup=get_main_inline_keyboard())
            return
        try:
            parts = text.split('|')
            day_name = parts[0].strip()
            s_name = parts[1].strip()
            l_type = parts[2].strip()
            hall = parts[3].strip()
            start_t = parts[4].strip()
            end_t = parts[5].strip()

            conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO smart_schedule (user_id, day_name, subject_name, lecture_type, hall_name, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (chat_id, day_name, s_name, l_type, hall, start_t, end_t))
            conn.commit()
            conn.close()

            user_states.pop(chat_id, None)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("عرض جدولي الشخصي", callback_data="schedule_menu"))
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
            send_or_replace_message(chat_id, f"تمت إضافة المحاضرة بنجاح إلى جدولك الذكي!\nسيتم تنبيهك قبل موعدها بـ 5 دقائق فقط.", reply_markup=markup)
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل بالصيغة التالية تماماً:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\nمثال:\n`السبت | فيزياء 1 | نظري | قاعة 3 | 10:00 | 11:00`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    if state == "waiting_for_edit_schedule_details":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء التعديل.", reply_markup=get_main_inline_keyboard())
            return
        try:
            parts = text.split('|')
            s_id = user_states.get(chat_id, {}).get("edit_schedule_id")
            day_name = parts[0].strip()
            s_name = parts[1].strip()
            l_type = parts[2].strip()
            hall = parts[3].strip()
            start_t = parts[4].strip()
            end_t = parts[5].strip()

            conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("UPDATE smart_schedule SET day_name = ?, subject_name = ?, lecture_type = ?, hall_name = ?, start_time = ?, end_time = ? WHERE id = ? AND user_id = ?", 
                           (day_name, s_name, l_type, hall, start_t, end_t, s_id, chat_id))
            conn.commit()
            conn.close()

            user_states.pop(chat_id, None)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("عرض جدولي الشخصي", callback_data="schedule_menu"))
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
            send_or_replace_message(chat_id, f"تم تحديث بيانات المحاضرة بنجاح!", reply_markup=markup)
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل بالصيغة التالية تماماً:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    if state == "waiting_for_semester_gpa":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء عملية حساب المعدل.", reply_markup=get_main_inline_keyboard())
            return
        try:
            lines = text.strip().split('\n')
            total_points = 0
            total_hours = 0
            for line in lines:
                parts = line.split('|')
                grade = float(parts[0].strip())
                hours = float(parts[1].strip())
                total_points += (grade * hours)
                total_hours += hours
            
            if total_hours == 0:
                raise ValueError("عدد الساعات لا يمكن أن يكون صفرًا.")
            
            gpa = total_points / total_hours
            user_states.pop(chat_id, None)

            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("حساب معدل جديد", callback_data="gpa_calculator"))
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
            
            if gpa < 55:
                status_message = (
                    f"نتيجة حساب المعدل الفصلي:\n\n"
                    f"- إجمالي الساعات: {total_hours}\n"
                    f"- المعدل المحسوب: {gpa:.2f}\n\n"
                    f"لا تقلق يا بطل!\n"
                    f"البدايات قد تكون صعبة، لكنها فرصة حقيقية لتصحيح المسار ومضاعفة الجهد في المواد القادمة. أنت قادر على التعويض وتحقيق أفضل النتائج في القادم إن شاء الله!"
                )
            else:
                status_message = (
                    f"نتيجة حساب المعدل الفصلي:\n\n"
                    f"- إجمالي الساعات: {total_hours}\n"
                    f"- المعدل المحسوب: {gpa:.2f}\n\n"
                    f"مبارك مقدماً!"
                )
            
            send_or_replace_message(chat_id, status_message, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل كل مادة في سطر بالشكل التالي:\n`العلامة | عدد الساعات`\nمثال:\n`85 | 3`\n`90 | 2`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    if state == "waiting_for_cumulative_prev":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء عملية حساب المعدل.", reply_markup=get_main_inline_keyboard())
            return
        try:
            parts = text.split('|')
            prev_hours = float(parts[0].strip())
            prev_gpa = float(parts[1].strip())
            
            user_states[chat_id] = {
                "step": "waiting_for_cumulative_current",
                "prev_hours": prev_hours,
                "prev_gpa": prev_gpa
            }
            
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="gpa_calculator"))
            send_or_replace_message(chat_id, "حساب المعدل التراكمي (الخطوة 2/2):\n\nالآن أرسل نقاط مواد الفصل الحالي وعدد الساعات (كل مادة في سطر):\n`النقاط (مثل 3.0) | عدد الساعات`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل البيانات هكذا:\n`إجمالي الساعات السابقة | المعدل التراكمي السابق`\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    if state == "waiting_for_cumulative_current":
        if text == "إلغاء":
            user_states.pop(chat_id, None)
            send_or_replace_message(chat_id, "تم إلغاء عملية حساب المعدل.", reply_markup=get_main_inline_keyboard())
            return
        try:
            prev_hours = user_states.get(chat_id, {}).get("prev_hours", 0)
            prev_gpa = user_states.get(chat_id, {}).get("prev_gpa", 0)
            
            lines = text.strip().split('\n')
            curr_points = 0
            curr_hours = 0
            for line in lines:
                parts = line.split('|')
                grade_point = float(parts[0].strip())
                hours = float(parts[1].strip())
                curr_points += (grade_point * hours)
                curr_hours += hours
            
            if curr_hours == 0:
                raise ValueError("عدد الساعات لا يمكن أن يكون صفرًا.")
            
            total_hours = prev_hours + curr_hours
            total_points = (prev_gpa * prev_hours) + curr_points
            cumulative_gpa = total_points / total_hours
            
            user_states.pop(chat_id, None)

            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("حساب معدل جديد", callback_data="gpa_calculator"))
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
            
            fail_threshold = 2.0 if prev_gpa <= 4.0 else 55.0
            
            if cumulative_gpa < fail_threshold:
                status_message = (
                    f"نتيجة حساب المعدل التراكمي:\n\n"
                    f"- إجمالي الساعات التراكمية: {total_hours}\n"
                    f"- المعدل التراكمي المحسوب: {cumulative_gpa:.2f}\n\n"
                    f"لا تقلق يا بطل، أنت قادر على التعويض في القادم إن شاء الله!"
                )
            else:
                status_message = (
                    f"نتيجة حساب المعدل التراكمي:\n\n"
                    f"- إجمالي الساعات التراكمية: {total_hours}\n"
                    f"- المعدل التراكمي المحسوب: {cumulative_gpa:.2f}\n\n"
                    f"مبارك مقدماً!"
                )
            
            send_or_replace_message(chat_id, status_message, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل كل مادة في سطر:\n`النقاط | عدد الساعات`\nأو اكتب `إلغاء`.", parse_mode="Markdown")
        return

    safe_delete_message(chat_id, message.message_id)
    send_or_replace_message(chat_id, "يرجى استخدام الأزرار التفاعلية للتنقل:", reply_markup=get_main_inline_keyboard() if chat_id != ADMIN_ID else get_admin_inline_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    global COMM_TREE_FILE_ID
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    if data == "ai_chat_start":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"step": "ai_chatting"}
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ إنهاء المحادثة والعودة للقائمة", callback_data="main_menu"))
        send_or_replace_message(
            chat_id, 
            "🤖 **مرحباً بك في مساعد الذكاء الاصطناعي (Gemini)**\n\n"
            "اكتب أي سؤال أو استفسار علمي أو أكاديمي وسأقوم بالإجابة عليك فوراً تماماً مثل المحادثة المباشرة.\n\n"
            "لإنهاء المحادثة في أي وقت، اضغط على زر العودة أدناه أو اكتب `إلغاء`.", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
        return

    if data == "admin_add_link_menu":
        if chat_id != ADMIN_ID:
            return
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        for i in range(1, 13, 3):
            markup.row(
                InlineKeyboardButton(f"رابط الأسبوع {i}", callback_data=f"admin_add_week_{i}"),
                InlineKeyboardButton(f"رابط الأسبوع {i+1}", callback_data=f"admin_add_week_{i+1}"),
                InlineKeyboardButton(f"رابط الأسبوع {i+2}", callback_data=f"admin_add_week_{i+2}")
            )
        markup.row(InlineKeyboardButton("⬅️ رجوع لوحة الإدارة", callback_data="main_menu"))
        send_or_replace_message(chat_id, "اختر الأسبوع الذي تريد إضافة أو تحديث روابطه لجميع المواد:", reply_markup=markup)
        return

    elif data.startswith("admin_add_week_"):
        if chat_id != ADMIN_ID:
            return
        week_num = int(data.replace("admin_add_week_", ""))
        user_states[chat_id] = {"step": "waiting_for_bulk_week_links", "target_week": week_num}
        bot.answer_callback_query(call.id)
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("حذف روابط هذا الأسبوع", callback_data=f"admin_clear_week_{week_num}"),
            InlineKeyboardButton("تعديل / تحديث الروابط", callback_data=f"admin_add_week_{week_num}")
        )
        markup.row(InlineKeyboardButton("⬅️ رجوع لقائمة الأسابيع", callback_data="admin_add_link_menu"))
        
        send_or_replace_message(
            chat_id, 
            f"أنت تقوم بإضافة/تحديث روابط **الأسبوع {week_num}** لجميع المواد.\n\n"
            f"أرسل البيانات برسالة واحدة بحيث تكون كل مادة في سطر بالشكل التالي:\n"
            f"`اسم المادة | الرابط`\n\n"
            f"مثال:\n"
            f"`الفيزياء 1 | https://t.me/...`\n"
            f"`رياضيات 1 | https://t.me/...`\n\n"
            f"أو اكتب `إلغاء` للرجوع.", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
        return

    elif data.startswith("admin_clear_week_"):
        if chat_id != ADMIN_ID:
            return
        week_num = int(data.replace("admin_clear_week_", ""))
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM course_links WHERE week_number = ?", (week_num,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "تم الحذف بنجاح.")
        send_or_replace_message(chat_id, f"تم حذف جميع روابط الأسبوع {week_num} بنجاح.", reply_markup=get_admin_inline_keyboard())
        return

    elif data == "admin_show_links_menu":
        if chat_id != ADMIN_ID:
            return
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        for i in range(1, 13, 3):
            markup.row(
                InlineKeyboardButton(f"الأسبوع {i}", callback_data=f"admin_show_week_{i}"),
                InlineKeyboardButton(f"الأسبوع {i+1}", callback_data=f"admin_show_week_{i+1}"),
                InlineKeyboardButton(f"الأسبوع {i+2}", callback_data=f"admin_show_week_{i+2}")
            )
        markup.row(InlineKeyboardButton("⬅️ رجوع لوحة الإدارة", callback_data="main_menu"))
        send_or_replace_message(chat_id, "اختر الأسبوع لعرض الروابط المخزنة فيه لكل المواد:", reply_markup=markup)
        return

    elif data.startswith("admin_show_week_"):
        if chat_id != ADMIN_ID:
            return
        week_num = int(data.replace("admin_show_week_", ""))
        bot.answer_callback_query(call.id)
        
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT course_name, secure_link FROM course_links WHERE week_number = ? ORDER BY course_name", (week_num,))
        links = cursor.fetchall()
        conn.close()

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع لقائمة الأسابيع", callback_data="admin_show_links_menu"))

        if not links:
            send_or_replace_message(chat_id, f"لا توجد أي روابط مخزنة للأسبوع {week_num}.", reply_markup=markup)
            return

        text = f"📁 **الروابط المخزنة للأسبوع {week_num}:**\n\n"
        for c_name, s_link in links:
            text += f"🔹 {c_name}:\n{s_link}\n\n"
        
        if len(text) > 4096:
            text = text[:4090] + "..."
            
        send_or_replace_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
        return

    elif data == "say_azkar":
        random_zekr = random.choice(AZKAR_LIST)
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("ذكر آخر", callback_data="say_azkar"))
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        send_or_replace_message(chat_id, f"أذكر الله يذكرك:\n\n{random_zekr}", reply_markup=markup)

    elif data == "schedule_menu":
        bot.answer_callback_query(call.id)
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, day_name, subject_name, lecture_type, hall_name, start_time, end_time FROM smart_schedule WHERE user_id = ? ORDER BY CASE day_name WHEN 'السبت' THEN 1 WHEN 'الأحد' THEN 2 WHEN 'الإثنين' THEN 3 WHEN 'الثلاثاء' THEN 4 ELSE 5 END, start_time ASC", (chat_id,))
        schedules = cursor.fetchall()
        conn.close()

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("إضافة محاضرة للجدول", callback_data="add_schedule_item"))
        
        if schedules:
            markup.row(InlineKeyboardButton("تعديل محاضرة", callback_data="edit_schedule_select"))
            markup.row(InlineKeyboardButton("تفريغ الجدول بالكامل", callback_data="clear_schedule"))
            
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))

        text = "📅 **جدول المحاضرات الشخصي الذكي**\n\n"
        if not schedules:
            text += "جدولك فارغ حالياً. قم بإضافة محاضراتك لتتلقى تنبيهات تلقائية قبل كل محاضرة بـ 5 دقائق."
        else:
            current_day = ""
            for s_id, d_name, s_name, l_type, hall, start_t, end_t in schedules:
                if d_name != current_day:
                    current_day = d_name
                    text += f"\n🗓️ **[ يوم {current_day} ]**\n"
                text += f"📚 مادة: *{s_name}* ({l_type})\n🏛️ القاعة: {hall}\n⏰ الموعد: من `{start_t}` إلى `{end_t}`\n\n"

        send_or_replace_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif data == "add_schedule_item":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"step": "waiting_for_schedule_details"}
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="schedule_menu"))
        send_or_replace_message(chat_id, "أرسل تفاصيل المحاضرة بالصيغة التالية تماماً:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\n\nمثال:\n`السبت | فيزياء 1 | نظري | قاعة 1 | 10:00 | 11:00`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

    elif data == "edit_schedule_select":
        bot.answer_callback_query(call.id)
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, day_name, subject_name, start_time FROM smart_schedule WHERE user_id = ?", (chat_id,))
        schedules = cursor.fetchall()
        conn.close()

        markup = InlineKeyboardMarkup()
        if not schedules:
            markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="schedule_menu"))
            send_or_replace_message(chat_id, "لا توجد محاضرات لتعديلها.", reply_markup=markup)
            return

        for s_id, d_name, s_name, start_t in schedules:
            markup.row(InlineKeyboardButton(f"تعديل: {d_name} - {s_name} ({start_t})", callback_data=f"edit_sch_{s_id}"))
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="schedule_menu"))
        
        send_or_replace_message(chat_id, "اختر المحاضرة التي تريد تعديلها:", reply_markup=markup)

    elif data.startswith("edit_sch_"):
        bot.answer_callback_query(call.id)
        s_id = int(data.replace("edit_sch_", ""))
        user_states[chat_id] = {"step": "waiting_for_edit_schedule_details", "edit_schedule_id": s_id}
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="schedule_menu"))
        send_or_replace_message(chat_id, "أرسل البيانات الجديدة:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

    elif data == "clear_schedule":
        bot.answer_callback_query(call.id)
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM smart_schedule WHERE user_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="schedule_menu"))
        send_or_replace_message(chat_id, "تم تفريغ جدولك الشخصي بنجاح.", reply_markup=markup)

    elif data == "gpa_calculator":
        bot.answer_callback_query(call.id)
        user_states.pop(chat_id, None)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("المعدل الفصلي", callback_data="gpa_semester"))
        markup.row(InlineKeyboardButton("المعدل التراكمي", callback_data="gpa_cumulative"))
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        send_or_replace_message(chat_id, "حاسبة المعدل الجامعي:\n\nاختر نوع الحساب الذي تريده:", reply_markup=markup, parse_mode="Markdown")

    elif data == "gpa_semester":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"step": "waiting_for_semester_gpa"}
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="gpa_calculator"))
        send_or_replace_message(chat_id, "حساب المعدل الفصلي:\n\nأرسل علاماتك وعدد الساعات (كل مادة في سطر):\n`العلامة | عدد الساعات`\n\nمثال:\n`85 | 3`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

    elif data == "gpa_cumulative":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"step": "waiting_for_cumulative_prev"}
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="gpa_calculator"))
        send_or_replace_message(chat_id, "حساب المعدل التراكمي (الخطوة 1/2):\n\nأرسل بياناتك السابقة:\n`إجمالي الساعات السابقة | المعدل التراكمي السابق`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

    elif data == "special_services_menu":
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, "قائمة الخدمات الخاصة:\n\nاختر الخدمة المطلوبة من القائمة أدناه:", reply_markup=get_special_services_keyboard(), parse_mode="Markdown")

    elif data in ["srv_cv", "srv_ppt", "srv_tasks", "srv_graduation_writing", "srv_final_prog", "srv_convert", "srv_translate"]:
        bot.answer_callback_query(call.id)
        titles = {
            "srv_ppt": "📊 العروض التقديمية",
            "srv_graduation_writing": "🎓 مشاريع التخرج (كتابة)",
            "srv_tasks": "📝 حل الواجبات",
            "srv_translate": "🌐 ترجمة (عربي/انجليزي)",
            "srv_convert": "📁 تحويل صيغ الملفات",
            "srv_final_prog": "💻 مشاريع تخرج (برمجة)",
            "srv_cv": "📄 تصميم سيرة ذاتية"
        }
        service_name = titles.get(data, "الخدمة المطلوبة")
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("اطلب الخدمة الآن", url=f"https://t.me/{YOUR_USERNAME}"))
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="special_services_menu"))
        text = f"خدمة: {service_name}\n\nلطلب هذه الخدمة والاستفسار عن التفاصيل، اضغط على الزر أدناه للتواصل المباشر مع الإدارة."
        send_or_replace_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif data == "show_comm_tree":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        
        caption_text = "مخطط الشجرة الخاص بهندسة الاتصالات"
        safe_delete_message(chat_id, message_id)
        
        try:
            if COMM_TREE_FILE_ID:
                msg = bot.send_document(chat_id, document=COMM_TREE_FILE_ID, caption=caption_text, parse_mode="Markdown", reply_markup=markup, protect_content=True)
                user_last_message[chat_id] = msg.message_id
            elif os.path.exists(COMM_TREE_PATH):
                with open(COMM_TREE_PATH, "rb") as doc_file:
                    msg = bot.send_document(chat_id, document=doc_file, caption=caption_text, parse_mode="Markdown", reply_markup=markup, protect_content=True)
                    user_last_message[chat_id] = msg.message_id
                    COMM_TREE_FILE_ID = msg.document.file_id
            else:
                send_or_replace_message(chat_id, f"{caption_text}\n\n(يرجى التأكد من وضع ملف Communications_Tree.pdf في مجلد البوت)", reply_markup=markup)
        except Exception:
            send_or_replace_message(chat_id, caption_text, reply_markup=markup)

    elif data == "browse_subjects":
        user_states[chat_id] = {"step": "browsing_subjects"}
        markup = InlineKeyboardMarkup()
        for i in range(0, len(AVAILABLE_SUBJECTS), 2):
            row = [InlineKeyboardButton(AVAILABLE_SUBJECTS[i], callback_data=f"sub_{i}")]
            if i + 1 < len(AVAILABLE_SUBJECTS):
                row.append(InlineKeyboardButton(AVAILABLE_SUBJECTS[i+1], callback_data=f"sub_{i+1}"))
            markup.row(*row)
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, "اختر المادة المطلوبة من القائمة أدناه:", reply_markup=markup)

    elif data.startswith("sub_"):
        sub_index = int(data.replace("sub_", ""))
        sub_name = AVAILABLE_SUBJECTS[sub_index]
        user_states[chat_id] = {"step": "viewing_weeks", "selected_subject": sub_name}

        markup = InlineKeyboardMarkup()
        for i in range(1, 13, 3):
            row = [
                InlineKeyboardButton(f"الأسبوع {i}", callback_data=f"week_{i}"),
                InlineKeyboardButton(f"الأسبوع {i+1}", callback_data=f"week_{i+1}"),
                InlineKeyboardButton(f"الأسبوع {i+2}", callback_data=f"week_{i+2}")
            ]
            markup.row(*row)
        markup.row(
            InlineKeyboardButton("⬅️ رجوع", callback_data="browse_subjects")
        )

        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, f"المادة المختارة: {sub_name}\n\nاختر الأسبوع الدراسي المطلوب:", reply_markup=markup, parse_mode="Markdown")

    elif data.startswith("week_"):
        week_num = int(data.replace("week_", ""))
        current_sub = user_states.get(chat_id, {}).get("selected_subject")
        if not current_sub:
            bot.answer_callback_query(call.id, "اختر المادة أولاً.")
            return

        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT secure_link FROM course_links WHERE TRIM(course_name) = TRIM(?) AND week_number = ?", (current_sub, week_num))
        res = cursor.fetchone()
        conn.close()

        markup = InlineKeyboardMarkup()
        if not res or not res[0]:
            markup.row(
                InlineKeyboardButton("⬅️ رجوع", callback_data=f"sub_{AVAILABLE_SUBJECTS.index(current_sub)}")
            )
            bot.answer_callback_query(call.id)
            send_or_replace_message(chat_id, f"المادة: {current_sub}\nالأسبوع {week_num}\n\nغير متاح حالياً.", reply_markup=markup)
            return

        user_states[chat_id]["step"] = "selected_week_payment"
        user_states[chat_id]["selected_week"] = week_num

        order_code = generate_sorted_code()
        expire_time = time.time() + 1800
        
        user_pending_orders[chat_id] = {
            'subject': current_sub,
            'week': week_num,
            'order_code': order_code,
            'expire_time': expire_time
        }
        
        markup.row(InlineKeyboardButton("الدفع عبر شام كاش", callback_data="pay_sham_cash"))
        markup.row(
            InlineKeyboardButton("⬅️ رجوع", callback_data=f"sub_{AVAILABLE_SUBJECTS.index(current_sub)}")
        )
        
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, f"الأسبوع {week_num} من مادة {current_sub} متاح.\n\nاضغط زر الدفع أدناه لمتابعة التحويل:", reply_markup=markup, parse_mode="Markdown")

    elif data == "pay_sham_cash":
        if chat_id not in user_pending_orders:
            bot.answer_callback_query(call.id, "انتهت الجلسة.")
            return

        order_data = user_pending_orders[chat_id]
        order_code = order_data['order_code']
        current_sub = order_data['subject']
        week_num = order_data['week']
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("إرسال إيصال التحويل", callback_data="verify_payment"))
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data=f"week_{week_num}"))
        
        payment_caption = (
            f"طريقة الدفع عبر شام كاش\n"
            f"المقرر: {current_sub} (الأسبوع {week_num})\n\n"
            f"قم بتحويل مبلغ وقدره 150 ل.س جديد\n"
            f"اكتب الكود قبل التحويل في مربع الملاحظة: `{order_code}`\n"
            f"عند إتمام عملية التحويل اضغط على الزر أدناه لإرسال إيصال التحويل"
        )

        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, payment_caption, reply_markup=markup, parse_mode="Markdown", is_photo=True, photo_path=QR_IMAGE_PATH, protect_content=True)

    elif data == "verify_payment":
        if chat_id not in user_pending_orders:
            bot.answer_callback_query(call.id, "خطأ بالطلب.")
            return
            
        user_states[chat_id]["step"] = "waiting_for_receipt"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="pay_sham_cash"))
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, "يرجى إرسال ملف التحويل أو صورة الإيصال الآن ليتم مراجعته وتفعيل اشتراكك من قِبل الإدارة.", parse_mode="Markdown", reply_markup=markup)

    elif data == "bot_about":
        bot.answer_callback_query(call.id)
        about_text = "«يُقدّم بوت (Kashkoul Jami'i) مواكبة أسبوعية لكل مقرر دراسي تماشيًا مع ما يطرحه أستاذ المادة، وذلك عبر توفير ملفات رقمية مشروحة بشكل دوري ومستمر كل أسبوع؛ لضمان متابعة الطالب وعدم تشتته طوال الفصل الدراسي الأول. إضافةً إلى تقديم خدمات متميزة لكل طالب جامعي طوال مسيرته الأكاديمية.»"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        send_or_replace_message(chat_id, about_text, reply_markup=markup, parse_mode="Markdown")

    elif data == "main_menu":
        user_states.pop(chat_id, None)
        bot.answer_callback_query(call.id)
        if chat_id == ADMIN_ID:
            send_or_replace_message(chat_id, "لوحة تحكم الإدارة:", reply_markup=get_admin_inline_keyboard())
        else:
            send_or_replace_message(chat_id, "القائمة الرئيسية:", reply_markup=get_main_inline_keyboard())

    elif data == "admin_check_receipts":
        if chat_id != ADMIN_ID:
            return
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, course_name, week_number, file_id, order_code FROM pending_receipts WHERE status = 'pending'")
        receipts = cursor.fetchall()
        conn.close()

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))

        if not receipts:
            bot.answer_callback_query(call.id, "لا توجد إيصالات معلقة.")
            send_or_replace_message(chat_id, "لا توجد أي إيصالات معلقة بانتظار المراجعة.", reply_markup=markup)
            return

        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, f"يوجد ({len(receipts)}) إيصال بانتظار المراجعة:", reply_markup=markup)

        for rec_id, u_id, c_name, w_num, f_id, o_code in receipts:
            rec_markup = InlineKeyboardMarkup()
            rec_markup.row(
                InlineKeyboardButton("قبول وتفعيل", callback_data=f"admin_approve_{rec_id}_{u_id}"),
                InlineKeyboardButton("رفض", callback_data=f"admin_reject_{rec_id}_{u_id}")
            )
            caption = f"إيصال جديد:\n- المستخدم: `{u_id}`\n- المادة: {c_name} (الأسبوع {w_num})\n- الكود: `{o_code}`"
            try:
                bot.send_document(chat_id, f_id, caption=caption, parse_mode="Markdown", reply_markup=rec_markup, protect_content=True)
            except Exception:
                try:
                    bot.send_photo(chat_id, f_id, caption=caption, parse_mode="Markdown", reply_markup=rec_markup, protect_content=True)
                except Exception:
                    bot.send_message(chat_id, f"{caption}\n(تعذر عرض الملف)", reply_markup=rec_markup, protect_content=True)

    elif data.startswith("admin_approve_"):
        if chat_id != ADMIN_ID:
            return
        parts = data.replace("admin_approve_", "").split("_")
        rec_id = parts[0]
        target_user_id = int(parts[1])

        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT course_name, week_number FROM pending_receipts WHERE id = ?", (rec_id,))
        row = cursor.fetchone()
        if row:
            c_name, w_num = row[0], row[1]
            cursor.execute("SELECT secure_link FROM course_links WHERE TRIM(course_name) = TRIM(?) AND week_number = ?", (c_name, w_num))
            link_res = cursor.fetchone()
            secure_link = link_res[0] if link_res else "https://t.me"

            cursor.execute("UPDATE pending_receipts SET status = 'approved' WHERE id = ?", (rec_id,))
            cursor.execute("INSERT OR IGNORE INTO user_subscriptions (user_id, course_name) VALUES (?, ?)", (target_user_id, c_name))
            conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "تم التفعيل.")
        send_or_replace_message(chat_id, f"تم قبول إيصال المستخدم `{target_user_id}` بنجاح وتفعيل اشتراكه.", reply_markup=get_admin_inline_keyboard())

        try:
            link_markup = InlineKeyboardMarkup()
            link_markup.row(InlineKeyboardButton("اضغط هنا للانتقال إلى ملف المادة", url=secure_link))
            bot.send_message(
                target_user_id, 
                f"تم قبول إيصالك بنجاح وتفعيل:\n{c_name} (الأسبوع {w_num}).\n\nرابط الملف الخاص بك جاهز:", 
                reply_markup=link_markup, 
                parse_mode="Markdown",
                protect_content=True
            )

            motiv_text = "💪 عاش يا بطل!\nخطوة ممتازة نحو التفوق والنجاح. نَظِّم وقتك، واقرأ الشرح بتركيز، وكن على أتم الاستعداد لتحقيق أعلى الدرجات هذا الفصل! نحن معك دائماً لضمان تميزك، موفق إن شاء الله. ❤️"
            motiv_msg = bot.send_message(
                target_user_id, 
                motiv_text, 
                parse_mode="Markdown", 
                reply_markup=get_main_inline_keyboard(),
                protect_content=True
            )
            user_last_message[target_user_id] = motiv_msg.message_id
        except Exception:
            pass

    elif data.startswith("admin_reject_"):
        if chat_id != ADMIN_ID:
            return
        parts = data.replace("admin_reject_", "").split("_")
        rec_id = parts[0]
        target_user_id = int(parts[1])

        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE pending_receipts SET status = 'rejected' WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "تم الرفض.")
        send_or_replace_message(chat_id, f"تم رفض إيصال المستخدم `{target_user_id}`.", reply_markup=get_admin_inline_keyboard())
        try:
            bot.send_message(target_user_id, "عذراً، تم رفض الإيصال من قبل الإدارة.", protect_content=True)
        except Exception:
            pass

    elif data == "admin_to_student":
        if chat_id != ADMIN_ID:
            return
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, "لوحة الطالب الرئيسية:", reply_markup=get_main_inline_keyboard())

@bot.message_handler(content_types=['document', 'photo'])
def handle_receipt_file(message):
    chat_id = message.chat.id
    if chat_id not in user_pending_orders:
        bot.reply_to(message, "ليس لديك طلب دفع نشط.")
        return
        
    order_data = user_pending_orders[chat_id]
    if time.time() > order_data['expire_time']:
        del user_pending_orders[chat_id]
        user_states.pop(chat_id, None)
        send_or_replace_message(chat_id, "انتهت صلاحية الطلب. يرجى البدء من جديد.", reply_markup=get_main_inline_keyboard())
        return
        
    sub_name = order_data['subject']
    week_num = order_data['week']
    order_code = order_data['order_code']
    
    try:
        if message.document:
            file_id = message.document.file_id
        else:
            file_id = message.photo[-1].file_id
    except Exception:
            file_id = ""

    safe_delete_message(chat_id, message.message_id)

    conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pending_receipts (user_id, course_name, week_number, file_id, order_code, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    ''', (chat_id, sub_name, week_num, file_id, order_code))
    conn.commit()
    conn.close()

    send_or_replace_message(chat_id, "تم استلام ملف التحويل بنجاح.\n\nيرجى الانتظار قليلاً ريثما يتم التحقق من الإيصال وتفعيل اشتراكك من قِبل الإدارة.", reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")

    try:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("مراجعة الإيصالات", callback_data="admin_check_receipts"))
        bot.send_message(ADMIN_ID, f"إيصال جديد للمادة: {sub_name} (الأسبوع {week_num}).", parse_mode="Markdown", reply_markup=markup, protect_content=True)
    except Exception:
        pass

    del user_pending_orders[chat_id]
    user_states.pop(chat_id, None)

if __name__ == '__main__':
    print("البوت يعمل الآن بكامل الميزات وبنموذج gemini-2.5-flash النظامي...")
    bot.infinity_polling()
