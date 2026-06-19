import os
import sys
import subprocess

# --- ۱. بررسی و نصب خودکار کتابخانه‌های پیش‌نیاز سیستم ---
def install_dependencies():
    required_libs = ["openai", "rich"]
    missing_libs = []
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        print(f"کتابخانه‌های مورد نیاز یافت نشدند. در حال نصب: {missing_libs}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs])
            print("کتابخانه‌ها با موفقیت نصب شدند!\n")
        except Exception as e:
            print(f"خطا در نصب خودکار کتابخانه‌ها: {e}")
            sys.exit(1)

# اجرای بررسی و نصب پکیج‌ها پیش از شروع برنامه
install_dependencies()

# ایمپورت ابزارها پس از اطمینان از نصب
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

console = Console()

# --- ۲. تنظیمات توکن و اتصال به Hugging Face Router ---
# خواندن توکن از سیستم؛ اگر تنظیم نشده باشد از کاربر دستی می‌پرسد
Token = os.getenv("HF_TOKEN")

if not Token:
    console.print("[yellow]توکن Hugging Face در متغیرهای سیستم (Environment Variables) یافت نشد.[/yellow]")
    Token = input("لطفاً توکن Hugging Face خود را وارد کنید: ").strip()
    if not Token:
        console.print("[red]خطا: بدون توکن امکان استفاده از برنامه وجود ندارد.[/red]")
        sys.exit(1)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=Token,
)

MODEL_NAME = "zai-org/GLM-5.2"

# --- ۳. فیلتر امنیتی دستورات خطرناک ---
FORBIDDEN_COMMANDS = ["rm -rf /", "mkfs", "dd", "shutdown", "reboot", ":(){ :|:& };:"]

def is_safe(command):
    for forbidden in FORBIDDEN_COMMANDS:
        if forbidden in command:
            return False
    return True

# --- ۴. توابع ارتباط با هوش مصنوعی (OpenAI SDK) ---
def ask_hf_for_command(prompt, shell_type):
    """تبدیل متن کاربر به دستور دقیق شل"""
    system_prompt = (
        f"You are an expert system administrator. The user wants to achieve something in their {shell_type} shell. "
        "Your job is to output ONLY the exact, single command needed to achieve this. "
        "Do not include any explanations, do not use markdown code blocks or backticks. Just raw text command."
        "you are in ubuntu and debian based opration systems "
    )
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content.strip().replace("`", "")
    except Exception as e:
        console.print(f"[red]خطا در ارتباط با سرور (تولید دستور): {e}[/red]")
        return None

def ask_hf_for_summary(output):
    """خلاصه‌سازی خروجی ترمینال به زبان فارسی"""
    system_prompt = "You are a helpful Linux assistant. Summarize the following terminal output very briefly and clearly in Persian (Farsi)."
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Terminal Output:\n{output}"}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"خطا در خلاصه‌سازی: {e}"

# --- ۵. دستور راهنما ---
def show_help():
    help_text = """
    [bold cyan]راهنمای AI Shell Controller[/bold cyan]
    -----------------------------------
    • خواسته خود را به زبان ساده بنویسید (مثال: لیست پروسس‌های در حال اجرا که بیشترین رم را مصرف می‌کنند).
    • هوش مصنوعی دستور را آماده کرده و پس از تایید شما (y/n)، آن را اجرا می‌کند.
    
    [bold yellow]دستورات برنامه:[/bold yellow]
    • [green]/help[/green] : نمایش این منوی راهنما
    • [green]exit[/green]  : خروج کامل از برنامه
    """
    console.print(Panel(help_text, title="Help Menu", expand=False))

# --- ۶. جریان اصلی برنامه ---
def main():
    console.print("[bold magenta]به کنترل‌کننده هوشمند شل (نسخه سیستمی) خوش آمدید![/bold magenta]\n")
    
    # انتخاب نوع شل
    console.print("[1] Bash\n[2] Fish")
    choice = input("نوع شل را انتخاب کنید (1 یا 2): ").strip()
    shell_type = "fish" if choice == "2" else "bash"
    
    # بررسی نصب بودن شل انتخاب شده روی لینوکس/مک شما
    try:
        subprocess.run([shell_type, "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        console.print(f"[bold yellow]هشدار: شل '{shell_type}' روی سیستم شما نصب نیست یا در PATH قرار ندارد.[/bold yellow]")
    
    console.print(f"[green]شل فعال: {shell_type}[/green]\n")
    
    # انتخاب نوع خروجی
    console.print("[1] Full Output (خروجی کامل دستور ترمینال)\n[2] Summarized by AI (توضیح خلاصه خروجی به فارسی)")
    mode_choice = input("حالت نمایش خروجی را انتخاب کنید (1 یا 2): ").strip()
    output_mode = "summary" if mode_choice == "2" else "full"
    console.print(f"[green]حالت خروجی: {output_mode}[/green]\n")

    while True:
        try:
            user_prompt = input(f"AI-{shell_type} > ").strip()
            
            if not user_prompt:
                continue
            if user_prompt.lower() == "exit":
                break
            if user_prompt == "/help":
                show_help()
                continue
                
            # دریافت دستور از GLM-5.2
            with console.status("[bold blue]در حال تحلیل و تولید دستور..."):
                command = ask_hf_for_command(user_prompt, shell_type)
                
            if not command:
                continue
                
            console.print(f"\n[bold yellow]دستور پیشنهادی:[/bold yellow] {command}")
            
            # فیلتر امنیتی دستورات خطرناک
            if not is_safe(command):
                console.print("[red]✖ دستور مسدود شد! این دستور جزو موارد فیلتر شده و خطرناک سیستم است.[/red]\n")
                continue
                
            # تایید برای اجرا بر روی سیستم شما
            confirm = input("آیا این دستور اجرا شود؟ (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    # اجرای دستور در محیط شل انتخابی سیستم شما
                    result = subprocess.run(
                        [shell_type, "-c", command], 
                        capture_output=True, 
                        text=True, 
                        timeout=45
                    )
                    
                    stdout = result.stdout.strip()
                    stderr = result.stderr.strip()
                    
                    # مدیریت نحوه نمایش خروجی
                    if output_mode == "full":
                        if stdout: console.print(f"[green]خروجی استاندارد (Stdout):[/green]\n{stdout}")
                        if stderr: console.print(f"[red]خروجی خطا (Stderr):[/red]\n{stderr}")
                        if not stdout and not stderr:
                            console.print("[gray]دستور با موفقیت بدون خروجی متنی اجرا شد.[/gray]")
                    else:
                        # حالت خلاصه‌سازی خروجی به فارسی
                        combined_output = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}".strip()
                        if stdout or stderr:
                            with console.status("[bold blue]در حال خلاصه‌سازی خروجی ترمینال..."):
                                explanation = ask_hf_for_summary(combined_output)
                            console.print(f"\n[bold green]توضیح خلاصه هوش مصنوعی:[/bold green]\n{explanation}")
                        else:
                            console.print("[gray]دستور با موفقیت اجرا شد (بدون خروجی برای خلاصه‌سازی).[/gray]")
                            
                except subprocess.TimeoutExpired:
                    console.print("[red]خطا: زمان اجرای دستور بیش از حد طولانی شد (Timeout).[/red]")
                except Exception as e:
                    console.print(f"[red]خطا در اجرای سیستم: {e}[/red]")
            else:
                console.print("[gray]اجرای دستور لغو شد.[/gray]\n")
                
        except (KeyboardInterrupt, EOFError):
            print("\nخروج از برنامه...")
            break

if __name__ == "__main__":
    main()
