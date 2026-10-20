import json
import os
import re
import requests
import smtplib
from datetime import datetime, timedelta
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
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"❌ خطأ تليجرام: {e}")

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
              <div style="background: #fff; padding: 15px; border-radius: 5px;">
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
    except Exception as e:
        print(f"❌ خطأ إرسال الإيميل: {e}")

# ==========================================
# 2. الفحص التفاعلي وسحب المواعيد والغياب
# ==========================================
USERNAME = '4241427'            # كود الطالب
PASSWORD = '30509071200293'     # كلمة المرور

PAGES_TO_MONITOR = {
    '📝 الواجبات والتكليفات (Assignments)': 'https://dulms.deltauniv.edu.eg/StudentAssignment.aspx',
    '⏱️ الكويزات والمواعيد (Quizzes)': 'https://dulms.deltauniv.edu.eg/StudentQuiz.aspx',
    '📌 الغياب والحضور (Lecture Absence)': 'https://dulms.deltauniv.edu.eg/StudentAttendance.aspx',
    '📊 الدرجات وأعمال السنة (Grades)': 'https://dulms.deltauniv.edu.eg/StudentGrades.aspx',
    '📁 المواد وملفات المحاضرات (Files & Materials)': 'https://dulms.deltauniv.edu.eg/StudentCourses.aspx',
    '🔔 الإشعارات واللوحة (Dashboard)': 'https://dulms.deltauniv.edu.eg/StudentDashboard.aspx'
}

def scrape_lms_with_browser():
    scraped_data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🔑 جاري تسجيل الدخول التفاعلي لـ LMS جامعة الدلتا...")
        page.goto("https://dulms.deltauniv.edu.eg/login.aspx", wait_until="networkidle")
        
        page.fill("input[name='txtUsername']", USERNAME)
        page.fill("input[name='txtPassword']", PASSWORD)
        page.click("input[name='btnLogin']")
        page.wait_for_load_state("networkidle")

        for category_name, url in PAGES_TO_MONITOR.items():
            print(f"🌐 فحص وتفاعل مع قسم: {category_name}")
            extracted_items = []
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(2000)

                # التفاعل مع القوائم المنسدلة لاختيار المواد
                selects = page.query_selector_all("select")
                for select in selects:
                    options = select.query_selector_all("option")
                    for opt in options:
                        val = opt.get_attribute("value")
                        if val and val not in ["0", "-1", ""]:
                            try:
                                select.select_option(value=val)
                                page.wait_for_timeout(1000)
                            except:
                                pass

                # قراءة الجداول (الغياب، المواعيد، الدرجات)
                rows = page.query_selector_all("table tr")
                for row in rows:
                    cols = row.query_selector_all("td, th")
                    col_texts = [c.inner_text().strip() for c in cols if c.inner_text().strip()]
                    if col_texts:
                        row_str = " | ".join(col_texts)
                        if len(row_str) > 5 and row_str not in extracted_items:
                            extracted_items.append(row_str)

                # قراءة الكروت
                cards = page.query_selector_all("div.card, div.alert, .quiz-item, .assignment-item")
                for card in cards:
                    txt = card.inner_text().strip()
                    txt = re.sub(r'\s+', ' ', txt)
                    if txt and len(txt) > 8 and txt not in extracted_items:
                        extracted_items.append(txt)

                scraped_data[category_name] = extracted_items
            except Exception as e:
                print(f"❌ خطأ في فحص {category_name}: {e}")
                scraped_data[category_name] = []

        browser.close()
    return scraped_data

# ==========================================
# 3. إرسال التقرير الشامل
# ==========================================
def run_monitor():
    scraped_data = scrape_lms_with_browser()

    for category_name, items in scraped_data.items():
        if items:
            clean_items = [f"• {item}" for item in items[:15]]
            formatted_list = "\n\n".join(clean_items)
            msg = f"📊 [{category_name}]\n\n{formatted_list}"
        else:
            msg = f"📊 [{category_name}]\n\nلا توجد بيانات أو مواعيد مسجلة حالياً بهذا القسم."
        
        send_telegram_msg(msg)
        send_email_msg(category_name, msg)

if __name__ == '__main__':
    try:
        run_monitor()
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الفحص: {e}")
