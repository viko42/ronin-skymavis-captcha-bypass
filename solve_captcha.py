import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64
import json
from PIL import Image, ImageDraw
import sys
import os
import io
import uuid
from datetime import datetime

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# App key of the app
APP_KEY = '5a0eb357-db13-4911-a810-c1914c17bc6f'

proxies = {
    'http': "--your-proxy-url--",
    'https': "--your-proxy-url--",
}

def get_token_from_captcha(url, id, result):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,id;q=0.6,th;q=0.5',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://accounts.skymavis.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://accounts.skymavis.com/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    json_data = {
        'app_key': APP_KEY,
        'id': id,
        'result': result,
    }
    
    response = requests.post(url, headers=headers, json=json_data, verify=False, proxies=proxies)
    if response.status_code != 200:
        print(f"Error getting image: {response.status_code}")
        return None
    
    data = response.json()
    token = data.get("token")
    return token


def get_image_from_api(url):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,id;q=0.6,th;q=0.5',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://accounts.skymavis.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://accounts.skymavis.com/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    json_data = {
        'app_key': APP_KEY,
        'context': 'login',
    }
    print(f"Captcha logs", json_data)
    response = requests.post(url, headers=headers, json=json_data, verify=False, proxies=proxies)
    print(f"Error", response.status_code)
    
    if response.status_code != 200:
        print(f"Error getting image: {response.status_code}")
        return None
    
    data = response.json()
    return data.get("image"), data.get("id")

def save_base64_image(base64_string, output_path):
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)

def check_points(image_paths, points_sets, output_prefix):
    for image_path in image_paths:
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Le fichier {image_path} est introuvable.")
            continue

        angle = int(image_path.split('/')[-1].split('_')[0])

        image = image.convert("RGBA")
        width, height = image.size
        
        debug_image = image.copy()
        draw = ImageDraw.Draw(debug_image)

        all_rules_passed = True  # Flag to check if all rules pass for this image
        for i, points in enumerate(points_sets):
            all_points_passed = True
            print(f"Checking rules {i + 1} for image {angle}:")
            for (x, y) in points:
                if x < 0 or x >= width or y < 0 or y >= height:
                    print(f"Point ({x}, {y}) outside the image")
                    all_rules_passed = False
                    all_points_passed = False
                    break

                pixel = image.getpixel((x, y))
                if pixel[3] == 0:
                    print(f"Transparent pixel at ({x}, {y}).")
                    draw.point((x, y), fill="blue")
                else:
                    print(f"No transparent pixel at ({x}, {y}).")
                    draw.point((x, y), fill="green")
                    all_rules_passed = False
                    all_points_passed = False
                    break
            
            if all_points_passed:
                # debug_image.save(f"{output_prefix}_debug_{image_number}.{i}.png")
                return angle
            print()
        # Optionally, save the debug image
        # debug_image.save(f"{output_prefix}/debug_{image_number}.{i}.png")
    return -1  # Return False if no image passed all rules
    
def rotate_and_save_image(image_path, output_folder, run_id, step=30):
    try:
        image = Image.open(image_path)
    except FileNotFoundError:
        print(f"Le fichier {image_path} est introuvable.")
        return
    os.makedirs(output_folder, exist_ok=True)

    for angle in range(0, 360, step):
        image_rotated = image.rotate(angle, resample=Image.BICUBIC, expand=False)
        output_path = os.path.join(output_folder, f"{angle}_{run_id}.png")
        image_rotated.save(output_path)

def cleanup_files(input_image, rotated_images):
    try:
        os.remove(input_image)
        for img in rotated_images:
            os.remove(img)
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]

    get_image_url = "https://x.skymavis.com/captcha-srv/check"
    submit_result_url = "https://x.skymavis.com/captcha-srv/submit"

    base64_image, image_id = get_image_from_api(get_image_url)
    if not base64_image:
        return
    
    input_image_path = f"axies_captcha/input_image_{run_id}.png"
    save_base64_image(base64_image, input_image_path)

    points_sets = [
        [(260,131), (251,216)],
        [(147,222), (110,209),(93,187),(87,148), (208,219), (170,75), (182,221)],
        # [(139,218), (116,209),(93,187),(87,148), (203,219), (155,75)],
    ]
    output_prefix = f"debug_{run_id}"
    
    rotate_and_save_image(input_image_path, 'axies_captcha_rotated', run_id)
    
    image_paths = [f"axies_captcha_rotated/{angle}_{run_id}.png" for angle in range(0, 360, 30)]

    result = check_points(image_paths, points_sets, output_prefix)
 
    if result >= 0:
        print(f"The function returned degree: {result}")
        token = get_token_from_captcha(submit_result_url, image_id, result)
        print(f"The function returned token: {token}")
        cleanup_files(input_image_path, image_paths)
        return image_id, token, (result // 30)
    else:
        print(f"Failed - The function returned degree: {result}")

    cleanup_files(input_image_path, image_paths)
    return None, False, None

if __name__ == "__main__":
    main()
