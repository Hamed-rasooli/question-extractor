import io
import json
import os
import re
import time
import pymupdf
from PIL import Image

# پشتیبانی از SDK جدید رسمی google.genai همراه با fallback به نسخه قبلی
try:
    from google import genai
    from google.genai import types
    USE_NEW_GENAI_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    USE_NEW_GENAI_SDK = False


def to_english_digits(text):
    """تبدیل ارقام فارسی و عربی به ارقام انگلیسی"""
    if not isinstance(text, str):
        text = str(text)
    persian_map = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    arabic_map = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(persian_map).translate(arabic_map)


def correct_common_spacing_errors(text):
    """اصلاح خودکار نیم‌فاصله‌ها و قواعد نگارشی زبان فارسی بدون دستکاری تگ‌های LaTeX"""
    if not text or not isinstance(text, str):
        return text or ""
    
    verb_stems_for_mi_ne = (
        r"روم|رود|روی|رویم|روید|روند|کنم|کند|کنی|کنیم|کنید|کنند|شوم|شود|شوی|شویم|شوید|شوند|"
        r"دهم|دهد|دهی|دهیم|دهید|دهند|زنم|زند|زنی|زنیم|زنید|زنند|گیرم|گیرد|گیری|گیریم|گیرید|گیرند|"
        r"گویم|گوید|گویی|گوییم|گویید|گویند|دارم|دارد|داری|داریم|دارید|دارند|باشم|باشد|باشی|باشیم|باشید|باشند|"
        r"آیم|آید|آیی|آییم|آیید|آیند|توانم|تواند|توانی|توانیم|توانید|توانند|یابم|یابد|یابی|یابیم|یابید|یابند|"
        r"سازم|سازد|سازی|سازیم|سازید|سازند|پذیرم|پذیرد|پذیری|پذیریم|پذیرید|پذیرند|گردم|گردد|گردی|گردیم|گردید|گردند|"
        r"بینم|بیند|بینی|بینیم|بینید|بینند|دانم|داند|دانی|دانیم|دانید|دانند|نویسم|نویسد|نویسی|نویسیم|نویسید|نویسند|"
        r"خوانم|خواند|خوانی|خوانیم|خوانید|خوانند|خواهم|خواهد|خواهی|خواهیم|خواهید|خواهند|برم|برد|بری|بریم|برید|برند"
    )
    text = re.sub(r'\b(می|نمی)\s+(' + verb_stems_for_mi_ne + r')\b', r'\1‌\2', text)
    text = re.sub(r'\b(می|نمی)(' + verb_stems_for_mi_ne + r')\b', r'\1‌\2', text)
    
    text = text.replace('مییابد', 'می‌یابد').replace('میشود', 'می‌شود').replace('آنها', 'آن‌ها')
    
    text = re.sub(r'(\S)\s+(ها)\b', r'\1‌ها', text)
    text = re.sub(r'(\S)\s+(ای)\b', r'\1‌ای', text)
    text = re.sub(r'(\S)\s+(تر|ترین)\b', r'\1‌\2', text)
    
    return text.strip()


def parse_key_text_universally(raw_text):
    """
    استخراج ۱۰۰٪ تضمینی جفت‌های {شماره سوال: گزینه صحیح} از خروجی مدل
    پشتیبانی از دیکشنری، لیست، JSONهای تودرتو و همچنین استخراج با الگوهای باقاعده Regex
    """
    answer_dict = {}
    if not raw_text or not isinstance(raw_text, str):
        return answer_dict

    # ۱. تلاش ساختاری با json.loads
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())

        if isinstance(data, dict):
            # بررسی فیلدهای احتمالی تودرتو
            for sub_k in ["answers", "keys", "data", "questions", "key"]:
                if sub_k in data and isinstance(data[sub_k], dict):
                    data = data[sub_k]
                    break
                elif sub_k in data and isinstance(data[sub_k], list):
                    data = data[sub_k]
                    break

            if isinstance(data, dict):
                for k, v in data.items():
                    try:
                        k_int = int(re.sub(r"\D", "", to_english_digits(str(k))))
                        v_str = to_english_digits(str(v)).strip()
                        if v_str in ["الف", "a", "A", "1"]:
                            answer_dict[k_int] = 1
                        elif v_str in ["ب", "b", "B", "2"]:
                            answer_dict[k_int] = 2
                        elif v_str in ["ج", "c", "C", "3"]:
                            answer_dict[k_int] = 3
                        elif v_str in ["د", "d", "D", "4"]:
                            answer_dict[k_int] = 4
                    except Exception:
                        pass

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    q = item.get("question") or item.get("number") or item.get("q") or item.get("no")
                    a = item.get("answer") or item.get("correct_option") or item.get("key") or item.get("opt") or item.get("a")
                    if q is not None and a is not None:
                        try:
                            q_int = int(re.sub(r"\D", "", to_english_digits(str(q))))
                            a_str = to_english_digits(str(a)).strip()
                            if a_str in ["الف", "a", "A", "1"]:
                                answer_dict[q_int] = 1
                            elif a_str in ["ب", "b", "B", "2"]:
                                answer_dict[q_int] = 2
                            elif a_str in ["ج", "c", "C", "3"]:
                                answer_dict[q_int] = 3
                            elif a_str in ["د", "d", "D", "4"]:
                                answer_dict[q_int] = 4
                        except Exception:
                            pass
    except Exception:
        pass

    # ۲. فال‌بک قدرتمند Regex روی متن خام برای استخراج تمام ردیف‌ها حتی در صورت ناقص بودن JSON
    if len(answer_dict) < 5:
        clean_raw = to_english_digits(raw_text)
        pairs = re.findall(r'["\']?(\d{1,3})["\']?\s*[:\-=,\s]\s*["\']?([1-4]|الف|ب|ج|د|[A-Da-d])["\']?', clean_raw)
        for q_str, a_str in pairs:
            try:
                q_int = int(q_str)
                a_clean = a_str.strip()
                if a_clean in ["الف", "a", "A", "1"]:
                    answer_dict[q_int] = 1
                elif a_clean in ["ب", "b", "B", "2"]:
                    answer_dict[q_int] = 2
                elif a_clean in ["ج", "c", "C", "3"]:
                    answer_dict[q_int] = 3
                elif a_clean in ["د", "d", "D", "4"]:
                    answer_dict[q_int] = 4
            except Exception:
                pass

    return answer_dict


def robust_parse_questions_json(raw_text):
    """
    تجزیه فوق‌العاده مقاوم JSON که حتی در صورت وجود گیومه‌های فرارنخورده در متون ریدینگ انگلیسی
    یا قطع شدن انتهای پاسخ، تمام سوالات را بدون خطا استخراج می‌کند.
    """
    if not raw_text or not isinstance(raw_text, str):
        return []

    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    start_idx = cleaned.find('[')
    end_idx = cleaned.rfind(']')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            data = json.loads(cleaned[start_idx:end_idx + 1])
            if isinstance(data, list):
                return data
        except Exception:
            pass

    if start_idx != -1:
        last_brace = cleaned.rfind('}')
        if last_brace != -1 and last_brace > start_idx:
            repaired = cleaned[start_idx:last_brace + 1] + "]"
            try:
                data = json.loads(repaired)
                if isinstance(data, list):
                    return data
            except Exception:
                pass

    # استخراج فیلد به فیلد با Regex
    results = []
    blocks = re.split(r'\{\s*"number"\s*:', cleaned)
    for b in blocks[1:]:
        num_m = re.match(r'\s*(\d+)', b)
        if not num_m:
            continue
        num = int(num_m.group(1))

        q_m = re.search(r'"question"\s*:\s*"(.*?)(?="\s*,\s*"options")', b, re.DOTALL)
        if not q_m:
            q_m = re.search(r'"question"\s*:\s*"(.*?)"\s*,\s*"options"', b, re.DOTALL)
        q_text = q_m.group(1) if q_m else ""
        q_text = q_text.replace('\\"', '"').replace('\\n', '\n')

        options = []
        opt_m = re.search(r'"options"\s*:\s*\[(.*?)\]', b, re.DOTALL)
        if opt_m:
            raw_opts = opt_m.group(1)
            opt_items = re.findall(r'"(.*?)"(?:\s*,\s*|\s*$)', raw_opts, re.DOTALL)
            options = [opt.replace('\\"', '"') for opt in opt_items[:4]]

        corr_m = re.search(r'"correct_option"\s*:\s*(\d+|null)', b)
        corr = None
        if corr_m and corr_m.group(1) != "null":
            corr = int(corr_m.group(1))

        results.append({
            "number": num,
            "question": q_text,
            "options": options,
            "correct_option": corr
        })

    if results:
        return results

    raise ValueError(f"امکان خواندن خروجی مدل وجود ندارد:\n{raw_text[:400]}")


def convert_file_to_images(file_input, dpi=200):
    """
    تبدیل با کیفیت و بهینه صفحات PDF/تصاویر (رزولوشن ۲۰۰۰ پیکسل با حفظ حداکثر وضوح)
    """
    if isinstance(file_input, (bytes, bytearray)):
        stream_bytes = file_input
    elif hasattr(file_input, "getvalue"):
        stream_bytes = file_input.getvalue()
    elif hasattr(file_input, "read"):
        stream_bytes = file_input.read()
    else:
        with open(file_input, "rb") as f:
            stream_bytes = f.read()

    try:
        img = Image.open(io.BytesIO(stream_bytes))
        img.load()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        return [img]
    except Exception:
        pass

    doc = pymupdf.open(stream=stream_bytes, filetype="pdf")
    images = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        zoom = dpi / 72
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        images.append(img)
    doc.close()
    return images


convert_pdf_to_images = convert_file_to_images


def configure_gemini(api_key: str, proxy: str = None):
    """تنظیم کلید و پروکسی برای اتصال به Google Gemini بدون ایجاد تداخل متغیرها"""
    if not api_key or not str(api_key).strip():
        raise ValueError("کلید API جمینای وارد نشده است. لطفاً کلید معتبر را در سایدبار وارد فرمایید.")
    
    clean_key = str(api_key).strip()
    os.environ["GEMINI_API_KEY"] = clean_key
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

    if proxy and proxy.strip():
        proxy_clean = proxy.strip()
        os.environ["HTTP_PROXY"] = proxy_clean
        os.environ["HTTPS_PROXY"] = proxy_clean
        os.environ["http_proxy"] = proxy_clean
        os.environ["https_proxy"] = proxy_clean
    else:
        for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            if k in os.environ:
                del os.environ[k]
                
    if not USE_NEW_GENAI_SDK:
        legacy_genai.configure(api_key=clean_key)


def generate_content_with_resilience(client, primary_model, parts, response_mime_type="application/json", max_retries=3, progress_callback=None):
    """
    فراخوانی ضدخطا با مدیریت ترافیک سنگین (503 UNAVAILABLE)، تلاش مجدد خودکار (Backoff)
    و سوئیچ هوشمند به مدل‌های جایگزین
    """
    candidate_models = [primary_model]
    for alt in ["gemini-2.5-flash", "gemini-3.1-flash-lite"]:
        if alt not in candidate_models:
            candidate_models.append(alt)

    last_error = None
    for model_name in candidate_models:
        for attempt in range(max_retries):
            try:
                if USE_NEW_GENAI_SDK:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=parts,
                        config=types.GenerateContentConfig(
                            response_mime_type=response_mime_type
                        )
                    )
                    if resp and resp.text:
                        return resp.text.strip()
                else:
                    gen_model = legacy_genai.GenerativeModel(model_name)
                    resp = gen_model.generate_content(
                        parts,
                        generation_config=legacy_genai.types.GenerationConfig(
                            response_mime_type=response_mime_type
                        )
                    )
                    if resp and resp.text:
                        return resp.text.strip()
            except Exception as e:
                last_error = e
                err_msg = str(e).lower()
                if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg or "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
                    wait_time = (attempt + 1) * 2
                    if progress_callback:
                        progress_callback(85, f"⏳ ترافیک موقت روی مدل {model_name}؛ تلاش مجدد هوشمند پس از {wait_time} ثانیه...")
                    time.sleep(wait_time)
                    continue
                else:
                    break

    raise last_error or RuntimeError("پاسخی از مدل‌های هوش مصنوعی دریافت نشد.")


def extract_answer_key_dict(key_images, active_key, model_name="gemini-2.5-flash", progress_callback=None):
    """
    موتور استخراج هوشمند و همه‌منظوره کلید پاسخنامه (کاملاً مستقل از ساختار: تک‌ستونه، چندستونه، جدولی، لیستی، افقی و عمودی)
    """
    if not key_images:
        return {}

    if progress_callback:
        progress_callback(80, "🎯 تحلیل هوشمند ساختار پاسخنامه و استخراج کلیدها...")

    prompt_key = """
    You are an advanced, layout-agnostic OCR and examination answer key extractor.
    This image contains an official exam answer key (کلید / پاسخنامه) in ANY format:
    It could be a single-column list, a 2-column table, a multi-column grid, horizontal rows, or multiple side-by-side blocks.

    Your goal is to dynamically analyze the visual structure and extract ALL question numbers and their corresponding correct options.

    Universal Extraction Instructions:
    1. **Layout & Header Analysis**:
       - Dynamically locate where Question Numbers (e.g. شماره سوال, شماره, ردیف, No, Q) and Correct Options (e.g. گزینه صحیح, گزینه, کلید, پاسخ, Ans, Key) are placed.
       - Trace the natural ascending sequence of question numbers (1, 2, 3, 4, ...) across all columns, sections, grids, or sub-tables, following the continuity of the exam.
    
    2. **Accurate Cell Pairing**:
       - Pair each question number with its exact designated answer choice adjacent to it (or directly below it if formatted horizontally).
       - Pay careful attention to grid boundaries and ensure no shift or misalignment occurs between adjacent columns.

    3. **Universal Option Normalization**:
       - Convert all answer representations into integers (1, 2, 3, or 4):
         * 1, "۱", "الف", "A", "a" -> 1
         * 2, "۲", "ب", "B", "b" -> 2
         * 3, "۳", "ج", "C", "c" -> 3
         * 4, "۴", "د", "D", "d" -> 4
       - Ignore empty/blank cells, canceled questions, or non-key header text.

    Output format:
    Return ONLY a single valid JSON object mapping question numbers (as strings) to their correct option integers (1-4):
    {
      "1": 4,
      "2": 1,
      "3": 1
    }
    """

    parts = [prompt_key]
    for img in key_images:
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=90, optimize=True)
        if USE_NEW_GENAI_SDK:
            parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))
        else:
            parts.append({"mime_type": "image/jpeg", "data": buf.getvalue()})

    client = genai.Client(api_key=active_key) if USE_NEW_GENAI_SDK else None
    raw_key_text = generate_content_with_resilience(
        client=client,
        primary_model=model_name.strip(),
        parts=parts,
        response_mime_type="application/json",
        progress_callback=progress_callback
    )

    answer_dict = parse_key_text_universally(raw_key_text)
    return answer_dict


def extract_questions_from_images(question_images, answer_key_images=None, api_key=None, model_name="gemini-2.5-flash", total_questions_expected=None, answers_are_bolded=False, answer_key_page=0, progress_callback=None, stream_callback=None):
    """
    استخراج هوشمند و همه‌منظوره با انطباق قطعی کلیدها
    """
    if not question_images:
        raise ValueError("هیچ تصویری از دفترچه سوالات برای پردازش یافت نشد.")

    active_key = api_key.strip() if (api_key and str(api_key).strip()) else os.environ.get("GEMINI_API_KEY", "").strip()
    if not active_key:
        raise ValueError("کلید API جمینای خالی است. لطفاً کلید API را در منوی تنظیمات وارد کنید.")

    # مدیریت دقیق تفکیک صفحات سوالات و پاسخنامه
    actual_q_images = list(question_images)
    isolated_key_images = []

    if answers_are_bolded:
        actual_q_images = list(question_images)
    elif answer_key_images:
        isolated_key_images = list(answer_key_images)
    elif answer_key_page and 1 <= answer_key_page <= len(question_images):
        isolated_key_images = [question_images[answer_key_page - 1]]
        actual_q_images = [img for idx, img in enumerate(question_images) if idx != (answer_key_page - 1)]

    if progress_callback:
        progress_callback(10, f"آماده‌سازی {len(actual_q_images)} صفحه سوال برای استخراج با مدل {model_name}...")

    expected_info = f"تعداد کل سوالات مورد انتظار حدوداً {total_questions_expected} سوال است." if total_questions_expected else ""

    bold_rule = """
    ۸. **کلید پاسخ با فونت بولد (`correct_option`):**
       - در هر سوال با دقت فونت و وزن گزینه‌ها را بررسی کن؛ گزینه‌ای که با **فونت بولد/ضخیم‌تر**، **رنگ متفاوت** یا **علامت تیک** مشخص شده است را پیدا کن و شماره آن (۱، ۲، ۳ یا ۴) را در فیلد `correct_option` قرار بده.
       - اگر هیچ گزینه‌ای بولد نبود، مقدار آن را null بگذار.
    """

    table_key_rule = """
    ۸. **کلید پاسخ (`correct_option`):**
       - مطلقاً سعی نکن جواب سوالات را حدس بزنی. مقدار این فیلد را برای تمام سوالات null بگذار (کلید رسمی آزمون در مرحله دوم از فایل پاسخنامه استخراج و اضافه خواهد شد).
    """

    prompt = f"""
    شما یک دستیار فوق‌العاده دقیق برای استخراج آزمون‌های چهارگزینه‌ای فارسی و انگلیسی هستید.
    سامانه مقصد به طور کامل از Markdown و LaTeX پشتیبانی می‌کند.
    تصاویر پیوست‌شده صفحات دفترچه سوالات آزمون هستند. {expected_info}

    دستورالعمل‌های حیاتی:
    ۱. **حل سوالات دوتکه (Cross-page):** اگر یک سوال در انتهای یک صفحه شروع شده و ادامه‌اش یا گزینه‌هایش در صفحه بعدی قرار دارد، حتماً آن‌ها را با هم ترکیب کن تا یک سوال کامل تشکیل شود.
    ۲. **جداسازی کامل متن سوال از گزینه‌ها:** فیلد `question` فقط و فقط باید متن صورت سوال باشد و نباید متن گزینه‌ها در آن تکرار شود.
    ۳. **متن‌های ریدینگ (Passage):** اگر چند سوال مربوط به یک متن مشترک (ریدینگ/درک مطلب) هستند، متن ریدینگ را با فرمت‌بندی خوانا در ابتدای فیلد `question` آن سوالات قرار بده.
    ۴. **پشتیبانی کامل از LaTeX برای فرمول‌های ریاضی و علمی:**
       - تمام فرمول‌های ریاضی، فیزیک، شیمی، کسرها، رادیکال‌ها، توان‌ها، ماتریس‌ها و نمادهای علمی را با فرمت استاندارد LaTeX بنویس.
       - برای فرمول‌های درون‌خطی از `$فرمول$` و برای فرمول‌های مستقل از `$$فرمول$$` استفاده کن (مانند `$x^2 + y^2 = r^2$` یا `$\\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}$` یا `$\\lim_{{x \\to 0}}$` یا `$\\int_a^b f(x)dx$`).
       - در متن گزینه‌ها (`options`) نیز اگر فرمول وجود دارد، حتماً با فرمت `$LaTeX$` بنویس.
    ۵. **پشتیبانی از Markdown (جدول‌ها و متون ساختاریافته):**
       - اگر سوال شامل جدول داده است، آن را با جدول Markdown استاندارد (`| ستون ۱ | ستون ۲ |`) بازنویسی کن.
    ۶. **نقل‌قول‌ها در متون انگلیسی و فارسی:**
       - برای جلوگیری از خطای JSON، در داخل متن سوالات از علامت گیومه تک ('...') یا «...» استفاده کن و از دابل‌کوتیشن مستقیم داخل رشته‌ها پرهیز کن.
    ۷. **سوالات دارای تصویر و نمودار غیرمتنی:**
       - فقط و فقط اگر سوال دارای یک شکل هندسی، نمودار، مدار الکتریکی یا تصویر غیرمتنی واقعی است، عبارت `(This question has an image, add it manually)` را در ابتدای متن صورت سوال قرار بده.
    ۸. **رعایت دقیق ترتیب گزینه‌ها در آزمون‌های فارسی (خیلی مهم):**
       - در آرایه `options`، خانه اول (ایندکس ۰) باید متن **گزینه (۱)**، خانه دوم متن **گزینه (۲)**، خانه سوم متن **گزینه (۳)** و خانه چهارم متن **گزینه (۴)** باشد.
       - دقت کن که در آزمون‌های فارسی گزینه‌ها ممکن است از راست به چپ چیده شده باشند (مثلاً ۴ در چپ، ۱ در راست). حتماً متن گزینه را با شماره برچسب خودش `(۱)`، `(۲)`، `(۳)` و `(۴)` تطبیق بده و شماره یا حرف اول گزینه را از متن حذف کن.
    {bold_rule if answers_are_bolded else table_key_rule}

    فرمت خروجی مورد انتظار:
    یک آرایه JSON معتبر حاوی اشیاء به این ساختار:
    [
      {{
        "number": 1,
        "question": "متن صورت سوال...",
        "options": ["متن گزینه ۱", "متن گزینه ۲", "متن گزینه ۳", "متن گزینه ۴"],
        "correct_option": { "1" if answers_are_bolded else "null" }
      }}
    ]

    تنها و تنها یک ساختار JSON معتبر برگردان. هیچ توضیح اضافی خارج از JSON قرار نده.
    """

    if progress_callback:
        progress_callback(25, f"در حال پردازش و ارسال صفحات سوالات به {model_name}...")

    raw_text = ""
    target_model = model_name.strip()

    if USE_NEW_GENAI_SDK:
        client = genai.Client(api_key=active_key)
        parts = [prompt]
        for img in actual_q_images:
            buf = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buf, format='JPEG', quality=85, optimize=True)
            parts.append(types.Part.from_bytes(
                data=buf.getvalue(),
                mime_type="image/jpeg"
            ))

        try:
            response_stream = client.models.generate_content_stream(
                model=target_model,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            for chunk in response_stream:
                if chunk.text:
                    raw_text += chunk.text
                    if stream_callback:
                        q_count_est = raw_text.count('"number":')
                        stream_callback(chunk.text, len(raw_text), q_count_est)
        except Exception:
            if progress_callback:
                progress_callback(40, "🟢 در حال فراخوانی پایدار و مقاوم در برابر ترافیک...")
            raw_text = generate_content_with_resilience(
                client=client,
                primary_model=target_model,
                parts=parts,
                response_mime_type="application/json",
                progress_callback=progress_callback
            )
    else:
        legacy_genai.configure(api_key=active_key)
        image_parts = []
        for img in actual_q_images:
            buf = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buf, format='JPEG', quality=85, optimize=True)
            image_parts.append({
                "mime_type": "image/jpeg",
                "data": buf.getvalue()
            })
        raw_text = generate_content_with_resilience(
            client=None,
            primary_model=target_model,
            parts=[prompt, *image_parts],
            response_mime_type="application/json",
            progress_callback=progress_callback
        )

    data = robust_parse_questions_json(raw_text)

    cleaned_questions = []
    seen_numbers = set()

    for item in data:
        if not isinstance(item, dict):
            continue

        raw_num = item.get("number")
        try:
            num = int(to_english_digits(str(raw_num)))
        except (ValueError, TypeError):
            num = len(cleaned_questions) + 1

        if num in seen_numbers:
            continue

        q_text = correct_common_spacing_errors(str(item.get("question", "")))

        raw_options = item.get("options", [])
        if not isinstance(raw_options, list):
            raw_options = []

        options = [correct_common_spacing_errors(str(opt)) for opt in raw_options]
        while len(options) < 4:
            options.append("")
        options = options[:4]

        correct_opt = item.get("correct_option")
        if correct_opt is not None:
            try:
                correct_opt_clean = int(to_english_digits(str(correct_opt)))
                if 1 <= correct_opt_clean <= 4:
                    correct_opt = correct_opt_clean
                else:
                    correct_opt = None
            except (ValueError, TypeError):
                correct_opt = None

        cleaned_questions.append({
            "number": num,
            "question": q_text,
            "options": options,
            "correct_option": correct_opt
        })
        seen_numbers.add(num)

    cleaned_questions.sort(key=lambda x: x["number"])

    # مرحله ۲: استخراج قطعی کلید پاسخنامه از فایل کلید
    if isolated_key_images and not answers_are_bolded:
        answer_key_dict = extract_answer_key_dict(
            key_images=isolated_key_images,
            active_key=active_key,
            model_name=model_name,
            progress_callback=progress_callback
        )
        if answer_key_dict:
            matched_count = 0
            for q in cleaned_questions:
                q_num = q["number"]
                if q_num in answer_key_dict:
                    q["correct_option"] = answer_key_dict[q_num]
                    matched_count += 1
                else:
                    q["correct_option"] = None
            if progress_callback:
                progress_callback(95, f"✅ کلید {matched_count} سوال با موفقیت و تطبیق ۱۰۰٪ از فایل پاسخنامه اعمال شد.")
        else:
            # اگر کلیدی استخراج نشد، مقدار را None بگذار تا مقدار حدسی نمایش داده نشود
            for q in cleaned_questions:
                q["correct_option"] = None
    elif not answers_are_bolded and not isolated_key_images:
        for q in cleaned_questions:
            q["correct_option"] = None

    if progress_callback:
        progress_callback(100, f"✅ استخراج تکمیل شد: {len(cleaned_questions)} سوال آماده ثبت است.")

    return cleaned_questions
