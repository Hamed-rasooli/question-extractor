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


def extract_questions_data(html_text):
    """
    استخراج شناسه‌های یکتا و وضعیت درسنامه هر سوال از صفحه سوالات سنجشکده
    خروجی: لیستی از دیکشنری‌ها با فیلدهای question_id و has_lesson_plan
    """
    items = []
    seen = set()
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        for box in soup.select("div.QuestionBox[question-id]"):
            qid = box.get("question-id")
            if not qid:
                continue
            qid = str(qid).strip()
            if qid in seen:
                continue
            seen.add(qid)

            # بررسی المان وضعیت درسنامه در صفحه سنجشکده
            status_el = box.select_one(".HasLessonPlanStatus")
            preview_btn = box.select_one(".PreviewLessonPlanFromGridBtn")

            has_lp = False
            if status_el:
                classes = status_el.get("class", [])
                text = status_el.get_text(strip=True)
                # در سنجشکده اگر درسنامه داشته باشد: class="text-success" و متن "درسنامه: دارد" است
                if "text-success" in classes or ("دارد" in text and "ندارد" not in text):
                    has_lp = True

            # دکمه پیش‌نمایش در صورت نداشتن درسنامه کلاس disabled و aria-disabled="true" دارد
            if not has_lp and preview_btn:
                btn_classes = preview_btn.get("class", [])
                if "disabled" not in btn_classes and preview_btn.get("aria-disabled") != "true":
                    has_lp = True

            items.append({
                "question_id": qid,
                "has_lesson_plan": has_lp
            })
    except Exception:
        pass

    # پشتیبان Regex در صورت خطای احتمالی در تجزیه HTML
    if not items:
        regex_ids = re.findall(r'question-id=["\']?([a-f0-9\-]+|\d+)["\']?', html_text)
        for qid in regex_ids:
            if qid not in seen:
                seen.add(qid)
                items.append({
                    "question_id": qid,
                    "has_lesson_plan": False
                })

    return items


def extract_question_ids(html_text):
    """
    استخراج شناسه‌های یکتای سوالات از صفحه سوالات سنجشکده (جهت سازگاری با سایر ماژول‌ها)
    """
    return [q["question_id"] for q in extract_questions_data(html_text)]


def generate_lesson_plan(session, endpoint_url, headers, question_id, timeout=60, max_retries=2, retry_delay=2.0):
    """
    ارسال درخواست ساخت درسنامه به اندپوینت سنجشکده برای یک شناسه سوال
    همراه با مکانیزم تلاش مجدد خودکار (Auto-Retry) برای خطاهای تایم‌اوت و نوسانات شبکه
    """
    payload = json.dumps([str(question_id)])
    last_error = ""

    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(endpoint_url, data=payload, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return True, resp.text[:200]

            # خطاهای گذرای سرور سنجشکده (502/503/504)
            if resp.status_code in (502, 503, 504) and attempt < max_retries:
                time.sleep(retry_delay)
                continue

            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

        except requests.Timeout as e:
            last_error = f"تایم‌اوت شبکه ({timeout} ثانیه): {e}"
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
        except requests.RequestException as e:
            last_error = f"خطای شبکه: {e}"
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue

    return False, last_error


def run_batch_lesson_plan_generation(
    target_url_or_id,
    cookie_str=None,
    username=None,
    password=None,
    delay=1.0,
    only_missing=True,
    timeout=60,
    max_retries=2,
    progress_callback=None,
    log_callback=None
):
    """
    فرآیند جامع و خودکار تولید درسنامه:
    ۱. لاگین خودکار نامرئی و استخراج کوکی (اگر کوکی داده نشده باشد)
    ۲. پیمایش صفحه سوالات درس و استخراج شناسه تمام سوالات به همراه وضعیت درسنامه
    ۳. فیلتر هوشمند سوالاتی که از قبل درسنامه دارند (جهت جلوگیری از دوباره‌کاری و خطای سرور)
    ۴. فراخوانی دسته‌جمعی اندپوینت ساخت درسنامه با تلاش مجدد هوشمند و گزارش لحظه‌ای
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

    questions_data = extract_questions_data(html_text)
    total_q = len(questions_data)
    if total_q == 0:
        raise RuntimeError("هیچ سوالی در این صفحه یافت نشد. لطفاً از درستی لینک یا شناسه درس اطمینان حاصل فرمایید.")

    already_done = [q for q in questions_data if q["has_lesson_plan"]]
    missing_lp = [q for q in questions_data if not q["has_lesson_plan"]]

    if only_missing:
        target_questions = missing_lp
    else:
        target_questions = questions_data

    target_total = len(target_questions)

    log(f"📊 وضعیت سوالات درس: مجموعاً {total_q} سوال یافت شد.")
    log(f"✅ سوالات دارای درسنامه قبلی: {len(already_done)} سوال")
    log(f"⚡ سوالات نیازمند تولید درسنامه: {len(missing_lp)} سوال")

    if only_missing and target_total == 0:
        log("🎉 تمامی سوالات این درس از قبل دارای درسنامه هستند! نیازی به ثبت درخواست مجدد نیست.")
        return {
            "total": total_q,
            "already_completed": len(already_done),
            "targeted": 0,
            "success_count": 0,
            "failed_count": 0,
            "results": []
        }

    log(f"🎯 شروع فرآیند تولید درسنامه برای {target_total} سوال...")
    ajax_headers = build_headers(cookie_str, questions_url, origin, ajax=True)

    results = []
    ok_count = 0
    fail_count = 0

    for idx, item in enumerate(target_questions, start=1):
        qid = item["question_id"]
        success, msg = generate_lesson_plan(
            session=session,
            endpoint_url=endpoint_url,
            headers=ajax_headers,
            question_id=qid,
            timeout=timeout,
            max_retries=max_retries
        )

        if success:
            ok_count += 1
            log(f"[{idx}/{target_total}] سوال #{qid}: ✅ درخواست درسنامه با موفقیت ثبت شد.")
        else:
            fail_count += 1
            log(f"[{idx}/{target_total}] سوال #{qid}: ❌ خطا: {msg}")

        results.append({
            "index": idx,
            "question_id": qid,
            "success": success,
            "message": msg
        })

        if progress_callback:
            progress_callback(idx, target_total, qid, success, msg)

        if idx < target_total and delay > 0:
            time.sleep(delay)

    log(f"🎉 فرآیند تکمیل شد! {ok_count} موفق، {fail_count} خطا از مجموع {target_total} سوال نیازمند پردازش.")
    return {
        "total": total_q,
        "already_completed": len(already_done),
        "targeted": target_total,
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
    parser.add_argument("--force", action="store_true", help="تولید مجدد حتی برای سوالاتی که قبلاً درسنامه دارند")
    parser.add_argument("--timeout", type=int, default=60, help="حداکثر زمان انتظار برای پاسخ هر سوال به ثانیه (پیش‌فرض 60)")
    parser.add_argument("--max-retries", type=int, default=2, help="تعداد دفعات تلاش مجدد در صورت خطای شبکه (پیش‌فرض 2)")
    args = parser.parse_args()

    try:
        res = run_batch_lesson_plan_generation(
            target_url_or_id=args.referer,
            cookie_str=args.cookie,
            username=args.username,
            password=args.password,
            delay=args.delay,
            only_missing=not args.force,
            timeout=args.timeout,
            max_retries=args.max_retries
        )
        print(f"\nپایان عملیات: {res['success_count']} موفق، {res['failed_count']} خطا (از {res['targeted']} سوال پردازش شده).")
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


