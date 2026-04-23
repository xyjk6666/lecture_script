import requests
import ddddocr
import time
import datetime
import base64
import json

#配置cookie和讲座id，时间，次数
COOKIE = ""
WIDS = [""]
TARGET_TIME = datetime.datetime(2026, 4, 23, 18, 59, 59,980000)
Count=20

#进入的网页
#https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/*default/index.do#/hdyy

logs=[]

BASE_URL = "https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/modules/hdyy"
#CHECK_URL = f"{BASE_URL}/appiontCheck.do"
VCODE_URL = f"{BASE_URL}/vcode.do"
SAVE_URL = f"{BASE_URL}/addReservation.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Cookie": COOKIE,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Origin": "https://ehall.seu.edu.cn",
    "Referer": "https://ehall.seu.edu.cn/gsapp/sys/yddjzxxtjappseu/index.html",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}


def auto_task_flow():
    ocr = ddddocr.DdddOcr(show_ad=False)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.trust_env = False
    print(f"脚本已启动，等待到达设定时间: {TARGET_TIME}")
    while True:
        now = datetime.datetime.now()
        delta = (TARGET_TIME - now).total_seconds()
        if delta <= 0:
            print(f"时间到，当前时间: {now.strftime('%H:%M:%S.%f')}，开始抢！")
            break
        elif delta > 1:
            time.sleep(0.5)
        elif delta > 0.1:
            time.sleep(0.01)
        else:
            pass

    for wid in WIDS:
        logs.append(f"抢wid{wid}")
        count = 0
        while count<Count:
            count += 1
            logs.append(f"第{count}次：获取并识别验证码...")
            captcha_text = ""
            try:
                vcode_resp = session.get(VCODE_URL, params={'_': int(time.time() * 1000)}, timeout=5)
                resp_json = vcode_resp.json()
                full_base64 = resp_json.get('datas', "")
                if "base64," in full_base64:
                    clean_base64 = full_base64.split("base64,")[1]
                    img_bytes = base64.b64decode(clean_base64)
                    captcha_text = ocr.classification(img_bytes)
                else:
                    logs.append(f"验证码接口未返回成功状态{vcode_resp.text}")
                    continue
            except Exception as e:
                logs.append(f"获取验证码失败: {e}")
                continue
            logs.append(f"验证码识别结果{captcha_text}")
            if len(captcha_text) != 4 or not captcha_text.isdigit():
                logs.append("验证码识别明显有误，重新获取...")
                continue

            #发送最终保存请求
            save_payload = {
                "wid": wid,
                "vcode": captcha_text
            }
            final_resp=None
            try:
                final_resp = session.post(SAVE_URL, data=save_payload, timeout=8)
                if not final_resp.text.strip():
                    logs.append(f"报错{final_resp}")
                    continue
                final_json = final_resp.json()
                if final_json.get("code") == 0 and final_json.get("datas") == 1:
                    logs.append("服务器返回成功，预约已锁定！")
                    break
                else:
                    logs.append(f"预约未能成功，服务器返回: {final_json}")
            except Exception as e:
                logs.append(f"最终提交异常: {e}")
                if final_resp is not None:
                    logs.append(f"final_resp:{final_resp.text[:200]}")

    for log in logs:
        print(log)


if __name__ == "__main__":
    auto_task_flow()