"""Ring-Token-Knoten für Aufgabe 1 (Feuerwerk) – robuste Windows-Version

Start:
  python ring_node.py <id> <n> <k> <p0> <base_port>

Parameter
---------
  id          : Position im Ring [0 .. n-1]
  n           : Gesamtzahl Prozesse im Ring
  k           : Terminierung, wenn k Runden lang niemand zündet
  p0          : Anfangs‑Zündwahrscheinlichkeit
  base_port   : Port von Prozess 0  (Port i = base_port + i)
"""

from __future__ import annotations

import json
import os
import random
import socket
import struct
import sys
import time
from datetime import datetime
from typing import Tuple

MULTICAST_ADDR = "239.42.42.42"
MCAST_PORT      = 51000
TOKEN_TTL       = 1           # nur localhost

Token = Tuple[int, int, float, bool]  # round_id, silent, p_sender, stop


def make_udp_socket(bind_port: int, *, multicast: bool = False) -> socket.socket:
    """Erzeugt einen UDP-Socket; auf Windows werden ICMP-Resets sauber ignoriert."""

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # --- Windows-Spezialfall: ICMP "Port unreachable" unterdrücken ---
    if os.name == "nt":
        try:
            SIO_UDP_CONNRESET = getattr(socket, "SIO_UDP_CONNRESET", 0x9800000C)
            s.ioctl(SIO_UDP_CONNRESET, struct.pack("I", 0))  # 0 = Reset OFF
        except (AttributeError, OSError, ValueError):
            pass  # nicht verfügbar → einfach weiter
    # ------------------------------------------------------------

    if multicast:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TOKEN_TTL)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        s.bind(("", MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        s.bind(("127.0.0.1", bind_port))

    s.setblocking(False)
    return s


def node(id_: int, n: int, k: int, p0: float, base_port: int) -> None:
    """Startet einen einzelnen Ring-Prozess."""

    rng         = random.Random(id_)
    unicast     = make_udp_socket(base_port + id_)
    multicast   = make_udp_socket(0, multicast=True)
    next_addr   = ("127.0.0.1", base_port + ((id_ + 1) % n))

    p               = p0
    silent_rounds   = 0
    initiated_stop  = False    # True nur bei Prozess 0, wenn er STOP auslöst

    round_times: list[float] = []
    last_round_ts   = None
    mcasts_sent     = 0

    def send_token(round_id: int, silent: int, prob: float, stop: bool = False):
        token: Token = (round_id, silent, prob, stop)
        unicast.sendto(json.dumps(token).encode(), next_addr)

    # --- Token initiieren (Prozess 0) ---
    if id_ == 0:
        time.sleep(0.2)               # Start-Barriere (alle Sockets binden)
        last_round_ts = time.monotonic()
        send_token(0, 0, p)           # stop=False

    # --- Hauptschleife ---
    while True:
        # 1) Token empfangen?
        try:
            data, _ = unicast.recvfrom(4096)
            round_id, silent_rounds, p_prev, stop_flag = json.loads(data.decode())

            # Wenn Stop-Token empfangen → vor dem Beenden an Nachbarn weiterleiten
            if stop_flag:
                unicast.sendto(data, next_addr)
                break

            # Metrik (nur Prozess 0): Rundenzeit messen
            if id_ == 0:
                now = time.monotonic()
                if last_round_ts is not None:
                    round_times.append(now - last_round_ts)
                last_round_ts = now

            # 2) Würfeln, ob wir zünden
            if rng.random() < p:
                msg = f"BOOM from {id_} in round {round_id}"
                multicast.sendto(msg.encode(), (MULTICAST_ADDR, MCAST_PORT))
                p /= 2
                silent_rounds = 0
                if id_ == 0:
                    mcasts_sent += 1
            else:
                silent_rounds += 1

            # 3) Prozess 0 löst STOP aus, sobald k stille Runden erreicht sind
            if id_ == 0 and silent_rounds >= k and not initiated_stop:
                initiated_stop = True
                stop_flag = True
            else:
                stop_flag = False

            # 4) Token weiterreichen
            send_token(round_id + 1, silent_rounds, p, stop_flag)

        except BlockingIOError:
            pass
        except ConnectionResetError:
            continue

        # 5) Multicast-Nachricht (BOOM) nur lesen, um Kernel-Puffer klein zu halten
        try:
            while True:
                multicast.recvfrom(4096)
        except BlockingIOError:
            pass
        except ConnectionResetError:
            continue

    # --- Nachbereitung (nur Prozess 0) ---
    if id_ == 0:
        stats = {
            "n"          : n,
            "rounds"     : len(round_times),
            "multicasts" : mcasts_sent,
            "min_rt"     : min(round_times) if round_times else 0,
            "mean_rt"    : sum(round_times)/len(round_times) if round_times else 0,
            "max_rt"     : max(round_times) if round_times else 0,
            "timestamp"  : datetime.now().isoformat(),
        }
        with open(f"stats_n{n}.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("usage: ring_node.py <id> <n> <k> <p0> <base_port>")
        sys.exit(1)

    id_, n, k       = map(int, sys.argv[1:4])
    p0              = float(sys.argv[4])
    base_port       = int(sys.argv[5])

    node(id_, n, k, p0, base_port)
