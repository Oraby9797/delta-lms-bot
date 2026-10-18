import json
import os
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. إعدادات بوت التليجرام
# ==========================================
BOT_TOKEN = '8530974763:AAFNe--rkf-ocpitUqSV2z4tTWdoln_GgII'
CHAT_ID = '8894056949'

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': f"🚨 [تحديث LMS جامعة الدلتا]\n\n{text}"
    }
    try:
        requests.post(url, data=payload)
        print("تم إرسال التنبيه للتليجرام بنجاح!")
    except Exception as e:
        print(f"خطأ في إرسال التليجرام: {e}")

# ==========================================
# 2. بيانات الدخول لجامعة الدلتا
# ==========================================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

LOGIN_URL = 'https://dulms.deltauniv.edu.eg/login.aspx'
USERNAME = '4241427'            # كود الطالب
PASSWORD = '30509071200293'     # كلمة المرور

# روابط الأقسام الشاملة (غياب، واجبات، إشعارات، وملفات المواد)
PAGES_TO_MONITOR = {
    'الغياب والحضور (Lecture & Section Absence)': 'https://dulms.deltauniv.edu.eg/StudentAttendance.aspx',
    'الواجبات والكويزات (Assignments & Quizzes)': 'https://dulms.deltauniv.edu.eg/StudentQuiz.aspx',
    'الإشعارات واللوحة الرئيسية (Dashboard)': 'https://dulms.deltauniv.edu.eg/StudentDashboard.aspx',
    'المواد وملفات المحاضرات (Files & Materials)': 'https://dulms.deltauniv.edu.eg/StudentCourses.aspx'
}

def login():
    res = session.get(LOGIN_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    viewstate = soup.find('input', id='__VIEWSTATE')
    viewstate_val = viewstate['value'] if viewstate else ''
    
    eventvalidation = soup.find('input', id='__EVENTVALIDATION')
    eventvalidation_val = eventvalidation['value'] if eventvalidation else ''

    login_payload = {
        '__VIEWSTATE': viewstate_val,
        '__EVENTVALIDATION': eventvalidation_val,
        'txtUsername': USERNAME,
        'txtPassword': PASSWORD,
        'btnLogin': 'Login'
    }
    session.post(LOGIN_URL, data=login_payload)

def fetch_page_items(url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    extracted_texts = []
    
    # فحص الجداول والعناصر والروابط والملفات داخل الصفحة
    container = soup.find('div', class_='page-contect') or soup.find('section', id='user-control') or soup.find('form')
    if container:
        for item in container.find_all(['div', 'tr', 'li', 'a', 'td']):
            text = item.text.strip()
            if text and len(text) > 4 and text not in extracted_texts:
                extracted_texts.append(text)
                
    return extracted_texts

# ==========================================
# 3. دالة الفحص والمقارنة
# ==========================================
STATE_FILE = 'lms_state.json'

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def run_monitor():
    print("🔍 جاري فحص LMS جامعة الدلتا...")
    login()
    previous_state = load_state()
    current_state = {}

    for category_name, page_url in PAGES_TO_MONITOR.items():
        items = fetch_page_items(page_url)
        current_state[category_name] = items
        
        prev_items = set(previous_state.get(category_name, []))
        curr_items = set(items)
        new_items = curr_items - prev_items
        
        # إرسال تنبيه فقط في حالة وجود عنصر جديد أو غياب أو ملف مرفوع جديد
        if new_items and previous_state:
            for new_item in new_items:
                msg = f"📌 القسم: {category_name}\n\n📝 العنصر / الملف الجديد:\n{new_item}"
                send_telegram_msg(msg)

    save_state(current_state)

if __name__ == '__main__':
    try:
        # رسالة تأكيد فورية بتعديل الكود وتشغيله بنجاح
        send_telegram_msg("✅ تم تحديث كود السكربت ونظام الفحص (شامل الغياب، الواجبات، والملفات) يعمل بنجاح الآن!")
        run_monitor()
    except Exception as e:
        print(f"حدث خطأ أثناء الفحص: {e}")
