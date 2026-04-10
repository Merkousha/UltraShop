Product Requirement Document (PRD): UltraShop Next-Gen
Project Name: UltraShop (Smart SaaS E-commerce Builder)

Version: 2.0 (Hybrid Phase)

Target: AI-Driven Multi-Tenant Platform

۱. چشم‌انداز محصول (Product Vision)
تبدیل یک فروشگاه‌ساز سنتی به یک "سیستم فروش خودکار" که با استفاده از هوش مصنوعی، فرآیند تامین کالا (Multi-Warehouse)، تولید محتوا (Vision AI) و مدیریت فروش (CRM & Funnel) را یکپارچه می‌کند.

۲. معماری سیستم و محدودیت‌های فنی (System Architecture)
Framework: Django (Python)

Multi-tenancy: استراتژی Database-per-Tenant (ساخت دیتابیس مستقل در زمان ثبت‌نام).

Isolation: تفکیک منطقی داده‌ها در سطح اپلیکیشن؛ استفاده از tenant_id برای مسیریابی دیتابیس.

Infrastructure: استفاده از Wildcard Subdomains برای جداسازی فروشگاه‌ها (اجتناب از پیچیدگی DevOps دامین اختصاصی در فاز فعلی).

AI Integration: متصل به OpenAI/Anthropic برای پردازش تصویر و ایجنت‌های فروش.

۳. فازبندی توسعه (Development Roadmap)
فاز ۱: زیرساخت Multi-tenant و پایداری (The Foundation)
هدف: نهایی کردن هسته مرکزی و سیستم جداسازی مشتریان.

Dynamic DB Provisioning: پیاده‌سازی سیستمی که با ثبت‌نام کاربر، دیتابیس جدید ساخته و migrations را روی آن اجرا کند.

RBAC (سطوح دسترسی): تعریف نقش‌های Super Admin، Store Owner، Sales Agent، و Accountant.

Checkout Logic Fix: اصلاح منطق سبد خرید جهت وابستگی به وضعیت shipping_enabled محصول.

Plan Limitation: پیاده‌سازی سیستم محدودیت پلن (مثلاً تعداد انبار یا حجم آپلود AI).

فاز ۲: موتور CRM و قیف فروش (Business Engine)
هدف: ایجاد مزیت رقابتی بر اساس خواسته کارفرما.

Lead Management: ثبت خودکار سرنخ‌ها از چت و فرم‌های تماس.

Sales Funnel: پیاده‌سازی بورد کانبان برای مراحل فروش (Lead -> Negotiation -> Won/Lost).

Task System: سیستم یادآوری وظایف و تسک‌های پیگیری برای اپراتورهای فروش.

Contact History: لاگ تمام تعاملات مشتری (خریدها، چت‌ها، تیکت‌ها) در یک پروفایل واحد.

فاز ۳: ایجنت هوشمند و اتوماسیون (AI Sales Agent)
هدف: فعال‌سازی قابلیت‌های هوشمند برای کاربر نهایی.

AI Chat Agent: چت‌بات متصل به دیتابیس محصولات (KAG/RAG) جهت پاسخگویی به مشتری و پیشنهاد محصول.

Vision-to-Listing Enhancement: بهبود قابلیت فعلی (SO-16) با افزودن Progress Indicator و غنی‌سازی خودکار متادیتای محصول.

Abandoned Cart Recovery: ارسال خودکار پیامک/ایمیل حاوی کد تخفیف برای سبدهای رها شده.

فاز ۴: لجستیک و تحلیل داده (Advanced Growth)
هدف: بهینه‌سازی عملیات در مقیاس بالا.

Smart Routing (SO-52): تخصیص هوشمند سفارش به نزدیک‌ترین انبار بر اساس موجودی.

BI Dashboard: نمایش KPIهای حیاتی (LTV, CAC, Conversion Rate) به مدیر فروشگاه.

External Integrations: اتصال به API پست، سامانه مودیان و درگاه‌های پرداخت بانکی.

۴. نیازمندی‌های غیرعملیاتی (Non-Functional Requirements)
Scalability: هر دیتابیس مشتری باید قابلیت انتقال به سرور مجزا را داشته باشد.

Security: رمزنگاری کلیدهای API (SMS/Email) در تنظیمات پلتفرم.

UX/Accessibility: رعایت استانداردهای WCAG در تم‌های تولید شده توسط Theme Engine.

۵. دستورالعمل برای AI Agents (Instructions)
در هنگام تولید کد برای هر ماژول، ابتدا وجود tenant_context را چک کنید.

تمام مدل‌های جدید (مانند Lead یا SaleTask) باید در اپلیکیشن crm تعریف شده و به دیتابیس اختصاصی هر Tenant متصل باشند.

برای بخش AI، از Rate Limiting تعریف شده در PlatformSettings استفاده کنید تا هزینه‌ها کنترل شود.

توجه: این PRD مبنای عمل برای تمام اسپرینت‌های آتی است. هرگونه تغییر در مدل‌های دیتابیس باید با در نظر گرفتن ساختار Multi-tenant انجام شود.