import threading as th
import queue, random, time, json
from statistics import mean

# ----------------------------------- Konfig ----------------------------------
P0      = 1.0
K       = 5
NS      = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192,
           16384, 32768, 65536, 131072, 262144]
SEED    = 42

# -----------------------------------------------------------------------------
class Stats:
    """Threadsicheres Aggregat für Metriken + Konsistenzfehler."""
    def __init__(self, n: int):
        self.n              = n
        self.round_times    = []
        self.multicasts     = 0
        self.inconsistencies= 0
        self.lock           = th.Lock()
        self.last_round_start = None

    def note_round(self, dur: float):
        with self.lock:
            self.round_times.append(dur)

    def note_multicast(self):
        with self.lock:
            self.multicasts += 1

    def note_error(self):
        with self.lock:
            self.inconsistencies += 1

# -----------------------------------------------------------------------------

def ring_simulation(n: int, k: int, p0: float) -> dict:
    random.seed(SEED + n)
    queues = [queue.Queue() for _ in range(n)]
    stats  = Stats(n)
    stop_flag = th.Event()

    class Node(th.Thread):
        def __init__(self, idx: int):
            super().__init__(daemon=True)
            self.idx = idx
            self.p   = p0
            self.prev_p = p0
            self.last_seq = -1
            self.silent_local = 0

        def run(self):
            nonlocal silent_global
            next_q = queues[(self.idx + 1) % n]
            q      = queues[self.idx]
            while not stop_flag.is_set():
                token = q.get()
                if token.get("stop"):
                    next_q.put(token)
                    stop_flag.set()
                    break

                seq = token["rid"]
                # Konsistenz1: Sequenz darf nicht zurückspringen
                if seq <= self.last_seq:
                    stats.note_error()
                self.last_seq = seq

                if self.idx == 0:
                    now = time.perf_counter()
                    if stats.last_round_start is not None:
                        stats.note_round(now - stats.last_round_start)
                    stats.last_round_start = now

                if random.random() < self.p:
                    stats.note_multicast()
                    self.p /= 2
                    silent_global = 0
                    self.silent_local = 0
                else:
                    self.silent_local += 1
                    silent_global += 1

                # Konsistenz2: p darf nie steigen
                if self.p > self.prev_p + 1e-12:
                    stats.note_error()
                self.prev_p = self.p

                stop = (self.idx == 0 and silent_global >= k)
                next_q.put({"rid": seq + 1, "stop": stop})

    silent_global = 0
    nodes = [Node(i) for i in range(n)]
    for node in nodes:
        node.start()

    queues[0].put({"rid": 0, "stop": False})
    for node in nodes:
        node.join()

    return {
        "n"          : n,
        "rounds"     : len(stats.round_times),
        "multicasts" : stats.multicasts,
        "min_rt"     : min(stats.round_times) if stats.round_times else 0,
        "mean_rt"    : mean(stats.round_times) if stats.round_times else 0,
        "max_rt"     : max(stats.round_times) if stats.round_times else 0,
        "inconsistencies": stats.inconsistencies,
    }

# ------------------------------- Batch-Läufe ----------------------------------
if __name__ == "__main__":
    results = []
    for n in NS:
        res = ring_simulation(n, K, P0)
        results.append(res)
        print(f"n={n:>7}  Runden={res['rounds']:>2}  inc={res['inconsistencies']:<2}  "
              f"Multicasts={res['multicasts']:<5}  Ø={res['mean_rt']*1e3:8.3f} ms")

    with open("sim_ring_results_consistency.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
