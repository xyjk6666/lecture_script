import threading

import requests
import ddddocr
import time
import datetime
import base64
import json

#配置cookie和讲座id，时间
COOKIE = ""
WID = ""
TARGET_TIME = datetime.datetime(2026, 4, 14, 19, 0, 0)
THREAD_COUNT = 3


BASE_URL = "https://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy"
#CHECK_URL = f"{BASE_URL}/appiontCheck.do"
VCODE_URL = f"{BASE_URL}/vcode.do"
SAVE_URL = f"{BASE_URL}/yySave.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Cookie": COOKIE,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

is_success = False
ocr = ddddocr.DdddOcr(show_ad=False)
start_gun = threading.Event()

def single_task_flow(thread_id):
    global is_success
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"[线程 {thread_id}] 已在起跑线就位，等待发令枪...")
    start_gun.wait()

    count = 10
    while count > 0 and not is_success:
        count -= 1
        print(f"[线程 {thread_id}] 发起第 {10 - count} 次冲击...")
        #获取验证码
        captcha_text = ""
        try:
            vcode_payload = {"_": int(time.time() * 1000)}
            vcode_resp = session.post(VCODE_URL, data=vcode_payload, timeout=8)
            resp_json = vcode_resp.json()
            if resp_json.get("success") == True:
                clean_base64 = resp_json.get("result").split(",")[1]
                img_bytes = base64.b64decode(clean_base64)
                captcha_text = ocr.classification(img_bytes)
                print(f"[线程 {thread_id}] OCR 识别结果: {captcha_text}")
            else:
                continue
        except Exception as e:
            continue

        #发送最终保存请求
        inner_data = {
            "HD_WID": WID,
            "vcode": captcha_text
        }
        save_payload = {"paramJson": json.dumps(inner_data)}

        try:
            final_resp = session.post(SAVE_URL, data=save_payload, timeout=10)
            if not final_resp.text.strip():
                continue
            final_json = final_resp.json()
            if final_json.get("code") == 200 and final_json.get("success") == True:
                print(f"[线程 {thread_id}] 服务器返回成功，预约已锁定！")
                is_success = True
                break
            else:
                print(f"[线程 {thread_id}] 预约未成功: {final_json}")
        except Exception as e:
            continue


def main():
    print(f"脚本已启动，等待到达设定时间: {TARGET_TIME}")

    threads = []
    for i in range(THREAD_COUNT):
        t = threading.Thread(target=single_task_flow, args=(i + 1,))
        threads.append(t)
        t.start()

    while True:
        now = datetime.datetime.now()
        delta = (TARGET_TIME - now).total_seconds()
        if delta <= 0:
            print(f"时间到，当前时间: {now.strftime('%H:%M:%S.%f')}，开始抢！")
            start_gun.set()
            break
        elif delta > 1:
            time.sleep(0.5)
        elif delta > 0.1:
            time.sleep(0.01)
        else:
            pass


    for t in threads:
        t.join()


if __name__ == "__main__":
    main()