<div align="center">

# 📝 AI Question Extractor & Sanjeshkade Automator
### سامانه استخراج هوشمند سوالات آزمون با هوش مصنوعی و بارگذاری خودکار در سنجشکده

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini AI](https://img.shields.io/badge/Google%20Gemini-Flash%20%2F%202.5-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Selenium](https://img.shields.io/badge/Selenium-4.20%2B-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<br/>

[**فارسی (Persian)**](#-راهنمای-فارسی) &nbsp; | &nbsp; [**English**](#-english-guide)

</div>

---

<a name="-راهنمای-فارسی"></a>
## 🇮🇷 راهنمای فارسی

### 💡 معرفی پروژه
این پروژه یک ابزار جامع، مدرن و تحت وب برای **استخراج ۱۰۰٪ خودکار سوالات چهارگزینه‌ای از فایل‌های PDF آزمون** (کنکور کارشناسی، ارشد، دکتری، استخدامی و ...) با بهره‌گیری از مدل‌های بینایی پیشرفته **Google Gemini AI** و **ثبت دسته‌جمعی و بدون نقص آن‌ها در سامانه سنجشکده ([sanjeshkade.ir](https://sanjeshkade.ir))** است.

با استفاده از این ابزار، نیازی به ساعت‌ها کپی‌پیست دستی، تایپ فرمول‌ها، تنظیم گزینه‌ها و انتخاب تک‌تک کلیدها در فرم‌های وب نخواهید داشت.

---

### ✨ ویژگی‌های برجسته
* **🧠 بینایی ماشین فوق‌العاده با Gemini:** استخراج دقیق متن سوالات، گزینه‌ها، متن‌های درک مطلب طولانی (Reading Comprehension)، عبارات انگلیسی و فرمول‌های LaTeX.
* **🔑 استخراج و تطبیق خودکار کلید پاسخنامه:** خواندن هوشمند جدول کلید پاسخنامه سازمان سنجش از صفحه آخر دفترچه یا تشخیص خودکار گزینه پررنگ (Bold).
* **⚡ بدون نیاز به ابزارهای جانبی (No Poppler):** تبدیل پرسرعت صفحات PDF به تصاویر باکیفیت به صورت درونی با کتابخانه مدرن `PyMuPDF` (بدون نیاز به نصب Poppler یا تنظیم PATH).
* **📊 داشبورد وب تعاملی و مدرن (Streamlit):**
  * جدول داده زنده برای ویرایش سریع شماره سوالات، گزینه‌ها و کلید صحیح.
  * بازبین و ویرایشگر اختصاصی برای متون بلند، ریدینگ‌ها و فرمول‌ها.
  * ذخیره دائمی، پشتیبان‌گیری و خروجی `JSON`.
* **🌐 اتوماسیون هوشمند و پایدار سنجشکده:**
  * ورود خودکار به سامانه و ثبت بدون وقفه سوالات.
  * **موتور انطباق هوشمند تگ‌ها (Smart Tag Matching):** اتصال مستقیم به `tagService` سامانه و استعلام موضوعات معتبر دیتابیس بدون خطای تایم‌اوت.
  * پایدارسازی گرافیکی لینوکس/Wayland و اعمال DNS مستقیم برای جلوگیری از اختلال شبکه.
  * حالت پس‌زمینه (Headless Mode) و پشتیبانی از پروکسی برای درخواست‌های هوش مصنوعی.

---

### 🚀 راهنمای سریع راه‌اندازی (یک کلیک)

#### 🖥️ ویندوز (Windows)
فقط کافیست روی فایل **`run.bat`** دوبار کلیک کنید! 
> این اسکریپت در صورت نیاز، پایتون را نصب کرده، محیط مجازی `.venv` را آماده می‌کند، پکیج‌ها را نصب کرده و داشبورد را در مرورگر باز می‌کند.

#### 🐧 لینوکس / مک (Linux / macOS)
ترمینال را در پوشه پروژه باز کنید و دستور زیر را اجرا نمایید:
```bash
bash run.sh
```
یا:
```bash
chmod +x run.sh
./run.sh
```

---

### 🛠️ راه‌اندازی دستی (Manual Installation)

#### ۱. پیش‌نیازها
* پایتون نسخه 3.9 یا بالاتر ([دانلود پایتون](https://www.python.org/downloads/))
* مرورگر Google Chrome

#### ۲. کلون کردن مخزن و ورود به پوشه
```bash
git clone https://github.com/Hamed-rasooli/question-extractor.git
cd question-extractor
```

#### ۳. ایجاد و فعال‌سازی محیط مجازی (Virtual Environment)
* **ویندوز (PowerShell / CMD):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```
* **لینوکس / مک (Bash / Zsh):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### ۴. نصب پیش‌نیازها
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### ۵. اجرای برنامه
```bash
streamlit run app.py
```
سپس مرورگر را باز کرده و به آدرس `http://localhost:8501` بروید.

---

### 📖 راهنمای گام‌به‌گام کار با برنامه

1. **تنظیمات اولیه (سایدبار راست):**
   * **کلید API گوگل:** کلید اختصاصی خود را از [Google AI Studio](https://aistudio.google.com/app/apikey) دریافت کرده و وارد کنید.
   * **اطلاعات سنجشکده:** نام کاربری، رمز عبور، آدرس صفحه ایجاد سوال درس (مثلاً `https://sanjeshkade.ir/User/Lessons/CreateQuestion/155`)، شماره جلسه/سال (مثلاً `1403`) و عنوان آزمون/تگ پیش‌فرض را وارد فرمایید.
   *(تنظیمات شما به صورت امن و محلی ذخیره می‌شوند).*
2. **تب ۱ (استخراج هوشمند از PDF):**
   * فایل PDF آزمون را بارگذاری کنید.
   * محدوده صفحات سوالات و صفحه کلید پاسخنامه را مشخص کنید.
   * دکمه **شروع استخراج هوشمند** را بزنید تا هوش مصنوعی پردازش را آغاز کند.
3. **تب ۲ (مشاهده و ویرایش):**
   * سوالات استخراج‌شده را در جدول مشاهده و در صورت نیاز متن یا کلیدها را تصحیح کنید.
   * می‌توانید خروجی `JSON` را برای استفاده‌های بعدی دانلود کنید.
4. **تب ۳ (بارگذاری خودکار در سنجشکده):**
   * پیش‌نمایش تگ‌ها و وضعیت سوالات را بررسی کنید.
   * روی **شروع فرآیند بارگذاری خودکار** کلیک کنید و گزارش زنده ورود و ثبت سوالات را مشاهده نمایید.

---

<br/>

<a name="-english-guide"></a>
## 🇬🇧 English Guide

### 💡 Overview
**AI Question Extractor & Automator** is a modern, end-to-end web tool designed to automatically extract multiple-choice questions (MCQs), options, and official answer keys from exam PDF booklets using **Google Gemini Vision AI**, and systematically upload them directly into the **Sanjeshkade platform ([sanjeshkade.ir](https://sanjeshkade.ir))** using Selenium automation.

Say goodbye to tedious manual copy-pasting, formatting LaTeX formulas, and manual key selection.

---

### ✨ Key Features
* **🧠 Gemini AI Multimodal Extraction:** High-accuracy extraction of Persian & English text, reading passages, mathematical formulas (LaTeX), and option structures.
* **🔑 Automated Answer Key Pairing:** Reads answer tables from dedicated key pages or detects bolded option choices automatically.
* **⚡ Zero External Binaries:** High-speed PDF page rendering powered by `PyMuPDF` (no Poppler installation or PATH configuration required).
* **📊 Modern Interactive Web Dashboard (Streamlit):**
  * Dynamic data editor table for batch edits.
  * Specialized inspector view for reading comprehension and formula checks.
  * Local auto-persistence & `JSON` backup import/export.
* **🌐 Robust Sanjeshkade Automator:**
  * Automated login, question filling, option checking, and submission.
  * **Smart Tag Resolver:** Direct integration with Sanjeshkade's internal `tagService` API with fuzzy subject matching and year-string sanitization.
  * Linux Wayland GPU stabilization and direct host DNS mapping.
  * Headless browser mode & AI proxy support.

---

### 🚀 Quick Start (One-Click)

#### 🖥️ Windows
Simply double-click **`run.bat`**.
> Automatically provisions Python if needed, creates an isolated virtual environment, installs dependencies, and launches the dashboard.

#### 🐧 Linux / macOS
Open a terminal in the project directory and run:
```bash
bash run.sh
```

---

### 🛠️ Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/Hamed-rasooli/question-extractor.git
cd question-extractor

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install packages
pip install --upgrade pip
pip install -r requirements.txt

# 4. Launch web dashboard
streamlit run app.py
```

---

### 📁 Project Structure

```text
question-extractor/
├── app.py                  # Streamlit Web Dashboard & UI controller
├── core_extractor.py       # AI Vision Engine & Answer Key parser (Gemini + PyMuPDF)
├── core_automator.py       # Selenium Web Automator & Sanjeshkade Tag Resolver
├── requirements.txt        # Python dependency manifest
├── run.sh                  # One-click Linux / macOS launcher
├── run.bat                 # One-click Windows launcher
├── .streamlit/
│   └── config.toml         # Dark theme & custom Streamlit configuration
├── .gitignore              # Git ignore rules (protects credentials & local caches)
└── README.md               # Bilingual documentation & guides
```

---

### ☕ Support & Contribution

If this project saved you hours of manual work, consider giving it a **⭐️ Star on GitHub**!

Created by **[Hamed Rasooli](https://github.com/Hamed-rasooli)**. Contributions, bug reports, and suggestions are welcome!
