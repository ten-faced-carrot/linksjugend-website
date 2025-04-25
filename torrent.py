from flask import Flask, request, jsonify
import time
from urllib.parse import unquote
import binascii
from sqlite3 import connect

app = Flask(__name__)
db = connect("instance/data.sqlite3", check_same_thread=False)

# Dictionary zum Speichern der Peers
peers = {}
torrent_stats = {}  # Statistik für Seeders und Leecher pro Torrent


def cleanup_hash(info_hash: str):
    return info_hash.encode("latin1").hex()

@app.route('/announce', methods=['GET'])
def announce():
    info_hash = request.args.get('info_hash', '')
    
    peer_id = request.args.get('peer_id')
    ip = request.remote_addr
    port = int(request.args.get('port'))
    event = request.args.get('event')
    if info_hash not in peers: peers[info_hash] = []
    peers[info_hash].append({"ip": ip, "port": port, "peer_id": peer_id, "last_seen": time.time()})
    
    seeders = sum(1 for p in peers[info_hash] if p["last_seen"] > time.time() - 1800)  # Alle aktiven Peers
    leechers = len(peers[info_hash]) - seeders
    torrent_stats[info_hash] = {"seeders": seeders, "leechers": leechers, "peers": len(peers[info_hash]), "peer_ids": list(map(lambda i: i["peer_id"], peers[info_hash]))}
    if event == "stopped":
        for key in peers[info_hash]:
            if key["peer_id"] == ip: peers[info_hash].remove(key)
    print(info_hash)
    db.execute("UPDATE torrent SET seeders=?,peers=? WHERE info_hash=?", (seeders, len(peers[info_hash]), str(info_hash)))
    print(db.execute("SELECT * FROM torrent").fetchall())
    db.commit()
    # Veraltete Peers entfernen (z. B. nach 30 Minuten)
    if info_hash in peers:
        peers[info_hash] = [p for p in peers[info_hash] if time.time() - p["last_seen"] < 1800]
    print(f"Peers for {info_hash}: {peers[info_hash]}")
    # Antwort mit Peer-Liste
    return jsonify({"interval": 1800, "peers": peers[info_hash]})
@app.route('/scrape', methods=['GET'])
def scrape():
    stats = {info_hash: len(peers[info_hash]) for info_hash in peers}
    return jsonify(stats)
@app.route("/stats", methods=["GET"])
def stats():
    return torrent_stats
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6969)
