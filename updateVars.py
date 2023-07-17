# import requests
# import yaml
# from bs4 import BeautifulSoup
#
# APACHE_LOUNGE_URL = 'https://www.apachelounge.com/download/'
# CRS_REPO_URL = "https://api.github.com/repos/coreruleset/coreruleset/releases/latest"
# ANSIBLE_VARS_FILE = './vars.yml'
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
# }
#
# response = requests.get(APACHE_LOUNGE_URL, headers=HEADERS, verify=False)
# soup = BeautifulSoup(response.text, 'html.parser')
#
# if response.status_code == 200:
#     httpd_link = soup.find('a', href=lambda href: href and 'httpd' in href and href.endswith('.zip'))
#     httpd_version = httpd_link['href'].split('-')[1].split('-')[0]
#     mod_security_link = soup.find('a', href=lambda href: href and 'mod_security' in href and href.endswith('.zip'))
#     mod_security_version = mod_security_link['href'].split('-')[1].split('-')[0]
#     vs_version = httpd_link['href'].split('-')[-1].split('.')[0][2:]
#
#     print(f"Apache HTTP Server version: {httpd_version}")
#     print(f"ModSecurity version: {mod_security_version}")
#     print(f"Visual Studio version: {vs_version}")
# else:
#     print("Error retrieving the version number. Status code:", response.status_code)
#
# response = requests.get(CRS_REPO_URL)
# if response.status_code == 200:
#     release_data = response.json()
#     crs_version = release_data['tag_name']
#     print("Latest tag:", crs_version)
# else:
#     print("Error retrieving the latest tag. Status code:", response.status_code)
#
# with open(ANSIBLE_VARS_FILE, 'r') as file:
#     data = yaml.safe_load(file)
#
# data['httpd_version'] = httpd_version
# data['mod_security_version'] = mod_security_version
# data['crs_version'] = crs_version
#
# with open(ANSIBLE_VARS_FILE, 'w') as file:
#     yaml.dump(data, file)

import os

import requests
import yaml
from bs4 import BeautifulSoup

APACHE_LOUNGE_URL = 'https://www.apachelounge.com/download/'
CRS_REPO_URL = "https://api.github.com/repos/coreruleset/coreruleset/releases/latest"
ANSIBLE_VARS_FILE = '/home/zacg/ansible/vars.yml'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
}


def get_version_number(soup, keyword):
    link = soup.find('a', href=lambda href: href and keyword in href and href.endswith('.zip'))
    version = link['href'].split('-')[1].split('-')[0]
    return version


def update_vars_file(httpd_version, mod_security_version, crs_version):
    with open(ANSIBLE_VARS_FILE, 'r') as file:
        data = yaml.safe_load(file)
        data['httpd_version'] = httpd_version
        data['mod_security_version'] = mod_security_version
        data['crs_version'] = crs_version

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
        vs_version = httpd_link['href'].split('-')[-1].split('.')[0][2:]

        print(f"Apache HTTP Server version: {httpd_version}")
        print(f"ModSecurity version: {mod_security_version}")
        print(f"Visual Studio version: {vs_version}")

        response = session.get(CRS_REPO_URL)
        response.raise_for_status()
        release_data = response.json()
        crs_version = release_data['tag_name']
        crs_version = crs_version.replace('v', '')
        print("OWASP crs version:", crs_version)

        update_vars_file(httpd_version, mod_security_version, crs_version)

        playbook_path = "/home/zacg/ansible/build-httpd.yml"
        command = f"ansible-playbook {playbook_path} --connection=local --extra-vars '@vars.yml'"

        try:
            exit_code = os.system(command)
            if exit_code == 0:
                print("Ansible playbook executed successfully.")
            else:
                print(f"Error executing Ansible playbook. Exit code: {exit_code}")
        except OSError as e:
            print("Error executing Ansible playbook:", e)

except requests.exceptions as e:
    print("Error", e)
