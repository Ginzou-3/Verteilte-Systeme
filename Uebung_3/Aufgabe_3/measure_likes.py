"""
Mess-Skript für Like-Counter: Testet verschiedene Worker-Zahlen (Clustergrößen) und speichert Ergebnisse.
"""
import subprocess
import json
import time
import sys
import os

WORKER_COUNTS = [1, 2, 4, 8, 16, 32]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(SCRIPT_DIR, "like_counter_results.json")
PYTHON = sys.executable or "python3"
LIKE_COUNTER_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'Aufgabe_2', 'like_counter.py'))

results = []

for workers in WORKER_COUNTS:
    print(f"Starte Messung mit {workers} Workern...")
    t0 = time.time()
    env = os.environ.copy()
    env["NUM_WORKERS"] = str(workers)
    proc = subprocess.run([
        PYTHON, LIKE_COUNTER_PATH],
        capture_output=True, text=True, env=env
    )
    t1 = time.time()

    if proc.returncode != 0:
        print(f"  Fehler bei der Ausführung von like_counter.py mit {workers} Workern:")
        print(proc.stderr)
        results.append({
            "workers": workers,
            "likes_sum": 0,
            "min_likes": 0,
            "max_likes": 0,
            "errors": "N/A",
            "duration": t1-t0
        })
        continue

    output = proc.stdout
    # Extrahiere Likes pro Post und Fehler aus der Ausgabe
    likes = []
    errors = 0
    for line in output.splitlines():
        if line.startswith("Post"):
            parts = line.split(":")
            likes.append(int(parts[1].split()[0]))
        if "Fehlerhafte Reads" in line:
            errors = int(line.split(":")[1].strip())

    if not likes:
        print(f"  Keine Like-Daten für {workers} Worker gefunden. Ausgabe:")
        print(output)
        min_l, max_l, sum_l = 0, 0, 0
    else:
        min_l, max_l, sum_l = min(likes), max(likes), sum(likes)

    results.append({
        "workers": workers,
        "likes_sum": sum_l,
        "min_likes": min_l,
        "max_likes": max_l,
        "errors": errors,
        "duration": t1-t0
    })
    print(f"Fertig: {results[-1]}")

with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"Alle Ergebnisse in {RESULTS_FILE} gespeichert.")
