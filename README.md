<div align="center">

# 📝 سامانه خودکار تبدیل دفترچه آزمون به سنجشکده
### PDF to Sanjeshkade: Instant AI Quiz Extractor & Auto-Uploader

[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Selenium](https://img.shields.io/badge/Automation-Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<br/>

**دیگه نیازی به ساعت‌ها کپی‌پیست دستی، تایپ فرمول‌ها و تیک زدن گزینه‌ها در سنجشکده ندارید!**  
این برنامه کل دفترچه آزمون رو می‌خونه، پاسخنامه سازمان سنجش رو روش منطبق می‌کنه و با یک کلیک همه رو می‌فرسته تو پنل کاربریتون.

<br/>

[**🇮🇷 راهنمای فارسی و نحوه استفاده**](#-راهنمای-فارسی) &nbsp; | &nbsp; [**🇬🇧 English Summary & Usage**](#-english-guide)

</div>

---

<a name="-راهنمای-فارسی"></a>
## 🇮🇷 راهنمای فارسی

### 🎯 این برنامه چه کاری براتون انجام میده؟ (نتیجه نهایی)
1. **استخراج ۱۰۰٪ خودکار سوالات از PDF:** دفترچه آزمون (کنکور، ارشد، دکتری یا استخدامی) رو به برنامه می‌دید؛ هوش مصنوعی تمام سوالات، ۴ گزینه، متن‌های طولانی (ریدینگ‌ها) و فرمول‌ها رو دقیق استخراج می‌کنه.
2. **انطباق خودکار کلید پاسخنامه:** صفحه کلید آزمون رو می‌خونه و گزینه صحیح هر سوال رو خودش مشخص می‌کنه.
3. **ثبت خودکار در سایت سنجشکده ([sanjeshkade.ir](https://sanjeshkade.ir)):** مرورگر رو باز می‌کنه، وارد اکانتتون میشه و تمام سوالات رو به همراه تگ و سال آزمون، دونه‌دونه وارد و تایید می‌کنه.

---

### 🚀 نحوه اجرای سریع و آسان (بدون نیاز به دانش فنی)

#### 🪟 برای کاربران ویندوز (Windows)
فقط کافیه روی فایل زیر **دوبار کلیک (Double-Click)** کنید:
📁 **`run_windows.bat`**
> 💡 اگر پایتون نصب نباشه یا پکیج‌ها ناقص باشن، برنامه به صورت خودکار همه چیز رو آماده می‌کنه و در مرورگر باز میشه.

#### 🐧 🍏 برای کاربران لینوکس و مک (Linux / macOS)
یک ترمینال در پوشه پروژه باز کنید و دستور زیر رو بزنید:
```bash
bash run_linux_mac.sh
```

---

### 📋 ۳ مرحله ساده برای ثبت آزمون در سنجشکده

```mermaid
graph LR
    A["📄 ۱. انتخاب فایل PDF"] --> B["🤖 ۲. استخراج با هوش مصنوعی"]
    B --> C["📊 ۳. مشاهده، ویرایش و ثبت خودکار در سنجشکده"]
```

1. **مرحله ۱ (تنظیمات اولیه در سایدبار راست):**
   * **کلید API گوگل:** کلید رایگان خودتون رو از [Google AI Studio](https://aistudio.google.com/app/apikey) بگیرید و وارد کنید.
   * **اطلاعات سنجشکده:** نام کاربری، رمز عبور، لینک صفحه ثبت سوال درس (مثلاً `https://sanjeshkade.ir/User/Lessons/CreateQuestion/155`) و عنوان آزمون/تگ رو بنویسید.
   *(این اطلاعات روی سیستم خودتون ذخیره میشن و دفعه‌های بعد نیاز به تایپ مجدد نیست).*

2. **مرحله ۲ (استخراج هوشمند):**
   * فایل PDF دفترچه رو انتخاب کنید.
   * شماره صفحات سوالات و صفحه کلید رو مشخص کنید و دکمه **شروع استخراج** رو بزنید.

3. **مرحله ۳ (ثبت نهایی در سنجشکده):**
   * در تب دوم می‌تونید سوالات رو در جدول ببینید و در صورت تمایل ویرایش کنید یا خروجی JSON دانلود کنید.
   * در تب سوم دکمه **شروع فرآیند بارگذاری خودکار** رو بزنید تا ربات همه سوالات رو در سایت ثبت و ذخیره کنه!

---

### 📦 راهنمای نصب دستی (برای برنامه‌نویسان)

اگر تمایل دارید به صورت دستی محیط رو راه‌اندازی کنید:

```bash
# ۱. ساخت و فعال‌سازی محیط مجازی
python3 -m venv .venv
source .venv/bin/activate   # در ویندوز: .venv\Scripts\activate

# ۲. نصب نیازمندی‌ها
pip install -r requirements.txt

# ۳. اجرای داشبورد
streamlit run app.py
```

---

<br/>

<a name="-english-guide"></a>
## 🇬🇧 English Guide

### 🎯 What Does This Project Do? (Core Outcome)
* **Automated Exam Extraction:** Feed any multiple-choice quiz PDF (university entrance, professional certifications, etc.) to the app. Google Gemini Vision AI parses all questions, 4 options, long reading passages, and formulas.
* **Smart Answer Key Matching:** Automatically reads the official answer key table and sets the correct option for every single question.
* **One-Click Sanjeshkade Upload:** Automatically logs into [sanjeshkade.ir](https://sanjeshkade.ir) via Selenium and registers all questions with tags and session years.

---

### 🚀 Quick Launch (Beginner Friendly)

#### 🪟 Windows
Simply double-click:
📁 **`run_windows.bat`**

#### 🐧 🍏 Linux / macOS
Open a terminal in the folder and run:
```bash
bash run_linux_mac.sh
```

---

### 📁 Project Structure

| File / Directory | Description |
| :--- | :--- |
| **`app.py`** | Modern interactive Web Dashboard (Streamlit). |
| **`core_extractor.py`** | AI Vision engine for question & answer key extraction. |
| **`core_automator.py`** | Automation engine for logging in and uploading to Sanjeshkade. |
| **`run_windows.bat`** | One-click launcher for Windows. |
| **`run_linux_mac.sh`** | One-click launcher for Linux and macOS. |
| **`requirements.txt`** | List of required Python packages. |

---

### ⭐ حمایت از پروژه
اگر این ابزار ساعت‌ها کار تکراری رو براتون حذف کرد، با زدن دکمه **⭐️ Star** در بالای صفحه گیت‌هاب خستگی رو از تنمون در کنید! 😉🚀
