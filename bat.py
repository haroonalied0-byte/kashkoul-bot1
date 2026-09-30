import os
import sys
import time
import random
import sqlite3
import threading
from datetime import datetime
from flask import Flask

# سيرفر وهمي لتشغيل Web Service على Render بدون مشاكل
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
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
except ImportError:
    os.system(f"{sys.executable} -m pip install google-genai")
    from google import genai

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from io import BytesIO

TOKEN = "8874853282:AAGM0P7LTIglCOmA1S7JC9pJ_dBJfVl-Ips"
ADMIN_ID = 8159938802
YOUR_USERNAME = "KASHKOULQPU"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
bot = telebot.TeleBot(TOKEN)
QR_IMAGE_PATH = 'sham_cash.jpg'
COMM_TREE_PATH = 'Communications_Tree.pdf'
COMM_TREE_FILE_ID = None  

try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
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

def ask_real_gemini(prompt_text):
    if not ai_client:
        return "عذراً، لم يتم تهيئة اتصال الذكاء الاصطناعي (تحقق من مفتاح GEMINI_API_KEY)."
    try:
        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt_text
        )
        if response and response.text:
            return response.text
        else:
            return "لم يتم استلام رد من النموذج."
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            return "عذراً، لقد استهلكنا الحد المجاني اليوم، يرجى المحاولة غداً أو بعد قليل."
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
        InlineKeyboardButton("⏰ التنبيه الذكي", callback_data="schedule_menu"),
        InlineKeyboardButton("🔍 تصفح المواد", callback_data="browse_subjects")
    )
    markup.row(
        InlineKeyboardButton("🧮 حاسبة المعدل", callback_data="gpa_calculator"),
        InlineKeyboardButton("💎 الخدمات الخاصة", callback_data="special_services_menu")
    )
    markup.row(
        InlineKeyboardButton("🌿 شجرة المواد", callback_data="show_comm_tree"),
        InlineKeyboardButton("📿 أذكر الله", callback_data="say_azkar")
    )
    markup.row(
        InlineKeyboardButton("محادثة الذكاء الاصطناعي\n🤖", callback_data="ai_chat_start")
    )
    markup.row(
        InlineKeyboardButton("✍️ نبذة عن البوت", callback_data="bot_about")
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
        InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu")
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

def parse_time_12h_to_minutes(time_str):
    try:
        time_str = str(time_str).strip()
        # تنظيف الكلمات العربية والأرقام الهندية إن وجدت
        time_str = (time_str
                    .replace('٠', '0').replace('١', '1').replace('٢', '2').replace('٣', '3').replace('٤', '4')
                    .replace('٥', '5').replace('٦', '6').replace('٧', '7').replace('٨', '8').replace('٩', '9')
                    .replace("صباحاً", "").replace("صباح", "")
                    .replace("مساءً", "").replace("مساء", "")
                    .replace("ظهراً", "").replace("ظهر", "")
                    .strip())
        
        is_pm = any(w in str(time_str) for w in ["مساء", "ظهر"])
        is_am = any(w in str(time_str) for w in ["صباح"])
        
        parts = time_str.split(':')
        h = int(parts[0].strip())
        m = int(parts[1].strip()) if len(parts) > 1 else 0
        
        # إذا كانت الصيغة 12 ساعة ولم يتم تحديد صراحة، نتركها كما أدخلها المستخدم
        if ("مساء" in str(time_str) or "مساءً" in str(time_str)) and h < 12:
            h += 12
        return h * 60 + m
    except Exception as e:
        print(f"Parse time error for '{time_str}': {e}")
        return 0

def schedule_notification_worker():
    notified_today = set()
    valid_college_days = ["السبت", "الأحد", "الإثنين", "الثلاثاء"]
    
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

            # مسح الذاكرة المؤقتة للتنبيهات عند منتصف الليل لتجديدها لليوم الجديد
            if len(notified_today) > 100:
                notified_today.clear()

            # السماح أيام الدوام فقط (السبت، الأحد، الإثنين، الثلاثاء)
            if today_day_name in valid_college_days:
                conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT id, user_id, day_name, subject_name, lecture_type, hall_name, start_time, end_time FROM smart_schedule")
                all_schedules = cursor.fetchall()
                conn.close()

                current_total_mins = now.hour * 60 + now.minute

                for s_id, u_id, d_name, s_name, l_type, hall, start_t, end_t in all_schedules:
                    if d_name and d_name.strip().lower() == today_day_name.lower():
                        try:
                            start_total_mins = parse_time_12h_to_minutes(start_t)
                            end_total_mins = parse_time_12h_to_minutes(end_t)
                            
                            # تنبيه البدء قبل الموعد بـ 5 دقائق بالضبط
                            alert_start_mins = start_total_mins - 5
                            notif_key = f"start_{s_id}_{today_date_str}"
                            if notif_key not in notified_today:
                                if alert_start_mins <= current_total_mins <= alert_start_mins + 2:
                                    notified_today.add(notif_key)
                                    alert_text = (
                                        f"⏰ **تنبيه بقرب موعد المحاضرة!**\n\n"
                                        f"📚 المادة: `{s_name}` ({l_type})\n"
                                        f"🏛️ القاعة: `{hall}`\n"
                                        f"⏳ الموعد: من `{start_t}` إلى `{end_t}`\n\n"
                                        f"جهز نفسك، المحاضرة ستبدأ خلال 5 دقائق! بالتوفيق يا بطل!"
                                    )
                                    markup = InlineKeyboardMarkup()
                                    markup.row(InlineKeyboardButton("⏰ التنبيه الذكي", callback_data="schedule_menu"))
                                    bot.send_message(u_id, alert_text, parse_mode="Markdown", reply_markup=markup, protect_content=True)

                            # تنبيه الانتهاء عند وقت الانتهاء تماماً بالدقيقة
                            notif_end_key = f"end_{s_id}_{today_date_str}"
                            if notif_end_key not in notified_today:
                                if end_total_mins <= current_total_mins <= end_total_mins + 2:
                                    notified_today.add(notif_end_key)
                                    end_alert_text = (
                                        f"⏳ **تنبيه انتهاء المحاضرة!**\n\n"
                                        f"📚 المادة: `{s_name}` ({l_type})\n"
                                        f"🏛️ القاعة: `{hall}`\n"
                                        f"⏰ انتهى موعد المحاضرة تماماً (كانت من `{start_t}` إلى `{end_t}`).\n\n"
                                        f"نتمنى أن تكون قد استفدت بكامل التركيز!"
                                    )
                                    markup = InlineKeyboardMarkup()
                                    markup.row(InlineKeyboardButton("⏰ التنبيه الذكي", callback_data="schedule_menu"))
                                    bot.send_message(u_id, end_alert_text, parse_mode="Markdown", reply_markup=markup, protect_content=True)

                        except Exception as e:
                            print(f"Time calculation error: {e}")

        except Exception as e:
            print(f"Error in schedule worker: {e}")
            
        time.sleep(10)

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
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
        
        safe_delete_message(chat_id, message.message_id)
        send_or_replace_message(chat_id, f"🤖 **جيميناي:**\n\n{reply_text}", reply_markup=markup, parse_mode="Markdown")
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
            markup.row(InlineKeyboardButton("⏰ التنبيه الذكي", callback_data="schedule_menu"))
            markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
            send_or_replace_message(chat_id, f"تمت إضافة المحاضرة بنجاح إلى جدولك الذكي!\nسيتم تنبيهك قبل البدء بـ 5 دقائق، وعند الانتهاء تماماً.", reply_markup=markup)
        except Exception:
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل بالصيغة التالية تماماً:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\nمثال:\n`الإثنين | فيزياء 1 | نظري | قاعة 1 | 4:10 صباحاً | 4:20 صباحاً`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
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
            markup.row(InlineKeyboardButton("🧮 حاسبة المعدل", callback_data="gpa_calculator"))
            markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
            
            if gpa < 55:
                status_message = (
                    f"نتيجة حساب المعدل الفصلي:\n\n"
                    f"- إجمالي الساعات: {total_hours}\n"
                    f"- المعدل المحسوب: {gpa:.2f}\n\n"
                    f"لا تقلق يا بطل!\n"
                    f"البدايات قد تكون صعبة، لكنها فرصة حقيقية لتصحيح المسار ومضاعفة الجهد في المواد القادمة. أنت قادر على التعويض وتطوير أدائك في القادم إن شاء الله!"
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
            send_or_replace_message(chat_id, "خطأ في الصيغة. أرسل كل مادة في سطر بالشكل التالي:\n`العلامة | عدد الساعات`\nمثال:\n`85 | 3`\n\nأو اكتب `إلغاء`.", parse_mode="Markdown")
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
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
        send_or_replace_message(
            chat_id, 
            "🤖 **مرحباً بك في مساعد الذكاء الاصطناعي (Gemini)**\n\n"
            "اكتب أي سؤال أو استفسار علمي أو أكاديمي وسأقوم بالإجابة عليك فوراً.\n\n"
            "لإنهاء المحادثة في أي وقت، اضغط على زر العودة أدناه أو اكتب `إلغاء`.", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
        return

    elif data == "schedule_menu":
        bot.answer_callback_query(call.id)
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, day_name, subject_name, lecture_type, hall_name, start_time, end_time FROM smart_schedule WHERE user_id = ? ORDER BY CASE day_name WHEN 'السبت' THEN 1 WHEN 'الأحد' THEN 2 WHEN 'الإثنين' THEN 3 WHEN 'الثلاثاء' THEN 4 ELSE 5 END, id ASC", (chat_id,))
        schedules = cursor.fetchall()
        conn.close()

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("إضافة محاضرة للجدول", callback_data="add_schedule_item"))
        
        if schedules:
            markup.row(InlineKeyboardButton("تفريغ الجدول بالكامل", callback_data="clear_schedule"))
            
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))

        text = "📅 **جدول المحاضرات الشخصي الذكي (أيام الدوام: السبت، الأحد، الإثنين، الثلاثاء)**\n\n"
        if not schedules:
            text += "جدولك فارغ حالياً. قم بإضافة محاضراتك لتتلقى تنبيهات تلقائية قبل البدء بـ 5 دقائق وعند الانتهاء تماماً."
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
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data="schedule_menu"))
        send_or_replace_message(chat_id, "أرسل تفاصيل المحاضرة بالصيغة التالية تماماً:\n`اليوم | اسم المادة | نظري أو عملي | اسم القاعة | وقت البدء | وقت الانتهاء`\n\nمثال:\n`الإثنين | فيزياء 1 | نظري | قاعة 1 | 4:10 صباحاً | 4:20 صباحاً`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

    elif data == "clear_schedule":
        bot.answer_callback_query(call.id)
        conn = sqlite3.connect('kashkoul.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM smart_schedule WHERE user_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data="schedule_menu"))
        send_or_replace_message(chat_id, "تم تفريغ جدولك الشخصي بنجاح.", reply_markup=markup)

    elif data == "gpa_calculator":
        bot.answer_callback_query(call.id)
        user_states.pop(chat_id, None)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("المعدل الفصلي", callback_data="gpa_semester"))
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
        send_or_replace_message(chat_id, "حاسبة المعدل الجامعي:\n\nاختر نوع الحساب الذي تريده:", reply_markup=markup, parse_mode="Markdown")

    elif data == "gpa_semester":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"step": "waiting_for_semester_gpa"}
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data="gpa_calculator"))
        send_or_replace_message(chat_id, "حساب المعدل الفصلي:\n\nأرسل علاماتك وعدد الساعات (كل مادة في سطر):\n`العلامة | عدد الساعات`\n\nمثال:\n`85 | 3`\n\nأو اكتب `إلغاء` للرجوع.", reply_markup=markup, parse_mode="Markdown")

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
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data="special_services_menu"))
        text = f"خدمة: {service_name}\n\nلطلب هذه الخدمة والاستفسار عن التفاصيل، اضغط على الزر أدناه للتواصل المباشر مع الإدارة."
        send_or_replace_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif data == "show_comm_tree":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
        
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
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
        
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
            InlineKeyboardButton("السابق ↩️", callback_data="browse_subjects")
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
                InlineKeyboardButton("السابق ↩️", callback_data=f"sub_{AVAILABLE_SUBJECTS.index(current_sub)}")
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
            InlineKeyboardButton("السابق ↩️", callback_data=f"sub_{AVAILABLE_SUBJECTS.index(current_sub)}")
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
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data=f"week_{week_num}"))
        
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
        markup.row(InlineKeyboardButton("السابق ↩️", callback_data="pay_sham_cash"))
        bot.answer_callback_query(call.id)
        send_or_replace_message(chat_id, "يرجى إرسال ملف التحويل أو صورة الإيصال الآن ليتم مراجعته وتفعيل اشتراكك من قِبل الإدارة.", parse_mode="Markdown", reply_markup=markup)

    elif data == "bot_about":
        bot.answer_callback_query(call.id)
        about_text = "«يُقدّم بوت (Kashkoul Jami'i) مواكبة أسبوعية لكل مقرر دراسي تماشيًا مع ما يطرحه أستاذ المادة، وذلك عبر توفير ملفات رقمية مشروحة بشكل دوري ومستمر كل أسبوع؛ لضمان متابعة الطالب وعدم تشتته طوال الفصل الدراسي الأول. إضافةً إلى تقديم خدمات متميزة لكل طالب جامعي طوال مسيرته الأكاديمية.»"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))
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
        markup.row(InlineKeyboardButton("الرجوع إلى القائمة ↩️", callback_data="main_menu"))

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

if __name__ == '__main__':
    print("البوت يعمل الآن بكفاءة عالية ومنظومة تنبيهات دقيقة...")
    bot.infinity_polling()
