import psycopg2
import db
import config as cf
import hash_image
import time
from PIL import Image

CONFIG = cf.Config.from_env()
def main():
    with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as database:
        id_index = 1 # Start at 1 since there is no index 0
        fetch_amount = 100
        while True:
            imgs:list[db.ModifiedImage] = database.get_images(id_index, fetch_amount)

            if not imgs:
                break

            for img in imgs:
                process_image(img)

            id_index += fetch_amount

def process_image(img: db.ModifiedImage ):
    for name, Method in hash_image.HashingMethods().hashing_methods.items():

        with Image.open(img.image_path) as open_image:
            loaded_img = open_image.convert("RGB").copy()

        hash = Method().hash_image(loaded_img)

        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as database:
            try:
                database.send_hash(hash, img.id, name)
            except db.HashMethodIDNotFound:
                database.add_hash_method(name)
                database.send_hash(hash, img.id, name)

def open_image(img: db.ModifiedImage):
    Image.open(img.image_path)


if __name__ == "__main__":
    while True:
        try:
            main()
        except psycopg2.OperationalError:
            time.sleep(1)
            continue

        break
