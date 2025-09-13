"""
Like-Counter Beispielanwendung für horizontale Skalierbarkeit und abgeschwächte Konsistenz
Verteilte Worker erhöhen Likes auf zufällige Posts in MongoDB.
"""
import threading
import random
import time
import os
from pymongo import MongoClient, WriteConcern, ReadPreference

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "scaling_demo"
COLL_NAME = "posts"

NUM_POSTS = 10
NUM_WORKERS = int(os.environ.get("NUM_WORKERS", 8))  # Read from environment or default to 8
OPS_PER_WORKER = 1000
WRITE_CONCERN = WriteConcern(w=1)
READ_PREFERENCE = ReadPreference.SECONDARY_PREFERRED


def setup_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]
    coll.drop()
    coll.insert_many({"_id": i, "likes": 0} for i in range(NUM_POSTS))
    client.close()


def worker_fn(worker_id, stats):
    client = MongoClient(MONGO_URI, w=WRITE_CONCERN.document["w"])
    db = client[DB_NAME]
    coll = db.get_collection(COLL_NAME, write_concern=WRITE_CONCERN, read_preference=READ_PREFERENCE)
    for _ in range(OPS_PER_WORKER):
        post_id = random.randint(0, NUM_POSTS - 1)
        coll.update_one({"_id": post_id}, {"$inc": {"likes": 1}})
        # Optional: Lese-Operation mit schwacher Konsistenz
        doc = coll.find_one({"_id": post_id})
        if doc["likes"] < 0:  # Unmöglich, aber prüft auf Inkonsistenzen
            stats["errors"] += 1
    client.close()


def main():
    setup_db()
    stats = {"errors": 0}
    threads = []
    t0 = time.time()
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker_fn, args=(i, stats))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    t1 = time.time()
    # Ergebnisse ausgeben
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]
    print("Likes pro Post:")
    for doc in coll.find().sort("_id"):
        print(f"Post {doc['_id']}: {doc['likes']} Likes")
    print(f"Fehlerhafte Reads: {stats['errors']}")
    print(f"Dauer: {t1-t0:.2f} s")
    client.close()

if __name__ == "__main__":
    main()
