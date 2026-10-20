import json
import os
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from bs4 import BeautifulSoup

# ==========================================
# 1. إعدادات التليجرام والجيميل
# ==========================================
BOT_TOKEN = '8530974763:AAFNe--rkf-ocpitUqSV2z4tTWdoln_GgII'
CHAT_ID = '8894056949'

SENDER_EMAIL = 'oraby9797@gmail.com'       
SENDER_PASSWORD = 'txdseoecaarvkgmc'     
RECEIVER_EMAIL = 'oraby9797@gmail.com'     

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload)
        print("تم إرسال التنبيه للتليجرام بنجاح!")
    except Exception as e:
        print(f"خطأ تليجرام: {e}")

def send_email_msg(subject, body):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Delta LMS Monitor <{SENDER_EMAIL}>"
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚨 [LMS جامعة الدلتا] {subject}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #f4f6f9; padding: 20px; border-radius: 8px;">
              <h2 style="color: #0056b3;">🚨 إشعار LMS جامعة الدلتا</h2>
              <p><b>القسم:</b> {subject}</p>
              <hr style="border: 0; border-top: 1px solid #ccc;">
              <div style="background: #fff; padding: 15px; border-radius: 5px; border-right: 4px solid #0056b3;">
                <pre style="font-family: inherit; white-space: pre-wrap;">{body}</pre>
              </div>
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        print("تم إرسال الإيميل بنجاح!")
    except Exception as e:
        print(f"خطأ إرسال الإيميل: {e}")

# ==========================================
# 2. بيانات الدخول لجامعة الدلتا والأقسام
# ==========================================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

LOGIN_URL = 'https://dulms.deltauniv.edu.eg/login.aspx'
USERNAME = '4241427'            # كود الطالب
PASSWORD = '30509071200293'     # كلمة المرور

PAGES_TO_MONITOR = {
    '📝 الواجبات والتكليفات (Assignments)': 'https://dulms.deltauniv.edu.eg/StudentAssignment.aspx',
    '⏱️ الكويزات والمواعيد (Quizzes)': 'https://dulms.deltauniv.edu.eg/StudentQuiz.aspx',
    '📌 الغياب والحضور (Lecture Absence)': 'https://dulms.deltauniv.edu.eg/StudentAttendance.aspx',
    '📊 الدرجات وأعمال السنة والنتائج (Grades)': 'https://dulms.deltauniv.edu.eg/StudentGrades.aspx',
    '📁 المواد وملفات المحاضرات (Files & Materials)': 'https://dulms.deltauniv.edu.eg/StudentCourses.aspx',
    '🔔 الإشعارات العامة واللوحة (Dashboard)': 'https://dulms.deltauniv.edu.eg/StudentDashboard.aspx'
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
    extracted_items = []
    
    # فحص كافة الجداول والتفاصيل
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = [col.text.strip() for col in row.find_all(['td', 'th']) if col.text.strip()]
            if cols:
                row_str = " | ".join(cols)
                if len(row_str) > 5 and row_str not in extracted_items:
                    extracted_items.append(row_str)

    # فحص البطاقات والقوائم
    cards = soup.find_all(['div', 'li', 'article', 'tr'], class_=re.compile(r'(card|item|quiz|assignment|absent|grade|notice|notification)', re.I))
    for card in cards:
        txt = card.text.strip()
        txt = re.sub(r'\s+', ' ', txt)
        if txt and len(txt) > 8 and txt not in extracted_items:
            extracted_items.append(txt)

    return extracted_items

# ==========================================
# 3. الفحص وإرسال الرسائل المنفصلة
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
    print("🔍 جاري فحص LMS جامعة الدلتا واستخراج البيانات المنظمة...")
    login()
    previous_state = load_state()
    current_state = {}
    
    is_first_run = len(previous_state) == 0

    for category_name, page_url in PAGES_TO_MONITOR.items():
        items = fetch_page_items(page_url)
        current_state[category_name] = items
        
        prev_items = set(previous_state.get(category_name, []))
        curr_items = set(items)
        
        new_items = curr_items - prev_items
        
        if is_first_run:
            # إرسال رسالة مستقلة ومنظمة لكل قسم
            if items:
                formatted_list = "\n".join([f"• {item}" for item in items[:6]])
                msg = f"<b>{category_name}</b>\n\n{formatted_list}"
            else:
                msg = f"<b>{category_name}</b>\n\nلا توجد عناصر مسجلة حالياً."
            
            send_telegram_msg(msg)
            send_email_msg(category_name, msg)
        else:
            # التنبيهات الجديدة المنفصلة
            if new_items:
                for new_item in new_items:
                    msg = f"🚨 <b>[تحديث جديد]</b>\n\n<b>القسم:</b> {category_name}\n\n<b>التفاصيل:</b>\n{new_item}"
                    send_telegram_msg(msg)
                    send_email_msg(category_name, msg)

    save_state(current_state)

if __name__ == '__main__':
    try:
        run_monitor()
    except Exception as e:
        print(f"حدث خطأ أثناء الفحص: {e}")
