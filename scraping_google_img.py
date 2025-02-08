import os
import sys
import time
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image
from io import BytesIO

# コマンドライン引数の処理
parser = argparse.ArgumentParser(description="Google画像検索スクレイピングツール")
parser.add_argument("-k", "--keyword", type=str, help="検索キーワード")
parser.add_argument("-u", "--url", type=str, help="URL")
parser.add_argument("-n", "--num", type=int, default=10, help="取得する画像の最大枚数（デフォルト10）")
args = parser.parse_args()

# オプションを指定していない場合は、エラーを出力
if not args.keyword and not args.url:
    print("❌ エラー: 検索キーワード または `-u <URL>` のどちらかを指定してください。", file=sys.stderr)
    sys.exit(1)


# URLを指定する場合
if args.url:
    print(f"🔍 Downloading image from URL: {args.url}")
    search_url = f"{args.url}"
    timestamp = int(time.time() * 1000)
    folder_path = os.path.expanduser(f"./URL_{timestamp}/")
# キーワードで検索する場合
elif args.keyword:
    print(f"🔍 Searching images for keyword: {args.keyword}")
    search_url = f"https://www.google.com/search?tbm=isch&q={args.keyword}"
    folder_path = os.path.expanduser(f"./{args.keyword}/")

# 画像をダウンロードフォルダを作成
os.makedirs(folder_path, exist_ok=True)



# Chromeドライバを呼び出す
driver = webdriver.Chrome()
# Google画像検索のURL
driver.get(search_url)

# ページをスクロールして多くの画像を取得
for _ in range(5):  # 5回スクロール（調整可能）
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
    time.sleep(2)  # 読み込み待ち

# 「もっと見る」ボタンがあればクリック
try:
    more_button = driver.find_element(By.CSS_SELECTOR, ".mye4qd")  # ボタンのクラス
    more_button.click()
    time.sleep(2)
except:
    print("🔹 'もっと見る' ボタンなし")

# 画像要素を取得
image_elements = driver.find_elements(By.CSS_SELECTOR, "img")
# 画像URLを取得（http/https のみ）
image_urls = [img.get_attribute("src") for img in image_elements if img.get_attribute("src") and img.get_attribute("src").startswith("http")]



# 画像をダウンロードして保存
download_count = 0
for i, url in enumerate(image_urls):
    if download_count >= args.num:
        break  # 指定した最大数を超えたら終了

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # 🔹 **画像の `Content-Type` を確認**
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            print(f"❌ Skipping (Not an image): {url}")
            continue

        # 画像データを開く
        image = Image.open(BytesIO(response.content))
        file_extension = image.format.lower()  # jpg, png などを取得
        timestamp = int(time.time() * 1000)
        file_path = os.path.join(folder_path, f"img_{timestamp}.{file_extension}")

        # 画像を保存
        image.save(file_path)
        print(f"✅ Saved: {file_path}")

        download_count += 1

    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading {url}: {e}")
    except Image.UnidentifiedImageError:
        print(f"❌ Skipping (Invalid image file): {url}")

# 終了
driver.quit()

print(f"\n🎉 {download_count} images downloaded successfully!")