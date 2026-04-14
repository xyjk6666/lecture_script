import requests
import ddddocr
import time
import datetime
import base64
import json

#配置cookie和讲座id，时间
COOKIE = ""
WID = ""
TARGET_TIME = datetime.datetime(2026, 4, 14, 18, 59, 59,950000)


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


def auto_task_flow():
    ocr = ddddocr.DdddOcr(show_ad=False)
    session = requests.Session()
    session.headers.update(HEADERS)

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

    count = 10
    while count>0:
        count = count - 1
        """
        print("[1/3]发送状态校验请求...")
        try:
            check_payload = {"wid": WID}
            first_resp=session.post(CHECK_URL, data=check_payload, timeout=10)
            first_json=first_resp.json()
            if first_json.get("success") == True:
                print("状态校验成功")
            else:
                print("状态校验失败")
        except Exception as e:
            print(f"校验请求异常 (可忽略): {e}")
            continue
        """
        print("[2/3] 获取并识别验证码...")
        captcha_text = ""
        try:
            vcode_payload = {"_": int(time.time() * 1000)}
            vcode_resp = session.post(VCODE_URL, data=vcode_payload, timeout=8)
            resp_json = vcode_resp.json()
            if resp_json.get("success") == True:
                full_base64_str = resp_json.get("result")
                clean_base64 = full_base64_str.split(",")[1]
                img_bytes = base64.b64decode(clean_base64)
                captcha_text = ocr.classification(img_bytes)
                print(f"OCR 识别结果: {captcha_text}")
            else:
                print("获取验证码失败，服务器返回了不成功的状态。")
                continue
        except Exception as e:
            print(f"获取验证码失败: {e}")
            continue
        print("[3/3] 发送最终保存请求...")
        inner_data = {
            "HD_WID": WID,
            "vcode": captcha_text
        }
        save_payload = {
            "paramJson": json.dumps(inner_data)
        }
        try:
            final_resp = session.post(SAVE_URL, data=save_payload, timeout=10)
            if not final_resp.text.strip():
                print("报错")
                continue
            final_json = final_resp.json()
            if final_json.get("code") == 200 and final_json.get("success") == True:
                print("服务器返回成功，预约已锁定！")
                break
            else:
                print(f"预约未能成功，服务器返回: {final_json}")
        except Exception as e:
            print(f"最终提交异常: {e}")


if __name__ == "__main__":
    auto_task_flow()