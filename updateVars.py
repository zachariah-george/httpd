import hashlib
import requests
import yaml
from bs4 import BeautifulSoup

URLS = {
    'apache_lounge': 'https://www.apachelounge.com/download/',
    'crs_repo': "https://api.github.com/repos/coreruleset/coreruleset/releases/latest",
    'openssl_repo': "https://api.github.com/repos/openssl/openssl/releases/latest"
}
ANSIBLE_VARS_FILE = './vars.yml'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
}


def get_github_version(url):
    get_response = requests.get(url)
    get_response.raise_for_status()
    return get_response.json()['name'].split()[-1].lstrip('v')


def get_lounge_version(soup_ex, keyword):
    # Find the relevant link including version and date/build number
    link = soup_ex.find('a', href=lambda href: keyword in href and href.endswith('.zip'))
    # Extract the version and date/build number from the link
    version_date = link['href'].split('/')[-1].split('-')[1:3]
    return '-'.join(version_date)  # Combine version and date/build number


def calculate_checksum(file_path):
    with open(file_path, "rb") as file:
        sha256_hash = hashlib.sha256()
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


def update_vars_file(**kwargs):
    with open(ANSIBLE_VARS_FILE, 'r') as file:
        data = yaml.safe_load(file)
        data.update(kwargs)

    with open(ANSIBLE_VARS_FILE, 'w') as file:
        yaml.dump(data, file, sort_keys=False)


def download_file(url, file_path):
    get_response = requests.get(url, headers=HEADERS)
    get_response.raise_for_status()

    with open(file_path, 'wb') as file:
        file.write(get_response.content)


with requests.Session() as session:
    response = session.get(URLS['apache_lounge'], headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    httpd_version_date = get_lounge_version(soup, 'httpd')
    # mod_security_version = get_lounge_version(soup, 'mod_security')
    # mod_log_rotate_version = get_lounge_version(soup, 'mod_log_rotate')
    mod_security_version = get_lounge_version(soup, 'mod_security').split('-')[0]
    mod_log_rotate_version = get_lounge_version(soup, 'mod_log_rotate').split('-')[0]



    vs_version = soup.find('a', href=lambda href: 'httpd' in href and href.endswith('.zip'))['href'].split('-')[-1].split('.')[0][2:]
    httpd_file_name = f"httpd-{httpd_version_date}-win64-VS{vs_version}.zip"
    httpd_file_url = f"{URLS['apache_lounge']}VS{vs_version}/binaries/{httpd_file_name}"

    download_file(httpd_file_url, httpd_file_name)
    httpd_checksum = calculate_checksum(httpd_file_name)

    crs_version = get_github_version(URLS['crs_repo'])
    openssl_version = get_github_version(URLS['openssl_repo'])

    update_vars_file(
        httpd_version=httpd_version_date.split('-')[0],
        httpd_build_date=httpd_version_date.split('-')[1],
        httpd_checksum=httpd_checksum,
        mod_security_version=mod_security_version,
        mod_log_rotate_version=mod_log_rotate_version,
        crs_version=crs_version,
        openssl_version=openssl_version
    )
