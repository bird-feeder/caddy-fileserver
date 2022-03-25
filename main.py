import datetime
import ipaddress
import mimetypes
import os
import platform
import shlex
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import dotenv
import paramiko
import pyperclip
import pymongo
from loguru import logger


def notifcation(title, subtitle=None, message=None):
    notifier_bin = '/opt/homebrew/bin/terminal-notifier'
    subprocess.run(
        shlex.split(f'{notifier_bin} -title \"{title}\" '
                    f'-subtitle \"{subtitle}\" -message \"{message}\"'))


def check_host(strict=False):
    exit_code = os.system(f'ping -c 1 -W 1 {os.environ["FILSERVER_HOST"]} '
                          '> /dev/null 2>&1')
    if exit_code != 0:
        notifcation('Host server is down!')

    host = socket.gethostname()
    local_ip = ipaddress.ip_address(socket.gethostbyname(host))
    logger.info(f'Received a request from {local_ip} ({host})')
    if strict and not local_ip in ipaddress.ip_network(
            os.environ['SUBNET']) and local_ip != ipaddress.ip_address(
                '127.0.0.1'):
        raise ConnectionRefusedError
    if strict and not str(local_ip) in os.environ["ALLOWED_HOSTS"]:
        raise ConnectionRefusedError
    return


def insert(file_data):
    hostname = os.environ['DB_HOSTNAME']
    port = os.environ['DB_PORT']
    db_name = os.environ['DB_NAME']
    db_username = os.environ['DB_USERNAME']
    db_pass = os.environ['DB_PASS']

    collection = 'files'

    client = pymongo.MongoClient(
        f'mongodb://{db_username}:{db_pass}@{hostname}:{port}',
        serverSelectionTimeoutMS=2000)

    db = client[db_name]
    try:
        res = db.files.insert_one(file_data)
    except pymongo.errors.ServerSelectionTimeoutError:
        logger.warning('Failed to insert record into MongoDB')
    return


def upload(file, domain_name, strict=False):
    dotenv.load_dotenv(f'{Path(__file__).parent}/.env')
    logger.add(f'{Path(__file__).parent}/logs.log')
    start = time.time()
    check_host(strict=strict)

    start = time.time()
    id_ = str(uuid.uuid4()).split('-')[0]
    out_filename = f'{id_}{Path(file).suffix}'

    logger.info(f'Uploading "{file}"" with id "{id_}" ...')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(os.environ['FILSERVER_HOST'],
                       username=os.environ['FILSERVER_USERNAME'])
    except paramiko.ssh_exception.AuthenticationException:
        client.connect(
            os.environ['FILSERVER_HOST'],
            username=os.environ['FILSERVER_USERNAME'],
            key_filename=
            f'{Path().home()}/.ssh/{os.environ["SSH_PUBKEY_FILENAME"]}')

    sftp = client.open_sftp()
    sftp.put(file, f'{os.environ["FILESERVER_DATA_PATH"]}/{out_filename}')

    url = f'https://{domain_name}/{out_filename}'
    logger.info(f'Uploaded "{id_}" successfully! ({url})')

    file_data = {
        '_id': id_,
        'created_at': time.ctime(Path(file).stat().st_ctime),
        'original_file_name': Path(file).name,
        'url_file_name': Path(out_filename).name,
        'url': url,
        'size_bytes': Path(file).stat().st_size,
        'mimetype': mimetypes.guess_type(file)[0],
        'processing_time': str(datetime.timedelta(seconds=time.time() - start))
    }
    try:
        pyperclip.copy(file_data['url'])
    except pyperclip.PyperclipException:
        pass
    if 'macOS' in platform.platform():
        notifcation('Upload complete!',
                    f'Took {round(time.time() - start, 2)}s', file_data['url'])

    insert(file_data)
    logger.info('Inserted the file into the database successfully!')
    logger.info(file_data['url'])
    print(file_data['url'])
    sftp.close()
    client.close()
    return


if __name__ == '__main__':
    sys.argv = sys.argv + ['/Users/Felis.catus/Desktop/Rhizoecus_cyperalis']
    upload(sys.argv[1], 'd.aibird.me', strict=False)
