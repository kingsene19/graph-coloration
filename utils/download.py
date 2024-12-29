import requests
import os
import tarfile

URL_ARCHIVE = "https://mat.tepper.cmu.edu/COLOR/instances/instances.tar"
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")


def download():
    os.makedirs(DATASET_PATH, exist_ok=True)
    
    print("Téléchargement...")
    print(f"\t{URL_ARCHIVE}", end="\t")
    response = requests.get(URL_ARCHIVE)
    if response.status_code != 200:
        print("\x1b[31mFAILED\x1b[0m")
        return
    
    archive_path = os.path.join(DATASET_PATH, "instances.tar")
    with open(archive_path, "wb") as file:
        file.write(response.content)
    print("\x1b[32mOK\x1b[0m")
    
    print("Extraction...")
    with tarfile.open(archive_path) as file:
        for member in file.getmembers():
            file_path = os.path.join(DATASET_PATH, member.name)
            print(f"\t{member.name}", end="\t")
            try:
                file.extract(member, DATASET_PATH)
                print("\x1b[32mOK\x1b[0m")
            except:
                print("\x1b[31mFAILED\x1b[0m")
                
    os.remove(archive_path)
    
    
if __name__ == "__main__":
    download()