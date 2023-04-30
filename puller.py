import os
import time
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime
import subprocess

# Replace with your camera's IP address and port
camera_ip = "http://172.23.0.178:8080"
api_endpoint = "/ccapi/ver100"

# Local directory to save downloaded files
download_dir = "Downloaded_photos"

# File to track downloaded files
downloaded_files_list = "downloaded_files.txt"



def get_video_creation_date(file_path):
    #Used to pull creation dates of videos, no EXIF data there

    ffprobe_command = f"ffprobe -v error -select_streams v:0 -show_entries stream_tags=creation_time -of default=noprint_wrappers=1:nokey=1 -i {file_path}"
    date_string = subprocess.check_output(ffprobe_command, shell=True).decode("utf-8").strip()
    date_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    return date_object

# Check if the camera is online and responsive
try:
    response = requests.get(f"{camera_ip}{api_endpoint}/deviceinformation", timeout=5)
    if response.status_code != 200:
        print("Camera is not responding.")
        exit()
except requests.exceptions.RequestException:
    print("Camera is not reachable.")
    exit()

print("Camera is online and responsive.")

# Check if download directory exists, create it if not
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Load list of downloaded files
downloaded_files = set()
if os.path.exists(downloaded_files_list):
    with open(downloaded_files_list, "r") as file:
        downloaded_files = set(file.read().splitlines())

# Get the list of directories from the camera
response = requests.get(f"{camera_ip}{api_endpoint}/contents/sd")
directories_data = response.json()


# Check if the API endpoint returns a single message
if len(directories_data) == 1 and "url" not in directories_data:
    print("API endpoint returned a single message:", directories_data)
    exit()

# Extract the list of file URLs from all directories
file_urls = []
for directory in directories_data["url"]:
    directory = directory.split("/")[-1]
    print(directory)
    response = requests.get(f"{camera_ip}{api_endpoint}/contents/sd/{directory}")
    files_data = response.json()
    file_urls.extend(files_data["url"])

# Download new files
for file_url in file_urls:
    file_name = os.path.basename(file_url)

    if file_name not in downloaded_files:
        success = False
        attempts = 3

        while not success and attempts > 0:
            print(f"Attempting to download {file_name}...")
            response = requests.get(file_url)

            if response.ok:
                print("Got OK, Downloaded!")

                if file_name.lower().endswith(('.jpg', '.jpeg')):
                    # Save the downloaded file to the local directory
                    img = Image.open(BytesIO(response.content))
                    exif_data = img._getexif()
                    date_string = exif_data[36867]  # 36867 is the tag for DateTimeOriginal
                    date_object = datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")
                elif file_name.lower().endswith('.mp4'):
                    local_file_path = os.path.join(download_dir, file_name)  # Temporarily save the video file
                    with open(local_file_path, "wb") as file:
                        file.write(response.content)
                    date_object = get_video_creation_date(local_file_path)
                    #Kind of jank, and will write to a file, but whatever
                    os.remove(local_file_path)  # Remove the temporary video file after getting the creation date

                date_dir = os.path.join(download_dir, date_object.strftime("%Y%m%d"))
                if not os.path.exists(date_dir):
                    #If the date directory doesn't exist, make it
                    os.makedirs(date_dir)

                local_file_path = os.path.join(date_dir, file_name)
                with open(local_file_path, "wb") as file:
                    file.write(response.content)

                # Update the list of downloaded files
                downloaded_files.add(file_name)

                # Save the updated list to the file
                with open(downloaded_files_list, "a") as file:
                    file.write(f"{file_name}\n")

                print(f"{file_name} downloaded and saved.")
                success = True
            else:
                print(f"Failed to download {file_name}.")
                print("Status code:", response.status_code)
                print("Reason:", response.reason)
                print("Response text:", response.text)

                attempts -= 1
                if attempts > 0:
                    print(f"Retrying in 5 seconds... ({attempts} attempts remaining)")
                    time.sleep(5)

        if not success:
            print(f"Failed to download {file_name} after 3 attempts. Exiting.")
            exit()
    else:
        print(f"{file_name} already downloaded.")

