"""
Spawns n Prozesse, wartet auf Beendigung, liest stats_*.json
und aggregiert die Ergebnisse.
"""
import json, subprocess, sys

P0      = 1.0
K       = 2           # kein Feuerwerk in 5 Runden ⇒ Stopp
BASE    = 50000

def run_ring(n):
    procs = []
    for pid in range(n):
        cmd = [sys.executable, "ring_node.py",
               str(pid), str(n), str(K), str(P0), str(BASE)]
        procs.append(subprocess.Popen(cmd))
    for p in procs:
        p.wait()
    # Stats einsammeln
    with open(f"stats_n{n}.json") as f:
        return json.load(f)

def main():
    ns = [2, 4, 8, 16, 32, 64, 128]   # passe an deine Maschine an
    results = []
    for n in ns:
        try:
            stats = run_ring(n)
            results.append(stats)
            print(f"n={n:>3}: Runden={stats['rounds']:>5}, "
                  f"Multicasts={stats['multicasts']:>5}, "
                  f"ØRundenzeit={stats['mean_rt']*1000:6.1f} ms")
        except Exception as e:
            print(f"n={n} ✔ gescheitert – {e}")
            break
    # Gesamt-JSON
    with open("all_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
