#!/usr/bin/env python3
"""
Feuerwerks-Simulation in einem logischen Ring.
Alle Knoten laufen als Python-Threads und kommunizieren über Queues.
"""

import threading as th
import queue, random, time, json
from statistics import mean

# ----------------------------------- Konfig ----------------------------------

P0      = 1.0          # Anfangs-Zündwahrscheinlichkeit
K       = 5            # Terminierung, wenn K Runden lang niemand zündet
NS      = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144]   # Ringgrößen, die wir testen
SEED    = 42           # für Reproduzierbarkeit

# -----------------------------------------------------------------------------

class Stats:
    """Threadsicheres Aggregat für Metriken."""
    def __init__(self, n: int):
        self.n = n
        self.round_times = []          # Duration pro Token-Umlauf
        self.multicasts  = 0
        self.lock        = th.Lock()
        self.last_round_start = None   # wird von Knoten 0 gesetzt

    def note_round(self, dur: float):
        with self.lock:
            self.round_times.append(dur)

    def note_multicast(self):
        with self.lock:
            self.multicasts += 1

def ring_simulation(n: int, k: int, p0: float) -> dict:
    """Simuliert einen Ring mit n Knoten, liefert Statistik-Dict."""
    random.seed(SEED + n)             # ein Seed pro Durchlauf
    queues = [queue.Queue() for _ in range(n)]
    stats  = Stats(n)
    stop_flag = th.Event()            # globales Stopp-Signal

    class Node(th.Thread):
        def __init__(self, idx: int):
            super().__init__(daemon=True)
            self.idx = idx
            self.p   = p0
            self.silent_local = 0

        def run(self):
            nonlocal silent_global
            next_q = queues[(self.idx + 1) % n]
            q      = queues[self.idx]
            while not stop_flag.is_set():
                token = q.get()                    # blockiert
                if token.get("stop"):
                    next_q.put(token)              # einmal weiterleiten
                    stop_flag.set()
                    break

                round_id = token["rid"]
                if self.idx == 0:
                    now = time.perf_counter()
                    if stats.last_round_start is not None:
                        stats.note_round(now - stats.last_round_start)
                    stats.last_round_start = now

                # Würfel: zünde Feuerwerk?
                if random.random() < self.p:
                    stats.note_multicast()
                    self.p /= 2
                    silent_global = 0
                    self.silent_local = 0
                else:
                    self.silent_local += 1
                    silent_global += 1

                # Prozess 0 löst Stop aus
                stop = False
                if self.idx == 0 and silent_global >= k:
                    stop = True

                next_q.put({"rid": round_id + 1, "stop": stop})

    # --------- Threads erstellen ­& starten ---------------------------------
    silent_global = 0
    nodes = [Node(i) for i in range(n)]
    for node in nodes:
        node.start()

    # Initial-Token in Knoten 0 einwerfen
    queues[0].put({"rid": 0, "stop": False})

    # Auf Terminierung warten
    for node in nodes:
        node.join()

    return {
        "n"          : n,
        "rounds"     : len(stats.round_times),
        "multicasts" : stats.multicasts,
        "min_rt"     : min(stats.round_times) if stats.round_times else 0,
        "mean_rt"    : mean(stats.round_times) if stats.round_times else 0,
        "max_rt"     : max(stats.round_times) if stats.round_times else 0,
    }

# ------------------------------- Batch-Läufe ----------------------------------

if __name__ == "__main__":
    results = []
    for n in NS:
        res = ring_simulation(n, K, P0)
        results.append(res)
        print(f"n={n:>3}  Runden={res['rounds']:>3}  "
              f"Multicasts={res['multicasts']:>2}  "
              f"ØRundenzeit={res['mean_rt']*1e3:7.2f} ms")

    # JSON-Export
    with open("sim_ring_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
