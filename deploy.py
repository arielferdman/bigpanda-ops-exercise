import time
import urllib.request
import os
import zipfile
import tarfile
import subprocess
import logging
import shutil

app_zip_file_name = 'app.zip'
images_file_name = 'images.tar.gz'
data_dir_name = 'volumes'
repo_dir_name = 'app'
logger = logging.getLogger('deploy')

urls = {
    'app_repo_url': 'https://github.com/bigpandaio/ops-exercise/archive/master.zip',
    'images_download_url': 'https://s3.eu-central-1.amazonaws.com/devops-exercise/pandapics.tar.gz',
    'healthcheck': 'http://localhost:3000/health',
}


def errorlog(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            logger.error(ex)
            logger.error('deploy failed :(')
            tear_down()

    return wrapper


@errorlog
def create_directory():
    logger.info('creating volume directory...')
    os.mkdir(data_dir_name)


@errorlog
def download(file_url, file_name):
    logger.info('downloading ' + file_name + '...')
    urllib.request.urlretrieve(file_url, file_name)


@errorlog
def extract(archive_type, archive_file_name, destination_path):
    logger.info('extracting ' + archive_file_name + '...')
    if archive_type == 'zip':
        zip_ref = zipfile.ZipFile(archive_file_name, 'r')
        zip_ref.extractall(destination_path)
        zip_ref.close()
    elif archive_type == 'tar':
        tf = tarfile.open(images_file_name)
        tf.extractall(destination_path)


@errorlog
def rename_extracted_volume_dir_name():
    logger.info('renaming volume dir...')
    extracted_repo_path = os.path.join(data_dir_name, os.listdir(data_dir_name)[-1])
    new_repo_path = os.path.join(data_dir_name, repo_dir_name)
    if repo_dir_name in os.listdir(data_dir_name):
        shutil.rmtree(os.path.join(data_dir_name, repo_dir_name))
    os.rename(extracted_repo_path, new_repo_path)

    return new_repo_path


@errorlog
def remove_downloaded_files(file_names):
    logger.info('removing downloaded archives...')
    for file_name in file_names:
        os.remove(file_name)


@errorlog
def docker_compose(cmd='up -d'):
    logger.info('running docker-compose...')
    subprocess.run(['docker-compose'] + cmd.split())


def healthcheck():
    logger.info('checking app health...')
    cond = 1
    left_retries = 5
    while cond and left_retries > 0:
        try:
            response = urllib.request.urlopen(urls['healthcheck'], timeout=3)
            if response.status == 200:
                cond = 0
        except Exception as ex:
            if ex.errno == 104:
                pass
            logger.error(ex)
        time.sleep(1)
        left_retries -= 1

    return cond


def tear_down():
    logger.info('tearing down docker containers...')
    docker_compose('down')


def create_volume():
    logger.info('creating volumes...')
    download(urls['app_repo_url'], app_zip_file_name)
    download(urls['images_download_url'], images_file_name)
    extract('zip', app_zip_file_name, data_dir_name)
    new_dir_path = rename_extracted_volume_dir_name()
    extract('tar', images_file_name, os.path.join(new_dir_path, 'public', 'images'))
    remove_downloaded_files([app_zip_file_name, images_file_name])


def deploy_config():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler('deploy.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)


def check_directory():
    logger.info('checking if volumes dir exists...')
    return os.path.isdir(data_dir_name)


def main():
    deploy_config()
    logger.info('starting deploy process...')
    if not check_directory():
        create_directory()
    create_volume()
    docker_compose()
    # docker_compose('stop db')

    if not healthcheck():
        logger.info('deploy success :)')
    else:
        tear_down()
        logger.error('deploy failed :(')


main()
