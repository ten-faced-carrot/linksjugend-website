import libtorrent as lt
import os

tracked = []
active = []
save_path = "/tmp"

ses = lt.session()
ses.listen_on(6881, 6891)

for file in os.listdir("lt"):
    if file not in tracked:
        if "magnet" in os.listdir("lt/"+file):

            params = lt.parse_magnet_uri(open("lt/"+file+"/magnet").read())
            params.save_path = save_path
            handle = ses.add_torrent(params)
            
            print("Metadaten abrufen...")
            i = 0
            while not handle.has_metadata():
                ...
            ti = handle.get_torrent_info()
            print("MEtadaten erhalten!")
        else: info = lt.torrent_info(f'lt/{file}/{os.listdir("lt/"+file)[0]}')
        tracked.append(file)
        params = {
            "ti": info,
            "save_path": save_path,
            "seed_mode": True  # Direkt als Seeder starten
        }
        active.append(ses.add_torrent(params))

while True:
    for h in tracked:
        s = h.status()
        print(f"Seeding... {s.num_peers} Peers verbunden, Upload: {s.upload_rate / 1024:.2f} KB/s", end="\r")