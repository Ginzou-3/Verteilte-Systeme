#!/usr/bin/env bash
# run_ring_remote.sh  <knoten-anzahl=N> [BASE=50000]

N="$1"; BASE="${2:-50000}"
K=5; P0=1.0

mapfile -t HOSTS < hosts.txt
H=${#HOSTS[@]}

if (( N > H )); then
  echo "Fehler: nur $H Hosts verfügbar, aber $N Knoten angefordert"; exit 1
fi

echo ">>> Starte Ring mit $N Knoten auf $H Hosts"

for i in $(seq 0 $((N-1))); do
  host=${HOSTS[$i]}
  echo "   ▸ $host …"
  ssh "$host" "pkill -f ring_node.py; \
       nohup python3 ~/firework/ring_node.py $i $N $K $P0 $BASE \
       >~/firework/node_$i.log 2>&1 &"
done
echo ">>> Alle Prozesse laufen."
