import hashlib
import json
import pymysql

from util.common import common

config = common.config

DB_CONFIG = {
    "host": config.get('mariadb', 'mariadb_host'),
    "port": int(config.get('mariadb', 'mariadb_port')),
    "user": config.get('mariadb', 'mariadb_user'),
    "password": config.get('mariadb', 'mariadb_password'),
    "database": config.get('mariadb', 'mariadb_database'),
    "charset": config.get('mariadb', 'charset'),
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def insert_image(conn, source_url, origin_path, md5_hash):
    sql = """
    INSERT INTO image (source_url, md5_hash, origin_path)
    VALUES (%s, %s, %s)
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (source_url, md5_hash, origin_path))
        conn.commit()
        return cursor.lastrowid


def insert_embedding(conn, image_id, model_name, vector):
    sql = """
    INSERT INTO image_embedding (image_id, model_name, vector_512)
    VALUES (%s, %s, VEC_FromText(%s))
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (image_id, model_name, json.dumps(vector)))
        conn.commit()


def search_similar_image(conn, query_vector, limit=5):
    sql = """
    SELECT
        ie.image_id,
        i.origin_path,
        ie.model_name,
        VEC_DISTANCE_COSINE(ie.vector_512, VEC_FromText(%s)) AS distance
    FROM image_embedding ie
    JOIN image i ON ie.image_id = i.id
    ORDER BY distance ASC
    LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (json.dumps(query_vector), limit))
        return cursor.fetchall()


def main():
    conn = get_connection()
    try:
        # 假設 CLIP 輸出的 512 維 embedding
        embedding = [0.01] * 512

        image_id = insert_image(
            conn,
            source_url="https://example.com/cat.jpg",
            origin_path="/data/origin/cat.jpg",
            md5_hash=hashlib.md5(b"cat").hexdigest(),
        )

        insert_embedding(conn, image_id, "clip-vit-b32", embedding)

        results = search_similar_image(conn, embedding, limit=10)

        for row in results:
            print(row)

    finally:
        conn.close()


if __name__ == "__main__":
    main()