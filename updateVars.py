import os
import hashlib
import requests
import yaml
from bs4 import BeautifulSoup

APACHE_LOUNGE_URL = 'https://www.apachelounge.com/download/'
CRS_REPO_URL = "https://api.github.com/repos/coreruleset/coreruleset/releases/latest"
ANSIBLE_VARS_FILE = './vars.yml'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
}


def get_version_number(soup, keyword):
    link = soup.find('a', href=lambda href: href and keyword in href and href.endswith('.zip'))
    version = link['href'].split('-')[1].split('-')[0]
    return version

def calculate_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        while True:
            data = file.read(65536)  # Read the file in 64KB chunks
            if not data:
                break
            sha256_hash.update(data)
    return sha256_hash.hexdigest()


def update_vars_file(httpd_version, httpd_checksum, mod_security_version, mod_log_rotate_version, crs_version):
    # with open(ANSIBLE_VARS_FILE, 'r') as file:
    #     data = yaml.safe_load(file)
    #     data['httpd_version'] = httpd_version
    #     data['httpd_checksum'] = httpd_checksum
    #     data['mod_security_version'] = mod_security_version
    #     data['crs_version'] = crs_version
    #     data['mod_log_rotate_version'] = mod_log_rotate_version

    with open(ANSIBLE_VARS_FILE, 'w') as file:
        yaml.dump(data, file)


try:
    with requests.Session() as session:
        response = session.get(APACHE_LOUNGE_URL, headers=HEADERS, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        httpd_link = soup.find('a', href=lambda href: href and 'httpd' in href and href.endswith('.zip'))
        httpd_version = get_version_number(soup, 'httpd')
        
        mod_security_version = get_version_number(soup, 'mod_security')
        mod_log_rotate_version = get_version_number(soup, 'mod_log_rotate')
        vs_version = httpd_link['href'].split('-')[-1].split('.')[0][2:]

        httpd_file_name = f"httpd-{httpd_version}-win64-{vs_version}.zip"
        httpd_file_url =f'https://www.apachelounge.com/download/{vs_version}/binaries/{httpd_file_name}'
        response = session.get(httpd_file_url, headers=HEADERS, verify=False)
        response.raise_for_status()
        httpd_file_path = f"./{httpd_file_name}"
        with open(httpd_file_path, 'wb') as file:
            file.write(response.content)
        httpd_checksum = calculate_checksum(httpd_file_path)
        
        print(f"HTTPD Checksum: {httpd_checksum}")
        print(f"Apache HTTP Server version: {httpd_version}")
        print(f"ModSecurity version: {mod_security_version}")
        print(f"ModLogRotate version: {mod_log_rotate_version}")
        print(f"Visual Studio version: {vs_version}")

        response = session.get(CRS_REPO_URL)
        response.raise_for_status()
        release_data = response.json()
        crs_version = release_data['tag_name']
        crs_version = crs_version.replace('v', '')
        print("OWASP crs version:", crs_version)

        update_vars_file(httpd_version, httpd_checksum, mod_security_version, mod_log_rotate_version, crs_version)
        # Not needed with Actions
        # playbook_path = "/home/zacg/ansible/build-httpd.yml"
        # command = f"ansible-playbook {playbook_path} --connection=local --extra-vars '@vars.yml'"

        # try:
        #     exit_code = os.system(command)
        #     if exit_code == 0:
        #         print("Ansible playbook executed successfully.")
        #     else:
        #         print(f"Error executing Ansible playbook. Exit code: {exit_code}")
        # except OSError as e:
        #     print("Error executing Ansible playbook:", e)

except requests.exceptions as e:
    print("Error", e)
