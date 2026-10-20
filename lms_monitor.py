import json
import os
import re
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from playwright.sync_api import sync_playwright

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
        'text': text
    }
    try:
        res = requests.post(url, data=payload)
        print(f"نتيجة إرسال التليجرام: {res.status_code}")
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
# 2. الفحص التفاعلي باستخدام Playwright
# ==========================================
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

def scrape_lms_with_browser():
    scraped_data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🔑 جاري تسجيل الدخول تفاعلياً لـ LMS جامعة الدلتا...")
        page.goto("https://dulms.deltauniv.edu.eg/login.aspx", wait_until="networkidle")
        
        page.fill("input[name='txtUsername']", USERNAME)
        page.fill("input[name='txtPassword']", PASSWORD)
        page.click("input[name='btnLogin']")
        
        page.wait_for_load_state("networkidle")

        for category_name, url in PAGES_TO_MONITOR.items():
            print(f"🌐 فحص قسم: {category_name}")
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(2000)

                extracted_items = []
                
                rows = page.query_selector_all("table tr")
                for row in rows:
                    text = row.inner_text().strip()
                    text = re.sub(r'\t+', ' | ', text)
                    text = re.sub(r'\n+', ' | ', text)
                    if len(text) > 5 and text not in extracted_items:
                        extracted_items.append(text)

                cards = page.query_selector_all("div, li, article")
                for card in cards:
                    text = card.inner_text().strip()
                    text = re.sub(r'\s+', ' ', text)
                    if len(text) > 10 and text not in extracted_items and "Logout" not in text:
                        # إضافة نصوص الكروت المفيدة فقط
                        if any(k in text.lower() for k in ['quiz', 'assignment', 'absence', 'grade', 'lecture', 'section', 'واجب', 'غياب', 'كويز', 'درجات']):
                            extracted_items.append(text)

                scraped_data[category_name] = extracted_items
            except Exception as e:
                print(f"خطأ في فحص {category_name}: {e}")
                scraped_data[category_name] = []

        browser.close()
    return scraped_data

# ==========================================
# 3. الفحص والتقرير المنظم المباشر
# ==========================================
STATE_FILE = 'lms_state.json'

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def run_monitor():
    previous_state = load_state()
    scraped_data = scrape_lms_with_browser()
    current_state = {}

    for category_name, items in scraped_data.items():
        current_state[category_name] = items
        
        # إرسال تقرير لكل قسم بشكل منفصل
        if items:
            # تنظيف وقص النص ليكون مناسباً لرسالة التليجرام
            clean_items = [f"• {item[:200]}" for item in items[:8]]
            formatted_list = "\n\n".join(clean_items)
            msg = f"📊 [تقرير {category_name}]\n\n{formatted_list}"
        else:
            msg = f"📊 [تقرير {category_name}]\n\nلا توجد عناصر جديدة أو مواعيد مسجلة حالياً."
        
        send_telegram_msg(msg)
        send_email_msg(category_name, msg)

    save_state(current_state)

if __name__ == '__main__':
    try:
        run_monitor()
    except Exception as e:
        print(f"حدث خطأ أثناء الفحص: {e}")
