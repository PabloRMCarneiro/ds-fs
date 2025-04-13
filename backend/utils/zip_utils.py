# backend/utils/zip_utils.py
import os
import zipfile

def zip_directory(dir_path: str, zip_path: str):
    """
    Compacta o diretório informado em um arquivo ZIP.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dir_path)
                zipf.write(file_path, arcname)
