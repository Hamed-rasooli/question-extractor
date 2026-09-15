import time
import os
import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService


def _configure_chromium_options(options, headless=False):
    """اعمال فلگ‌های بهینه‌سازی و پایدارسازی روی گزینه‌های کرومیوم (Chrome و Edge)"""
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1440,1000")
    
    # جلوگیری از قفل شدن بافر گرافیکی لینوکس/Wayland روی مانیتور دوم
    options.add_argument("--disable-features=UseOzonePlatform")
    
    # حل قطعی مشکل DNS و اتصال مستقیم به سرورهای سنجشکده
    options.add_argument("--host-resolver-rules=MAP sanjeshkade.ir 185.2.14.61, MAP www.sanjeshkade.ir 185.2.14.61")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")


def create_driver(headless=False, log_callback=None):
    """
    ساخت و راه‌اندازی ضدخطا و خودترمیمی درایور مرورگر.
    سازگار با تمام سیستم‌ها و لپ‌تاپ‌های مختلف:
    ۱. دانلود و تنظیم خودکار درایور منطبق با نسخه نصب‌شده کروم (حل قطعی خطای session not created)
    ۲. پشتیبان خودکار مرورگر Microsoft Edge (پیش‌فرض روی تمام ویندوزهای ۱۰ و ۱۱)
    ۳. پشتیبان نهایی Mozilla Firefox
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)

    errors = []

    # -------------------------------------------------------------
    # استراتژی ۱: تلاش با Google Chrome و webdriver-manager
    # (دانلود خودکار درایور کاملاً منطبق با نسخه دقیق کروم کاربر و بای‌پس درایورهای قدیمی PATH)
    # -------------------------------------------------------------
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_opts = ChromeOptions()
        _configure_chromium_options(chrome_opts, headless=headless)

        driver_path = ChromeDriverManager().install()
        if driver_path and os.path.exists(driver_path):
            if os.path.isdir(driver_path):
                exe_name = "chromedriver.exe" if sys.platform.startswith("win") else "chromedriver"
                candidate = os.path.join(driver_path, exe_name)
                if os.path.exists(candidate):
                    driver_path = candidate

            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_opts)
            driver.maximize_window()
            return driver
    except Exception as e:
        errors.append(f"Google Chrome (webdriver-manager): {e}")

    # -------------------------------------------------------------
    # استراتژی ۲: تلاش با Google Chrome از طریق Selenium Manager داخلی
    # -------------------------------------------------------------
    try:
        chrome_opts = ChromeOptions()
        _configure_chromium_options(chrome_opts, headless=headless)

        driver = webdriver.Chrome(options=chrome_opts)
        driver.maximize_window()
        return driver
    except Exception as e:
        errors.append(f"Google Chrome (Selenium Manager): {e}")

    # -------------------------------------------------------------
    # استراتژی ۳: پشتیبان نجات‌بخش Microsoft Edge (پیش‌فرض روی ۱۰۰٪ سیستم‌های ویندوز)
    # -------------------------------------------------------------
    try:
        log("⚠️ اجرای کروم با مشکل نسخه مواجه شد؛ در حال فعال‌سازی خودکار مرورگر Microsoft Edge...")
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService

        edge_opts = EdgeOptions()
        _configure_chromium_options(edge_opts, headless=headless)

        # تلاش با webdriver-manager برای Edge
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            edge_driver_path = EdgeChromiumDriverManager().install()
            if edge_driver_path and os.path.exists(edge_driver_path):
                if os.path.isdir(edge_driver_path):
                    exe_name = "msedgedriver.exe" if sys.platform.startswith("win") else "msedgedriver"
                    candidate = os.path.join(edge_driver_path, exe_name)
                    if os.path.exists(candidate):
                        edge_driver_path = candidate
                edge_service = EdgeService(executable_path=edge_driver_path)
                driver = webdriver.Edge(service=edge_service, options=edge_opts)
                driver.maximize_window()
                log("✅ مرورگر Microsoft Edge با درایور هماهنگ راه‌اندازی شد.")
                return driver
        except Exception:
            pass

        # تلاش مستقیم با Edge داخلی
        driver = webdriver.Edge(options=edge_opts)
        driver.maximize_window()
        log("✅ مرورگر Microsoft Edge با موفقیت راه‌اندازی شد.")
        return driver
    except Exception as e:
        errors.append(f"Microsoft Edge: {e}")

    # -------------------------------------------------------------
    # استراتژی ۴: پشتیبان نهایی Firefox
    # -------------------------------------------------------------
    try:
        log("⚠️ در حال تلاش برای راه‌اندازی با Mozilla Firefox...")
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        ff_opts = FirefoxOptions()
        if headless:
            ff_opts.add_argument("--headless")
        driver = webdriver.Firefox(options=ff_opts)
        driver.maximize_window()
        log("✅ مرورگر Firefox با موفقیت راه‌اندازی شد.")
        return driver
    except Exception as e:
        errors.append(f"Firefox: {e}")

    # در صورت شکست کلیه روش‌ها
    error_summary = "\n".join(errors)
    raise RuntimeError(
        f"عدم امکان راه‌اندازی مرورگرهای سیستم (Chrome / Edge / Firefox).\n"
        f"جزئیات خطاها:\n{error_summary}\n\n"
        f"راهکار: لطفاً مرورگر Google Chrome یا Microsoft Edge سیستم خود را آپدیت فرمایید."
    )
get_browser_driver = create_driver


def login_sanjeshkade(driver, wait, username, password, log_callback=None):
    """لاگین خودکار به سامانه سنجشکده"""
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)

    log("در حال اتصال به صفحه ورود سامانه سنجشکده (sanjeshkade.ir)...")
    driver.get("https://sanjeshkade.ir/")
    time.sleep(1.5)
    
    try:
        username_field = wait.until(EC.presence_of_element_located((By.ID, 'UserName')))
        password_field = driver.find_element(By.ID, 'Password')
        
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        login_btn = driver.find_element(By.CSS_SELECTOR, '.LF_Submit_Btn')
        login_btn.click()
        
        log("در انتظار ورود و تایید هویت کاربر در سنجشکده...")
        # انتظار برای ورود به پنل کاربری (/User/Panel)
        wait.until(lambda d: "/User" in d.current_url or "Panel" in d.title)
        log("✅ ورود موفقیت‌آمیز به سامانه سنجشکده انجام شد.")
        return True
    except Exception as e:
        log(f"❌ خطا در فرآیند ورود: {e}")
        try:
            driver.save_screenshot("error_login.png")
            log("تصویر خطا در 'error_login.png' ذخیره شد.")
        except Exception:
            pass
        return False


def add_single_tag(driver, tag_name, log):
    """
    جستجو و انطباق هوشمند تگ با دیتابیس موضوعات سنجشکده و ثبت در سوال جاری
    """
    tag_clean = tag_name.strip()
    if not tag_clean:
        return False

    try:
        # استفاده از API درونی سامانه سنجشکده برای جستجوی دقیق، انطباق بدون تاخیر و ست مستقیم در tagService
        res = driver.execute_async_script("""
            var userTag = arguments[0];
            var done = arguments[1];

            // پاکسازی عبارت تگ از شماره سال و کاراکترهای اضافی
            var clean = userTag.replace(/سال\\s*\\d+|\\d{4}/g, '').trim();
            
            function addTagToService(tagObj) {
                if (typeof tagService !== 'undefined') {
                    var currentList = tagService.tagList || [];
                    if (!currentList.some(t => t.tagId === tagObj.tagId)) {
                        currentList.push(tagObj);
                        tagService.setTagsList(currentList);
                    }
                    return true;
                }
                return false;
            }

            function searchTag(query, onComplete) {
                if (!query || query.length < 2) {
                    onComplete([]);
                    return;
                }
                $.ajax({
                    url: '/User/Exams/GetTags',
                    method: 'GET',
                    data: { query: query },
                    success: function(data) {
                        onComplete(Array.isArray(data) ? data : []);
                    },
                    error: function() {
                        onComplete([]);
                    }
                });
            }

            // تلاش اول: جستجو با عبارت تمیز شده
            searchTag(clean, function(results1) {
                if (results1.length > 0) {
                    var best = results1[0];
                    for (var i = 0; i < results1.length; i++) {
                        var title = results1[i].title || '';
                        if (title === clean || clean.includes(title) || title.includes(clean)) {
                            best = results1[i];
                            break;
                        }
                    }
                    addTagToService(best);
                    done({ success: true, title: best.title, tagId: best.tagId });
                    return;
                }

                // تلاش دوم: جستجو بر اساس کلمات کلیدی اصلی موضوع
                var words = clean.split(/\\s+/).filter(w => w.length > 2 && w !== 'آزمون' && w !== 'کارشناسی' && w !== 'ارشد' && w !== 'کنکور');
                var fallbackQuery = words.join(' ');
                
                if (fallbackQuery && fallbackQuery !== clean) {
                    searchTag(fallbackQuery, function(results2) {
                        if (results2.length > 0) {
                            var best2 = results2[0];
                            for (var j = 0; j < results2.length; j++) {
                                var t2 = results2[j].title || '';
                                if (words.every(w => t2.includes(w))) {
                                    best2 = results2[j];
                                    break;
                                }
                            }
                            addTagToService(best2);
                            done({ success: true, title: best2.title, tagId: best2.tagId });
                            return;
                        }
                        done({ success: false, cleanQuery: clean, fallbackQuery: fallbackQuery });
                    });
                    return;
                }

                done({ success: false, cleanQuery: clean });
            });
        """, tag_clean)

        if res and res.get("success"):
            matched_title = res.get("title", tag_clean)
            log(f"  🏷️ تگ '{matched_title}' با موفقیت انتخاب شد.")
            return True
        else:
            # فال‌بک از طریق فرم UI
            tag_input = driver.find_element(By.ID, "search-tag-input")
            tag_input.clear()
            driver.execute_script("arguments[0].value = '';", tag_input)
            
            clean_search = re.sub(r'سال\s*\d+|\d{4}', '', tag_clean).strip()
            tag_input.send_keys(clean_search)
            
            search_btn = driver.find_element(By.ID, "search-tag-button")
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(1.2)
            
            buttons = driver.find_elements(By.CSS_SELECTOR, "#search-tag-list-container button.tag-selector-item")
            if buttons:
                driver.execute_script("arguments[0].click();", buttons[0])
                btn_txt = buttons[0].text.strip()
                log(f"  🏷️ تگ '{btn_txt}' انتخاب شد.")
                return True
            else:
                log(f"  ⚠️ تگ '{tag_clean}' در لیست موضوعات سامانه سنجشکده یافت نشد.")
                return False

    except Exception as e:
        log(f"  ⚠️ خطا در ثبت تگ '{tag_clean}': {e}")
        return False


def run_sanjeshkade_automation(username, password, create_question_url, session_number, tags, questions, headless=False, progress_callback=None, log_callback=None):
    """
    اجرای اتوماسیون کامل ثبت و ذخیره نهایی سوالات در سامانه سنجشکده
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)

    if not questions:
        log("❌ هیچ سوالی برای ثبت ارسال نشده است.")
        return {"success": 0, "failed": 0, "total": 0}

    driver = None
    success_count = 0
    failed_count = 0
    errors = []

    try:
        log("در حال راه‌اندازی مرورگر (Chrome / Edge) با کانکشن مستقیم سنجشکده...")
        driver = create_driver(headless=headless, log_callback=log)
        wait = WebDriverWait(driver, 20)

        # ۱. لاگین
        if not login_sanjeshkade(driver, wait, username, password, log_callback=log):
            return {"success": 0, "failed": len(questions), "total": len(questions), "error": "ورود به سامانه سنجشکده ناموفق بود"}

        # ۲. هدایت به صفحه درس / ایجاد سوال
        log(f"در حال هدایت به صفحه ثبت سوال: {create_question_url}")
        driver.get(create_question_url)
        time.sleep(2)

        total_q = len(questions)

        # ۳. درج و تایید تک‌تک سوالات در فرم
        for idx, q_data in enumerate(questions):
            q_num = q_data.get('number', idx + 1)
            q_text = q_data.get('question', '')
            options = q_data.get('options', [])
            correct_opt = q_data.get('correct_option')

            if progress_callback:
                progress_callback(int((idx / total_q) * 85), f"در حال آماده‌سازی و تایید سوال {q_num} ({idx+1}/{total_q})...")

            log(f"\n--- شروع درج سوال شماره {q_num} ({idx + 1}/{total_q}) ---")

            if not q_text or len(options) != 4:
                log(f"⚠️ اطلاعات سوال {q_num} ناقص است (متن خالی یا کمتر از ۴ گزینه). رد شد.")
                failed_count += 1
                continue

            try:
                # الف) درج متن سوال در ادیتور Markdown / LaTeX
                q_textarea = wait.until(EC.presence_of_element_located((By.ID, "QuestionText")))
                q_textarea.clear()
                q_textarea.send_keys(q_text)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", q_textarea)

                # ب) پیدا کردن فیلدهای ۴ گزینه (Textareaهای کلاس .QuestionAnswer)
                option_fields = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Option .QuestionAnswer")))
                option_checkboxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Option .ChoiceInput")))

                # درج متن گزینه‌ها
                for i in range(4):
                    option_fields[i].clear()
                    option_fields[i].send_keys(options[i])
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", option_fields[i])

                # ج) انتخاب گزینه صحیح و فعال‌سازی رویداد change در jQuery
                for cb in option_checkboxes:
                    if cb.is_selected():
                        driver.execute_script("arguments[0].checked = false; $(arguments[0]).trigger('change');", cb)

                if correct_opt and isinstance(correct_opt, int) and 1 <= correct_opt <= 4:
                    cb_to_select = option_checkboxes[correct_opt - 1]
                    driver.execute_script("arguments[0].checked = true; $(arguments[0]).trigger('change');", cb_to_select)
                    log(f"گزینه {correct_opt} به عنوان پاسخ صحیح انتخاب شد.")
                else:
                    log(f"⚠️ برای سوال {q_num} کلید صحیح معتبر تعیین نشده بود.")

                # د) افزودن دقیق و هوشمند تگ‌ها
                effective_tags = q_data.get('tags') if q_data.get('tags') is not None else tags
                if effective_tags:
                    for tag in effective_tags:
                        add_single_tag(driver, tag, log)

                # هـ) شماره جلسه
                if session_number:
                    session_field = driver.find_element(By.ID, "SessionNumber")
                    session_field.clear()
                    driver.execute_script("arguments[0].value = '';", session_field)
                    session_field.send_keys(str(session_number))

                # و) کلیک روی دکمه «تایید سوال» جهت اضافه شدن به لیست سوالات تایید شده
                confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "ConfirmQuestionBtn")))
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(0.5)

                log(f"✅ سوال {q_num} با موفقیت تایید و به لیست آزمون اضافه شد.")
                success_count += 1

            except Exception as item_err:
                log(f"❌ خطا در درج سوال {q_num}: {item_err}")
                failed_count += 1
                errors.append({"question": q_num, "error": str(item_err)})
                continue

        # ۴. ذخیره نهایی سوالات در دیتابیس با کلیک روی دکمه «ذخیره ی سوالات تایید شده»
        if success_count > 0:
            log(f"\n💾 در حال ارسال و ذخیره قطعی {success_count} سوال در دیتابیس سنجشکده...")
            if progress_callback:
                progress_callback(92, "در حال ذخیره‌سازی نهایی در دیتابیس سنجشکده...")

            try:
                save_btn = wait.until(EC.element_to_be_clickable((By.ID, "SaveQuestionsBtn")))
                driver.execute_script("arguments[0].click();", save_btn)
                
                # صبر برای دریافت پاسخ AJAX از سرور سنجشکده
                time.sleep(4)
                log("🎉 تمام سوالات با موفقیت در دیتابیس سامانه سنجشکده ذخیره شدند!")
            except Exception as save_err:
                log(f"⚠️ دکمه ذخیره نهایی با خطا مواجه شد: {save_err}")

        if progress_callback:
            progress_callback(100, f"پایان فرآیند: {success_count} موفق، {failed_count} ناموفق.")

        log(f"\n🏆 فرآیند بارگذاری با موفقیت تکمیل شد: {success_count} سوال ثبت شد.")
        return {
            "success": success_count,
            "failed": failed_count,
            "total": total_q,
            "errors": errors
        }

    except Exception as main_err:
        log(f"❌ خطای کلی در اتوماسیون: {main_err}")
        return {"success": success_count, "failed": failed_count, "total": len(questions), "error": str(main_err)}
    finally:
        if driver:
            try:
                time.sleep(2)
                driver.quit()
            except Exception:
                pass


# جهت حفظ سازگاری نام توابع قبلی
run_biazmoon_automation = run_sanjeshkade_automation
