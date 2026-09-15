#!/usr/bin/env python3
"""
ماژول تولید خودکار و دسته‌جمعی درسنامه (Lesson Plan) در سامانه سنجشکده
پشتیبانی همزمان از:
۱. لاگین خودکار با استفاده از مرورگر نامرئی (Selenium Headless) و استخراج کوکی‌های نشست
۲. دریافت دستی کوکی از کلاینت
۳. استخراج شناسه تمام سوالات از صفحه آزمون با BeautifulSoup و Regex
۴. ارسال درخواست‌های دسته‌جمعی به اندپوینت /User/Lessons/GenerateLessonPlanBatch
"""

import sys
import time
import json
import re
import argparse
import requests
from urllib.parse import urlparse

ENDPOINT_PATH = "/User/Lessons/GenerateLessonPlanBatch"


def normalize_lesson_url(url_or_id: str) -> str:
    """
    تبدیل هر نوع ورودی (آیدی عددی، لینک ایجاد سوال، یا لینک مشاهده سوالات) 
    به لینک استاندارد صفحه سوالات درس در سنجشکده
    """
    s = str(url_or_id).strip()
    match = re.search(r'(\d+)', s)
    if not match:
        raise ValueError("شناسه درس معتبر در ورودی یافت نشد.")
    lesson_id = match.group(1)
    return f"https://sanjeshkade.ir/User/Lessons/Questions/{lesson_id}"


def get_sanjeshkade_cookies(username, password, headless=True, log_callback=None):
    """
    ورود نامرئی (Headless) به سامانه سنجشکده با Selenium و استخراج کوکی‌های احراز هویت
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)

    log("🌐 در حال راه‌اندازی مرورگر نامرئی جهت ورود امن به سنجشکده...")
    from core_automator import create_driver, login_sanjeshkade
    from selenium.webdriver.support.ui import WebDriverWait

    driver = create_driver(headless=headless, log_callback=log_callback)
    wait = WebDriverWait(driver, 25)

    try:
        success = login_sanjeshkade(driver, wait, username, password, log_callback=log_callback)
        if not success:
            raise RuntimeError("ورود به سامانه سنجشکده ناموفق بود. لطفاً نام کاربری و رمز عبور را بررسی فرمایید.")

        log("🔑 ورود موفقیت‌آمیز بود؛ در حال استخراج کوکی‌های نشست (Session Cookies)...")
        selenium_cookies = driver.get_cookies()
        if not selenium_cookies:
            raise RuntimeError("هیچ کوکی معتبری پس از ورود یافت نشد.")

        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in selenium_cookies])
        log(f"✅ تعداد {len(selenium_cookies)} کوکی فعال با موفقیت استخراج شد.")
        return cookie_str
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def build_headers(cookie, referer, origin, ajax=True):
    """ساخت هدرهای استاندارد سازگار با سامانه ASP.NET سنجشکده"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Referer": referer,
        "Cookie": cookie,
    }
    if ajax:
        headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": origin,
        })
    return headers


def fetch_questions_page(session, url, headers):
    """دریافت کد HTML صفحه سوالات درس با سشن و کوکی احراز هویت شده"""
    resp = session.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_question_ids(html_text):
    """
    استخراج شناسه‌های یکتای سوالات از صفحه سوالات سنجشکده
    استفاده از BeautifulSoup به همراه Regex به عنوان پشتیبان بدون خطا
    """
    ids = []
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        for box in soup.select("div.QuestionBox[question-id]"):
            qid = box.get("question-id")
            if qid:
                ids.append(str(qid).strip())
    except Exception:
        pass

    # در صورت عدم استخراج با bs4، استخراج از طریق الگوهای Regex
    if not ids:
        regex_ids = re.findall(r'question-id=["\']?(\d+)["\']?', html_text)
        ids.extend(regex_ids)

    seen = set()
    unique_ids = []
    for qid in ids:
        if qid not in seen:
            seen.add(qid)
            unique_ids.append(qid)
            
    return unique_ids


def generate_lesson_plan(session, endpoint_url, headers, question_id):
    """ارسال درخواست ساخت درسنامه به اندپوینت سنجشکده برای یک شناسه سوال"""
    payload = json.dumps([str(question_id)])
    try:
        resp = session.post(endpoint_url, data=payload, headers=headers, timeout=35)
    except requests.RequestException as e:
        return False, f"خطای شبکه: {e}"

    if resp.status_code == 200:
        return True, resp.text[:200]
    return False, f"HTTP {resp.status_code}: {resp.text[:200]}"


def run_batch_lesson_plan_generation(
    target_url_or_id,
    cookie_str=None,
    username=None,
    password=None,
    delay=1.0,
    progress_callback=None,
    log_callback=None
):
    """
    فرآیند جامع و خودکار تولید درسنامه:
    ۱. لاگین خودکار نامرئی و استخراج کوکی (اگر کوکی داده نشده باشد)
    ۲. پیمایش صفحه سوالات درس و استخراج شناسه تمام سوالات
    ۳. فراخوانی دسته‌جمعی اندپوینت ساخت درسنامه با تاخیر کنترل‌شده و گزارش لحظه‌ای
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)

    # مرحله ۱: اعتبارسنجی و استخراج کوکی
    if not cookie_str or not str(cookie_str).strip():
        if not username or not password:
            raise ValueError("جهت لاگین خودکار، نام کاربری و رمز عبور سنجشکده الزامی است.")
        cookie_str = get_sanjeshkade_cookies(username, password, headless=True, log_callback=log_callback)

    # مرحله ۲: نرمال‌سازی لینک صفحه سوالات
    questions_url = normalize_lesson_url(target_url_or_id)
    parsed = urlparse(questions_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    endpoint_url = origin + ENDPOINT_PATH

    log(f"📄 در حال دریافت فهرست سوالات از: {questions_url}")
    session = requests.Session()
    page_headers = build_headers(cookie_str, questions_url, origin, ajax=False)

    try:
        html_text = fetch_questions_page(session, questions_url, page_headers)
    except Exception as e:
        raise RuntimeError(f"خطا در برقراری ارتباط با صفحه سوالات: {e}")

    question_ids = extract_question_ids(html_text)
    total_q = len(question_ids)
    if total_q == 0:
        raise RuntimeError("هیچ سوالی در این صفحه یافت نشد. لطفاً از درستی لینک یا شناسه درس اطمینان حاصل فرمایید.")

    log(f"🎯 تعداد {total_q} سوال در این درس یافت شد. شروع فرآیند تولید درسنامه...")
    ajax_headers = build_headers(cookie_str, questions_url, origin, ajax=True)

    results = []
    ok_count = 0
    fail_count = 0

    for idx, qid in enumerate(question_ids, start=1):
        success, msg = generate_lesson_plan(session, endpoint_url, ajax_headers, qid)
        if success:
            ok_count += 1
            log(f"[{idx}/{total_q}] سوال #{qid}: ✅ درخواست درسنامه با موفقیت ثبت شد.")
        else:
            fail_count += 1
            log(f"[{idx}/{total_q}] سوال #{qid}: ❌ خطا: {msg}")

        results.append({
            "index": idx,
            "question_id": qid,
            "success": success,
            "message": msg
        })

        if progress_callback:
            progress_callback(idx, total_q, qid, success, msg)

        if idx < total_q and delay > 0:
            time.sleep(delay)

    log(f"🎉 فرآیند تکمیل شد! {ok_count} موفق، {fail_count} خطا از مجموع {total_q} سوال.")
    return {
        "total": total_q,
        "success_count": ok_count,
        "failed_count": fail_count,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(
        description="استخراج سوالات و تولید دسته‌جمعی درسنامه در سنجشکده"
    )
    parser.add_argument("--referer", required=True, help="لینک صفحه سوالات یا شناسه درس (مثلاً 300)")
    parser.add_argument("--cookie", help="کوکی نشست (در صورت عدم ارائه، با یوزر/پس لاگین می‌شود)")
    parser.add_argument("--username", help="نام کاربری سنجشکده")
    parser.add_argument("--password", help="رمز عبور سنجشکده")
    parser.add_argument("--delay", type=float, default=1.0, help="وقفه بین درخواست‌ها به ثانیه (پیش‌فرض 1.0)")
    args = parser.parse_args()

    try:
        res = run_batch_lesson_plan_generation(
            target_url_or_id=args.referer,
            cookie_str=args.cookie,
            username=args.username,
            password=args.password,
            delay=args.delay
        )
        print(f"\nپایان عملیات: {res['success_count']} موفق، {res['failed_count']} خطا.")
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

