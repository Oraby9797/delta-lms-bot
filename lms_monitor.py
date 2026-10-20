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
        'text': text,
        'parse_mode': 'HTML'
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

        # 1. تسجيل الدخول التفاعلي
        print("🔑 جاري تسجيل الدخول تفاعلياً لـ LMS جامعة الدلتا...")
        page.goto("https://dulms.deltauniv.edu.eg/login.aspx", wait_until="networkidle")
        
        page.fill("input[name='txtUsername']", USERNAME)
        page.fill("input[name='txtPassword']", PASSWORD)
        page.click("input[name='btnLogin']")
        
        page.wait_for_load_state("networkidle")

        # 2. التنقل داخل الأقسام وسحب البيانات التفصيلية
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
                    if len(text) > 8 and text not in extracted_items:
                        extracted_items.append(text)

                cards = page.query_selector_all("div.card, div.item, .quiz-item, .assignment-item, .notification-item")
                for card in cards:
                    text = card.inner_text().strip()
                    text = re.sub(r'\s+', ' ', text)
                    if len(text) > 8 and text not in extracted_items:
                        extracted_items.append(text)

                scraped_data[category_name] = extracted_items
            except Exception as e:
                print(f"خطأ في فحص {category_name}: {e}")
                scraped_data[category_name] = []

        browser.close()
    return scraped_data

# ==========================================
# 3. المقارنة وإرسال التقارير المنظمة
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
    previous_state = load_state()
    scraped_data = scrape_lms_with_browser()
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    last_report_date = previous_state.get('_last_report_date', '')
    should_send_daily_report = (last_report_date != today_str) or (len(previous_state) == 0)

    current_state = {}

    for category_name, items in scraped_data.items():
        current_state[category_name] = items
        
        prev_items = set(previous_state.get(category_name, []))
        curr_items = set(items)
        new_items = curr_items - prev_items

        if should_send_daily_report:
            if items:
                formatted_list = "\n".join([f"• {item}" for item in items[:8]])
                msg = f"<b>[التقرير الشامل - LMS جامعة الدلتا]</b>\n\n<b>{category_name}</b>\n\n{formatted_list}"
            else:
                msg = f"<b>[التقرير الشامل - LMS جامعة الدلتا]</b>\n\n<b>{category_name}</b>\n\nلا توجد عناصر مسجلة حالياً."
            
            send_telegram_msg(msg)
            send_email_msg(category_name, msg)
            
        elif new_items:
            for new_item in new_items:
                msg = f"🚨 <b>[تحديث جديد عاجل]</b>\n\n<b>القسم:</b> {category_name}\n\n<b>التفاصيل:</b>\n{new_item}"
                send_telegram_msg(msg)
                send_email_msg(category_name, msg)

    current_state['_last_report_date'] = today_str
    save_state(current_state)

if __name__ == '__main__':
    try:
        run_monitor()
    except Exception as e:
        print(f"حدث خطأ أثناء الفحص: {e}")
