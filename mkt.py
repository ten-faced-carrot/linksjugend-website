import libtorrent as lt
import time
import os

# Pfad zur Datei oder zum Ordner, den du seeden möchtest
file_path = "./torrent_cache/Over_2_Hours_of_SteamOS_Installations_GONE_WRONG_to_Conk_Out_To_p_YFpc6dDk0.mp4"
save_path = os.path.dirname(file_path)  # Wo sich die Datei befindet
torrent_file_path = "output.torrent"

# **1. Torrent erstellen**
fs = lt.file_storage()
print("Stashe...")
lt.add_files(fs, file_path)

print("Erstelle Torrent")
t = lt.create_torrent(fs)
t.set_creator("My Torrent Creator")
t.add_tracker("udp://tracker.opentrackr.org:1337/announce")  # Öffentlicher Tracker
t.set_priv(False)  # False = öffentliche Torrent-Datei

lt.set_piece_hashes(t, save_path)  # Generiert Hashes der Datei

torrent_data = t.generate()
with open(torrent_file_path, "wb") as f:
    f.write(lt.bencode(torrent_data))

print(f"Torrent erstellt: {torrent_file_path}")

# **2. Seeding starten**
ses = lt.session()
ses.listen_on(6881, 6891)  # Portbereich für Torrent

info = lt.torrent_info(torrent_file_path)
params = {
    "ti": info,
    "save_path": save_path,
}
print(params)

h = ses.add_torrent(params)

print("Seeding gestartet...")
print(f"Magnet-Link: {lt.make_magnet_uri(h.get_torrent_info())}")

# **3. Seed-Status anzeigen**
while True:
    s = h.status()
    print(f"Seeding... {s.num_peers} Peers verbunden, Upload: {s.upload_rate / 1024:.2f} KB/s")
    time.sleep(5)
