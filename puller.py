import os
import time
import requests

# Replace with your camera's IP address and port
camera_ip = "http://172.23.0.178:8080"
api_endpoint = "/ccapi/ver100"

# Local directory to save downloaded files
download_dir = "Downloaded_photos"

# File to track downloaded files
downloaded_files_list = "downloaded_files.txt"

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
                # Save the downloaded file to the local directory
                local_file_path = os.path.join(download_dir, file_name)
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

