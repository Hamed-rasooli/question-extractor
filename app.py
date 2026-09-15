import json
import os
import re
import streamlit as st
from core_extractor import (
    convert_file_to_images,
    configure_gemini,
    extract_questions_from_images,
    extract_answer_key_dict
)
from core_automator import run_sanjeshkade_automation
from sanjesh import run_batch_lesson_plan_generation, normalize_lesson_url


# مسیرهای فایل‌های ذخیره‌سازی محلی (Auto-Persistence)
CONFIG_FILE = "config_local.json"
CACHE_FILE = "extracted_questions.json"


def load_local_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_local_config(conf):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_cached_questions():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_cached_questions(questions_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(questions_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="سامانه استخراج و ثبت آزمون سنجشکده",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# بازیابی تنظیمات ذخیره‌شده محلی
saved_config = load_local_config()

# مقداردهی اولیه سشن استیت با حافظه دیسک
if "questions" not in st.session_state or not st.session_state["questions"]:
    cached = load_cached_questions()
    if cached:
        st.session_state["questions"] = cached
    else:
        st.session_state["questions"] = []

if "api_key" not in st.session_state:
    st.session_state["api_key"] = saved_config.get("api_key", "")

# استایل‌های جامع، تمام‌صفحه و بهینه‌سازی جدول (Full Width + Custom Table)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');
    
    /* ۱. راست‌چین سراسری و تم تیره مدرن */
    html, body, .stApp, [data-testid="stAppViewContainer"], .main, div[data-testid="stAppViewBlockContainer"] {
        direction: rtl !important;
        text-align: right !important;
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif !important;
    }
    
    p, label, h1, h2, h3, h4, h5, h6, input, textarea, select, .stMarkdown, div[data-testid="stMarkdownContainer"] {
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* ۲. استفاده حداکثری از عرض صفحه (تمام‌صفحه) */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 98% !important;
        margin: 0 auto !important;
    }
    
    /* ۳. ستون‌ها و چیدمان افقی */
    div[data-testid="stHorizontalBlock"] {
        direction: rtl !important;
        gap: 1.5rem !important;
    }
    div[data-testid="column"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* ۴. استایل اختصاصی جدول و ویرایشگر داده */
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        width: 100% !important;
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
        background-color: #111827 !important;
    }
    
    /* ۵. عنوان و لیبل تمام فرم‌ها */
    div[data-testid="stWidgetLabel"], 
    label[data-testid="stWidgetLabel"], 
    .stWidgetLabel p, 
    [data-testid="stWidgetLabel"] label,
    div[data-testid="stWidgetLabel"] > div {
        direction: rtl !important;
        text-align: right !important;
        justify-content: flex-start !important;
        display: flex !important;
        font-weight: 700 !important;
        font-size: 0.94rem !important;
        color: #e5e7eb !important;
        margin-bottom: 6px !important;
    }
    
    /* ۶. رادیوباتن‌ها */
    div[data-testid="stRadio"] > div {
        direction: rtl !important;
        text-align: right !important;
        align-items: flex-start !important;
    }
    div[data-testid="stRadio"] label {
        direction: rtl !important;
        text-align: right !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        cursor: pointer !important;
        padding: 6px 0 !important;
    }
    div[data-testid="stRadio"] label > div:first-child {
        margin-left: 10px !important;
        margin-right: 0 !important;
    }
    div[data-testid="stRadio"] label > div:last-child {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* ۷. چک‌باکس‌ها */
    div[data-testid="stCheckbox"] label {
        direction: rtl !important;
        text-align: right !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        cursor: pointer !important;
    }
    div[data-testid="stCheckbox"] label > span:first-child {
        margin-left: 10px !important;
        margin-right: 0 !important;
    }
    div[data-testid="stCheckbox"] label > div[data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* ۸. فیلدهای ورودی */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        direction: rtl !important;
        text-align: right !important;
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
        color: #f9fafb !important;
        padding: 10px 14px !important;
        font-size: 0.95rem !important;
    }
    
    /* ۹. آیکون‌ها */
    [data-testid="stIconMaterial"], 
    .material-symbols-rounded, 
    .material-icons, 
    [class*="material-symbols"],
    button[data-testid="stSidebarCollapseButton"] *,
    div[data-baseweb="input"] button *,
    span[data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
        direction: ltr !important;
        display: inline-block !important;
    }
    
    /* ۱۰. تب‌ها */
    div[data-baseweb="tab-list"] {
        direction: rtl !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        border-bottom: 2px solid #1f2937 !important;
        margin-bottom: 24px !important;
    }
    button[data-baseweb="tab"] {
        direction: rtl !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        background-color: #111827 !important;
        border: 1px solid #1f2937 !important;
        color: #9ca3af !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #2563eb !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
    }
    
    /* ۱۱. سایدبار دائمی و حذف کامل دکمه جمع‌کردن */
    [data-testid="stSidebar"] {
        min-width: 340px !important;
        max-width: 360px !important;
        width: 350px !important;
        background-color: #111827 !important;
        border-left: 1px solid #1f2937 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    [data-testid="stSidebarContent"] {
        padding: 1.4rem 1.2rem !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* حذف و مخفی‌سازی کامل دکمه فلش جمع‌کردن سایدبار */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="stSidebarCollapsedControl"],
    button[data-testid="stSidebarCollapseButton"],
    div[data-testid="stSidebarCollapseButton"],
    div[data-testid="stSidebarCollapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
    }
    
    .section-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    
    .inspector-card {
        background: #162032;
        border: 1px solid #2563eb;
        border-radius: 16px;
        padding: 22px 24px;
        margin-top: 25px;
        margin-bottom: 20px;
    }
    
    .github-box {
        margin-top: 50px;
        padding: 28px 24px;
        border-radius: 16px;
        background: #111827;
        border: 1px solid #1f2937;
        text-align: center;
    }
    .github-link {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-top: 14px;
        padding: 11px 26px;
        background: #238636;
        color: #ffffff !important;
        text-decoration: none !important;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# --- سایدبار: تنظیمات و دسترسی‌ها ---
with st.sidebar:
    st.markdown("### ⚙️ تنظیمات و دسترسی‌ها")
    
    st.markdown("#### 🔑 اتصال به Google Gemini")
    api_key_input = st.text_input(
        "کلید Gemini API:",
        type="password",
        value=st.session_state.get("api_key", ""),
        help="کلید دریافتی از پنل Google AI Studio (aistudio.google.com)"
    )
    if api_key_input != st.session_state.get("api_key"):
        st.session_state["api_key"] = api_key_input
        saved_config["api_key"] = api_key_input
        save_local_config(saved_config)
        
    use_proxy = st.checkbox("فعال‌سازی پروکسی (v2ray / Socks5)", value=saved_config.get("use_proxy", False))
    proxy_url = saved_config.get("proxy_url", "http://127.0.0.1:10809")
    if use_proxy:
        proxy_url = st.text_input("آدرس پروکسی:", value=proxy_url, help="پورت http محلی کلاینت فیلترشکن")
        st.caption("💡 فقط درخواست‌های Gemini از این پروکسی رد می‌شوند و سایت سنجشکده با IP مستقیم ایران باز خواهد شد.")
        
    st.markdown("---")
    st.markdown("#### 🌐 حساب کاربری سنجشکده (sanjeshkade.ir)")
    sanjeshkade_user = st.text_input("نام کاربری / ایمیل سنجشکده:", value=saved_config.get("sanjeshkade_user", ""))
    sanjeshkade_pass = st.text_input("رمز عبور:", type="password", value=saved_config.get("sanjeshkade_pass", ""))
    sanjeshkade_url = st.text_input("لینک صفحه ایجاد سوال:", value=saved_config.get("sanjeshkade_url", "https://sanjeshkade.ir/User/Lessons/CreateQuestion/211"))
    sanjeshkade_session = st.text_input("شماره جلسه / سال:", value=saved_config.get("sanjeshkade_session", "1403"))
    sanjeshkade_tags = st.text_area(
        "تگ‌های پیش‌فرض:",
        value=saved_config.get("sanjeshkade_tags", "آزمون کارشناسی ارشد انگل شناسی دامپزشکی"),
        height=75,
        help="تگ‌ها را با کاما (,)، ویرگول فارسی (،) یا رفتن به خط بعد از هم جدا کنید."
    )
    
    headless_mode = st.checkbox("اجرای مرورگر در پس‌زمینه (Headless)", value=saved_config.get("headless_mode", False))

    current_sidebar_config = {
        "api_key": st.session_state.get("api_key", ""),
        "use_proxy": use_proxy,
        "proxy_url": proxy_url,
        "sanjeshkade_user": sanjeshkade_user,
        "sanjeshkade_pass": sanjeshkade_pass,
        "sanjeshkade_url": sanjeshkade_url,
        "sanjeshkade_session": sanjeshkade_session,
        "sanjeshkade_tags": sanjeshkade_tags,
        "headless_mode": headless_mode
    }
    if current_sidebar_config != saved_config:
        save_local_config(current_sidebar_config)

# --- کارت هدر اصلی ---
st.markdown("""
<div class="section-card" style="border-right: 4px solid #3b82f6;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <h2 style="margin: 0; color: #60a5fa; font-weight: 900; font-size: 1.55rem;">📝 سامانه استخراج و ثبت خودکار آزمون سنجشکده</h2>
        <span style="background: rgba(59, 130, 246, 0.15); color: #93c5fd; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem; font-weight: 700;">نسخه ۲.۰ سنجشکده</span>
    </div>
    <p style="margin: 10px 0 0 0; color: #9ca3af; font-size: 0.94rem; line-height: 1.8;">
        استخراج ۱۰۰٪ خودکار سوالات چهارگزینه‌ای از دفترچه آزمون PDF با هوش مصنوعی و انطباق کلید پاسخنامه سازمان سنجش با ثبت سیستمی در <b>سامانه سنجشکده (sanjeshkade.ir)</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# تب‌های اصلی
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 ۱. استخراج هوشمند از PDF",
    "📋 ۲. مشاهده و ویرایش سوالات",
    "🌐 ۳. بارگذاری خودکار در سنجشکده",
    "📚 ۴. ساخت خودکار درسنامه"
])

# --- تب ۱: استخراج ---
with tab1:
    col_pdf_q, col_pdf_key = st.columns([1, 1], gap="medium")
    
    with col_pdf_q:
        st.markdown("##### 📁 ۱. فایل دفترچه سوالات (PDF)")
        uploaded_pdf = st.file_uploader(
            "فایل PDF سوالات را انتخاب فرمایید:",
            type=["pdf"],
            help="دفترچه حاوی سوالات و گزینه‌ها",
            key="uploader_questions"
        )
        
    with col_pdf_key:
        st.markdown("##### 📄 ۲. فایل پاسخنامه / کلید آزمون (اختیاری)")
        uploaded_key_file = st.file_uploader(
            "فایل مجزای کلید پاسخنامه را انتخاب کنید (PDF یا عکس):",
            type=["pdf", "png", "jpg", "jpeg"],
            help="اگر کلید آزمون در یک فایل PDF مجزا یا عکس جدول کلید است، آن را اینجا قرار دهید.",
            key="uploader_key"
        )

    # امکان بارگذاری سریع فایل JSON قبلی مستقیم در تب ۱
    with st.expander("📂 یا بارگذاری مستقیم فایل JSON استخراج‌شده قبلی (بدون نیاز به پردازش مجدد PDF)"):
        uploaded_json_tab1 = st.file_uploader(
            "انتخاب فایل JSON سوالات:",
            type=["json"],
            key="uploader_json_tab1"
        )
        if uploaded_json_tab1 is not None:
            file_sig_t1 = f"{uploaded_json_tab1.name}_{uploaded_json_tab1.size}"
            if st.session_state.get("last_imported_file_sig") != file_sig_t1:
                try:
                    uploaded_json_tab1.seek(0)
                    loaded_data_t1 = json.load(uploaded_json_tab1)
                    if isinstance(loaded_data_t1, list) and len(loaded_data_t1) > 0:
                        st.session_state["questions"] = loaded_data_t1
                        st.session_state["last_imported_file_sig"] = file_sig_t1
                        save_cached_questions(loaded_data_t1)
                        st.toast(f"✅ تعداد {len(loaded_data_t1)} سوال با موفقیت بارگذاری شد.", icon="🎉")
                        st.rerun()
                    else:
                        st.error("❌ فایل JSON فاقد ساختار معتبر است.")
                except Exception as err:
                    st.error(f"❌ خطا در بارگذاری فایل JSON: {err}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # بخش ۲: انتخاب مدل هوش مصنوعی
    st.markdown("##### 🤖 ۳. انتخاب مدل هوش مصنوعی Gemini")
    model_choice = st.radio(
        "مدل هوش مصنوعی را انتخاب کنید:",
        [
            "gemini-2.5-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest"
        ],
        format_func=lambda x: {
            "gemini-2.5-flash": "🌟 Gemini 2.5 Flash (پیشنهادی و تست‌شده - سازگاری قطعی با سوالات آزمون و پاسخنامه)",
            "gemini-3.6-flash": "⚡ Gemini 3.6 Flash (نسل ۳.۶ - بهینه‌شده با سرعت بالا بدون تاخیر تفکر)",
            "gemini-3.5-flash-lite": "🚀 Gemini 3.5 Flash-Lite (فوق‌العاده سریع - سقف درخواست ۲ برابر)",
            "gemini-flash-lite-latest": "🔄 Gemini Flash-Lite Latest (آخرین نسخه پایدار لایت)"
        }.get(x, x),
        help="مدل‌های کاملاً فعال، تست‌شده و سازگار با اکانت‌های رایگان Google AI Studio."
    )

    with st.expander("📊 مشاهده جزئیات سهمیه و محدودیت‌ها (Rate Limits) مدل‌ها"):
        st.markdown("""
| نام مدل | سقف در دقیقه (RPM) | سقف در روز (RPD) | سقف توکن در دقیقه (TPM) | مشخصات و کاربرد |
| :--- | :---: | :---: | :---: | :--- |
| **Gemini 2.5 Flash** | **15 RPM** | **1,500 RPD** | 1,000,000 | 🌟 بالاترین سازگاری، دقت استخراج سوال و کلید در سریع‌ترین زمان ممکن |
| **Gemini 3.6 Flash** | **15 RPM** | **1,500 RPD** | 1,000,000 | ⚡ نسل ۳.۶ جدید بهینه‌شده بدون تاخیر تفکر (دقت بالا در جداول و ریاضیات) |
| **Gemini 3.5 Flash-Lite** | **30 RPM** | **1,500 RPD** | 1,000,000 | 🚀 سرعت فوق‌العاده بالا، سقف درخواست ۲ برابر (کمترین ریسک Rate Limit) |
| **Gemini Flash-Lite Latest** | **30 RPM** | **1,500 RPD** | 1,000,000 | 🔄 اتصال همیشگی به آخرین به‌روزرسانی شاخه لایت |

💡 **سیستم ضدخطای خودکار (Fallback)**: در صورت بروز خطای ترافیک یا محدودیت روی مدل انتخابی، سامانه به طور خودکار به مدل‌های بعدی سوئیچ می‌کند تا فرآیند استخراج متوقف نشود.
""")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # بخش ۳: تنظیمات کلید و تعداد سوالات
    st.markdown("##### ⚙️ ۴. تنظیمات تکمیلی کلید و تعداد سوالات")
    col_q_count, col_key_mode = st.columns([1, 1.5], gap="medium")
    
    with col_q_count:
        total_q_expected = st.number_input("تعداد کل سوالات:", min_value=0, max_value=500, value=155, step=5)
        
    with col_key_mode:
        answer_mode = st.selectbox(
            "وضعیت پاسخنامه آزمون:",
            [
                "کلید در فایل مجزا آپلود شده است (بالا)",
                "کلید در صفحه آخر همین فایل دفترچه سوالات است",
                "پاسخ‌های صحیح با فونت بولد در گزینه‌ها مشخص شده‌اند",
                "شماره صفحه اختصاصی کلید در همین PDF",
                "بدون پاسخنامه / وارد کردن دستی در تب ۲"
            ]
        )
    
    key_page_num = 0
    answers_bold = False
    if answer_mode == "پاسخ‌های صحیح با فونت بولد در گزینه‌ها مشخص شده‌اند":
        answers_bold = True
    elif answer_mode == "شماره صفحه اختصاصی کلید در همین PDF":
        key_page_num = st.number_input("شماره صفحه پاسخنامه در PDF سوالات:", min_value=1, max_value=200, value=16)

    st.markdown("<br>", unsafe_allow_html=True)
    extract_btn = st.button(f"🚀 شروع استخراج هوشمند با {model_choice}", type="primary", width="stretch")

    if extract_btn:
        if not uploaded_pdf:
            st.error("❌ لطفاً ابتدا فایل PDF سوالات را بارگذاری فرمایید.")
        elif not st.session_state.get("api_key"):
            st.error("❌ لطفاً کلید Gemini API را در سایدبار سمت راست وارد فرمایید.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.empty()

            def update_progress(pct, msg):
                if pct is not None:
                    progress_bar.progress(pct)
                if msg:
                    status_text.info(msg)

            def handle_stream(chunk_text, total_chars, q_count_est):
                calc_progress = min(30 + int((total_chars / 3000) * 45), 75)
                progress_bar.progress(calc_progress)
                status_text.markdown(f"🟢 **هوش مصنوعی فعال است:** در حال تحلیل ساختار آزمون و استخراج متون...")
                
                with metrics_container.container():
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric(label="📊 سوالات استخراج‌شده", value=f"{q_count_est} سوال")
                    with m2:
                        st.metric(label="📥 حجم پاسخ", value=f"{total_chars:,} کاراکتر")
                    with m3:
                        st.metric(label="⚡ وضعیت اتصال", value="استریم زنده 🟢")

            try:
                configure_gemini(st.session_state["api_key"], proxy=proxy_url if use_proxy else None)
                
                update_progress(5, "در حال رندر صفحات دفترچه سوالات...")
                question_images = convert_file_to_images(uploaded_pdf, dpi=200)
                update_progress(15, f"✅ تعداد {len(question_images)} صفحه سوال رندر شد.")
                
                key_images = None
                if uploaded_key_file:
                    update_progress(20, "در حال رندر فایل کلید پاسخنامه...")
                    key_images = convert_file_to_images(uploaded_key_file, dpi=200)
                    update_progress(25, f"✅ تعداد {len(key_images)} صفحه پاسخنامه رندر شد.")
                
                questions_result = extract_questions_from_images(
                    question_images=question_images,
                    answer_key_images=key_images,
                    api_key=st.session_state["api_key"],
                    model_name=model_choice,
                    total_questions_expected=total_q_expected if total_q_expected > 0 else None,
                    answers_are_bolded=answers_bold,
                    answer_key_page=key_page_num if answer_mode == "شماره صفحه اختصاصی کلید در همین PDF" else (len(question_images) if answer_mode == "کلید در صفحه آخر همین فایل دفترچه سوالات است" else 0),
                    progress_callback=update_progress,
                    stream_callback=handle_stream
                )
                
                st.session_state["questions"] = questions_result
                save_cached_questions(questions_result)
                
                metrics_container.empty()
                st.balloons()
                st.success(f"🎉 استخراج با موفقیت تکمیل و در حافظه ذخیره شد! تعداد {len(questions_result)} سوال استخراج شدند.")
                
            except Exception as e:
                st.error(f"❌ خطا در استخراج: {e}")

# --- تب ۲: پیش‌نمایش، ویرایش جدول و بازبینی تکی سوالات ---
with tab2:
    questions = st.session_state.get("questions", [])
    if not questions:
        questions = load_cached_questions()
        if questions:
            st.session_state["questions"] = questions
    
    col_stat, col_import, col_reset = st.columns([1.5, 1, 1], gap="medium")
    with col_stat:
        if questions:
            st.markdown(f"##### 📋 تعداد سوالات آماده ثبت: `{len(questions)}` سوال (ذخیره روی دیسک ✅)")
        else:
            st.info("💡 هنوز سوالی در حافظه نیست. فایل PDF را در تب اول استخراج کنید یا یک فایل JSON بارگذاری نمایید.")
            
    with col_import:
        uploaded_json = st.file_uploader(
            "📂 بارگذاری فایل JSON قبلی:",
            type=["json"],
            label_visibility="collapsed",
            key="uploader_json_tab2"
        )
        if uploaded_json is not None:
            file_sig = f"{uploaded_json.name}_{uploaded_json.size}"
            if st.session_state.get("last_imported_file_sig") != file_sig:
                try:
                    uploaded_json.seek(0)
                    loaded_data = json.load(uploaded_json)
                    if isinstance(loaded_data, list) and len(loaded_data) > 0:
                        st.session_state["questions"] = loaded_data
                        st.session_state["last_imported_file_sig"] = file_sig
                        save_cached_questions(loaded_data)
                        st.toast(f"✅ تعداد {len(loaded_data)} سوال با موفقیت بارگذاری گردید.", icon="🎉")
                        st.rerun()
                    else:
                        st.error("❌ فایل JSON فاقد ساختار معتبر (لیست سوالات) است.")
                except Exception as err:
                    st.error(f"❌ خطا در خواندن فایل JSON: {err}")
                
    with col_reset:
        if questions:
            if st.button("🗑 پاکسازی حافظه آزمون فعلی", width="stretch"):
                st.session_state["questions"] = []
                st.session_state["last_imported_file_sig"] = None
                save_cached_questions([])
                st.rerun()

    if questions:
        # بخش الف: جدول سراسری تمام‌صفحه
        st.markdown("###### 📊 نمای کلی جدول سوالات:")
        formatted_table = []
        for q in questions:
            opts = q.get("options", ["", "", "", ""])
            formatted_table.append({
                "شماره": q.get("number"),
                "صورت سوال": q.get("question"),
                "گزینه ۱": opts[0] if len(opts) > 0 else "",
                "گزینه ۲": opts[1] if len(opts) > 1 else "",
                "گزینه ۳": opts[2] if len(opts) > 2 else "",
                "گزینه ۴": opts[3] if len(opts) > 3 else "",
                "کلید صحیح": q.get("correct_option")
            })
            
        edited_df = st.data_editor(
            formatted_table,
            width="stretch",
            num_rows="dynamic",
            height=500,
            column_config={
                "شماره": st.column_config.NumberColumn("شماره", width="small", format="%d"),
                "صورت سوال": st.column_config.TextColumn("صورت سوال", width="large", max_chars=4000),
                "گزینه ۱": st.column_config.TextColumn("گزینه ۱", width="medium"),
                "گزینه ۲": st.column_config.TextColumn("گزینه ۲", width="medium"),
                "گزینه ۳": st.column_config.TextColumn("گزینه ۳", width="medium"),
                "گزینه ۴": st.column_config.TextColumn("گزینه ۴", width="medium"),
                "کلید صحیح": st.column_config.SelectboxColumn("کلید صحیح", width="small", options=[1, 2, 3, 4], required=False)
            }
        )
        
        col_save, col_dl = st.columns([1, 1], gap="medium")
        with col_save:
            if st.button("💾 ذخیره تغییرات جدول در حافظه و دیسک", width="stretch"):
                updated_questions = []
                for row in edited_df:
                    updated_questions.append({
                        "number": row.get("شماره"),
                        "question": row.get("صورت سوال"),
                        "options": [row.get("گزینه ۱"), row.get("گزینه ۲"), row.get("گزینه ۳"), row.get("گزینه ۴")],
                        "correct_option": row.get("کلید صحیح")
                    })
                st.session_state["questions"] = updated_questions
                save_cached_questions(updated_questions)
                st.success("✅ تمامی تغییرات در حافظه دائمی و فایل extracted_questions.json ذخیره شد.")
                st.rerun()
                
        with col_dl:
            json_str = json.dumps(st.session_state["questions"], ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 دانلود فایل خروجی JSON",
                data=json_str.encode("utf-8"),
                file_name="extracted_questions.json",
                mime="application/json",
                width="stretch"
            )

        # بخش ب: ویرایشگر و بازبین اختصاصی تکی (برای مشاهده آسان ریدینگ‌های بلند مثل سوال ۲۶)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="inspector-card">
            <h4 style="margin: 0 0 10px 0; color: #60a5fa; font-weight: 800;">🔍 ویرایشگر و بازبین اختصاصی سوال (مشاهده کامل ریدینگ‌ها و فرمول‌ها)</h4>
            <p style="margin: 0 0 14px 0; color: #9ca3af; font-size: 0.92rem;">
                اگر سوالی متن طولانی یا ریدینگ دارد (مانند سوالات درک مطلب انگلیسی)، شماره سوال را انتخاب کنید تا متن کامل آن در باکس اسکرول‌پذیر اختصاصی باز شود:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        q_numbers = [q.get("number") for q in questions]
        selected_q_num = st.selectbox("شماره سوال مورد نظر را انتخاب کنید:", q_numbers, index=25 if len(q_numbers) >= 26 else 0)
        
        selected_q_idx = next((i for i, q in enumerate(questions) if q.get("number") == selected_q_num), None)
        
        if selected_q_idx is not None:
            target_q = questions[selected_q_idx]
            
            with st.container():
                edit_q_text = st.text_area(
                    f"📝 متن کامل صورت سوال {selected_q_num} (با قابلیت اسکرول راحت و بازشدن متن کامل ریدینگ):",
                    value=target_q.get("question", ""),
                    height=240
                )
                
                opts = target_q.get("options", ["", "", "", ""])
                while len(opts) < 4:
                    opts.append("")
                    
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    opt1 = st.text_input(f"گزینه ۱:", value=opts[0], key=f"insp_opt1_{selected_q_num}")
                    opt2 = st.text_input(f"گزینه ۲:", value=opts[1], key=f"insp_opt2_{selected_q_num}")
                with col_o2:
                    opt3 = st.text_input(f"گزینه ۳:", value=opts[2], key=f"insp_opt3_{selected_q_num}")
                    opt4 = st.text_input(f"گزینه ۴:", value=opts[3], key=f"insp_opt4_{selected_q_num}")
                    
                col_key_edit, col_btn_edit = st.columns([1, 1])
                with col_key_edit:
                    curr_k = target_q.get("correct_option")
                    k_idx = (curr_k - 1) if (curr_k and 1 <= curr_k <= 4) else 0
                    new_key = st.selectbox(f"کلید صحیح سوال {selected_q_num}:", [1, 2, 3, 4], index=k_idx, key=f"insp_key_{selected_q_num}")
                    
                with col_btn_edit:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(f"💾 ثبت تغییرات سوال {selected_q_num}", type="primary", width="stretch", key=f"save_single_{selected_q_num}"):
                        questions[selected_q_idx] = {
                            "number": selected_q_num,
                            "question": edit_q_text,
                            "options": [opt1, opt2, opt3, opt4],
                            "correct_option": new_key
                        }
                        st.session_state["questions"] = questions
                        save_cached_questions(questions)
                        st.success(f"✅ تغییرات سوال {selected_q_num} با موفقیت ذخیره شد!")
                        st.rerun()

# --- تب ۳: بارگذاری خودکار در سنجشکده ---
with tab3:
    questions_to_upload = st.session_state.get("questions", [])
    if not questions_to_upload:
        questions_to_upload = load_cached_questions()
        if questions_to_upload:
            st.session_state["questions"] = questions_to_upload
    
    if not questions_to_upload:
        st.warning("⚠️ هیچ سوالی برای بارگذاری آماده نیست. ابتدا سوالات را استخراج فرمایید.")
    else:
        tags_list = [t.strip() for t in re.split(r'[,،;\n\r]+', sanjeshkade_tags) if t.strip()]
        tags_html = " ".join([f"<span style='display:inline-block; background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; margin: 2px;'>🏷️ {t}</span>" for t in tags_list]) if tags_list else "<span style='color: #9ca3af;'><i>(بدون تگ)</i></span>"

        st.markdown(f"""
        <div class="section-card">
            <p style="margin: 0 0 8px 0; font-size: 1.05rem;">🎯 <b>وضعیت:</b> آماده ثبت <b>{len(questions_to_upload)}</b> سوال در سامانه سنجشکده</p>
            <p style="margin: 0 0 6px 0; color: #9ca3af;">🔗 <b>آدرس مقصد:</b> <code>{sanjeshkade_url}</code></p>
            <p style="margin: 0 0 6px 0; color: #9ca3af;">📅 <b>شماره جلسه:</b> <code>{sanjeshkade_session}</code></p>
            <div style="margin-top: 8px;">
                <span style="color: #9ca3af; font-size: 0.9rem; font-weight: 600;">🏷️ تگ‌های ارسالی ({len(tags_list)} برچسب):</span>
                <div style="margin-top: 6px;">{tags_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        start_auto_btn = st.button("🚀 شروع فرآیند بارگذاری خودکار در سنجشکده", type="primary", width="stretch")
        
        if start_auto_btn:
            if not sanjeshkade_user or not sanjeshkade_pass:
                st.error("❌ لطفاً ابتدا نام کاربری و رمز عبور سامانه سنجشکده را در سایدبار راست وارد فرمایید.")
            else:
                auto_progress = st.progress(0)
                auto_status = st.empty()
                log_box = st.empty()
                
                log_messages = []
                
                def live_log(msg):
                    log_messages.append(msg)
                    log_box.code("\n".join(log_messages[-10:]), language="text")
                    
                def live_progress(pct, msg):
                    auto_progress.progress(pct)
                    auto_status.info(msg)
                
                result = run_sanjeshkade_automation(
                    username=sanjeshkade_user,
                    password=sanjeshkade_pass,
                    create_question_url=sanjeshkade_url,
                    session_number=sanjeshkade_session,
                    tags=tags_list,
                    questions=questions_to_upload,
                    headless=headless_mode,
                    progress_callback=live_progress,
                    log_callback=live_log
                )
                
                if result.get("success", 0) > 0:
                    st.balloons()
                    st.success(f"🎉 تبریک! تعداد {result['success']} سوال با موفقیت در سامانه سنجشکده ثبت شد.")
                else:
                    st.error(f"❌ خطا در فرآیند ثبت: {result.get('error', 'عدم ثبت سوالات')}")

# --- تب ۴: ساخت خودکار درسنامه در سنجشکده ---
with tab4:
    st.markdown("### 📚 ساخت خودکار و دسته‌جمعی درسنامه‌ها در سنجشکده")
    st.caption("این ابزار تمامی سوالات ثبت‌شده در درس مورد نظر را استخراج کرده و به صورت خودکار با هوش مصنوعی برای تک‌تک آن‌ها درسنامه (Lesson Plan) تولید می‌کند.")

    # تشخیص هوشمند پیش‌فرض آدرس درس از تنظیمات
    default_target_url = "https://sanjeshkade.ir/User/Lessons/Questions/300"
    if sanjeshkade_url:
        try:
            default_target_url = normalize_lesson_url(sanjeshkade_url)
        except Exception:
            default_target_url = sanjeshkade_url

    st.markdown("""
    <div class="section-card">
        <p style="margin: 0 0 8px 0; font-size: 1.05rem;">🎯 <b>تولید درسنامه خودکار (GenerateLessonPlanBatch):</b></p>
        <p style="margin: 0 0 6px 0; color: #9ca3af; font-size: 0.92rem; line-height: 1.8;">
            ۱. سامانه با نام کاربری و رمز عبور شما در حالت نامرئی وارد سنجشکده شده و کوکی‌های فعال را برمی‌دارد.<br>
            ۲. فهرست تمام سوالات موجود در درس مقصد را استخراج می‌کند.<br>
            ۳. درخواست‌های تولید درسنامه به صورت خودکار، پشت‌سرهم و با نوار وضعیت زنده ثبت می‌شوند.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_lesson_url, col_lesson_delay = st.columns([2.5, 1], gap="medium")
    with col_lesson_url:
        target_lesson_input = st.text_input(
            "🔗 آدرس صفحه سوالات یا شناسه درس مقصد:",
            value=default_target_url,
            help="می‌توانید آدرس کامل صفحه سوالات یا فقط شماره درس (مثلاً 300) را وارد نمایید."
        )
    with col_lesson_delay:
        lesson_delay_input = st.number_input(
            "⏱️ وقفه بین سوالات (ثانیه):",
            min_value=0.2,
            max_value=10.0,
            value=1.0,
            step=0.2,
            help="جهت جلوگیری از فشار به سرور سنجشکده و پردازش بدون خطای بک‌اند"
        )

    with st.expander("🔑 ورود دستی کوکی نشست (اختیاری - ویژه کاربران حرفه‌ای)"):
        st.markdown("""
        اگر مایلید بدون لاگین خودکار سلنیوم مستقیماً از کوکی مرورگر باز خود استفاده کنید، متن کامل هدر Cookie را در زیر قرار دهید:
        """)
        manual_cookie = st.text_area(
            "متن کوکی مرورگر (.AspNetCore.Cookies و .AspNetCore.Antiforgery):",
            value="",
            height=70,
            placeholder=".AspNetCore.Antiforgery.xxx=...; .AspNetCore.Cookies=..."
        )

    btn_start_lesson = st.button("🚀 شروع ورود و ساخت خودکار درسنامه‌ها", type="primary", width="stretch")

    if btn_start_lesson:
        if not manual_cookie.strip() and (not sanjeshkade_user or not sanjeshkade_pass):
            st.error("❌ لطفاً نام کاربری و رمز عبور سنجشکده را در سایدبار راست وارد فرمایید (یا کوکی دستی را در بخش تنظیمات وارد نمایید).")
        else:
            lp_progress = st.progress(0)
            lp_status = st.empty()
            lp_metrics = st.empty()
            lp_log_box = st.empty()

            log_history = []

            def handle_lp_log(msg):
                log_history.append(msg)
                lp_log_box.code("\n".join(log_history[-10:]), language="text")

            def handle_lp_progress(curr, total, qid, success, msg):
                pct = int((curr / total) * 100) if total > 0 else 0
                lp_progress.progress(pct)
                lp_status.info(f"⏳ در حال پردازش سوال {curr} از {total} (شناسه سوال: {qid})...")

            with st.spinner("در حال ارتباط با سامانه سنجشکده و پردازش درسنامه‌ها..."):
                try:
                    summary = run_batch_lesson_plan_generation(
                        target_url_or_id=target_lesson_input,
                        cookie_str=manual_cookie.strip() if manual_cookie.strip() else None,
                        username=sanjeshkade_user,
                        password=sanjeshkade_pass,
                        delay=lesson_delay_input,
                        progress_callback=handle_lp_progress,
                        log_callback=handle_lp_log
                    )

                    lp_progress.progress(100)
                    lp_status.success(f"🎉 عملیات ساخت درسنامه برای {summary['success_count']} سوال با موفقیت ارسال شد!")
                    st.balloons()

                    with lp_metrics.container():
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("📊 کل سوالات درس", f"{summary['total']} سوال")
                        with m2:
                            st.metric("✅ درخواست‌های موفق", f"{summary['success_count']} سوال")
                        with m3:
                            st.metric("❌ خطاها", f"{summary['failed_count']} سوال")

                except Exception as ex:
                    st.error(f"❌ خطا در فرآیند تولید درسنامه: {ex}")

# --- پاورقی و حمایت از گیت‌هاب ---
st.markdown("""
<div class="github-box">
    <h3 style="margin: 0 0 8px 0; color: #f9fafb; font-weight: 800;">☕️ حمایت از توسعه‌دهنده</h3>
    <p style="margin: 0 auto 12px auto; max-width: 650px; color: #9ca3af; font-size: 0.96rem; line-height: 1.8;">
        اگه این پروژه نجاتت داد و از ساعت‌ها کپی‌پیست دستی و کور شدن پای فرم‌های وب خلاصت کرد، با یه <b>⭐️ استار زدن توی گیت‌هاب</b> خستگی رو از تنمون در کن و به پروژه انرژی بده! 😉🚀
    </p>
    <a href="https://github.com/Hamed-rasooli/question-extractor" target="_blank" class="github-link">
        <svg height="18" width="18" viewBox="0 0 16 16" fill="currentColor" style="vertical-align: middle;">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
        </svg>
        <span>⭐ استار زدن به ریپازیتوری در گیت‌هاب</span>
    </a>
</div>
""", unsafe_allow_html=True)
