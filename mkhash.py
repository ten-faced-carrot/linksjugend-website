import hashlib
import bencodepy

def get_info_hash(torrent_file):
    with open(torrent_file, 'rb') as f:
        torrent_data = f.read()
    metadata = bencodepy.decode(torrent_data)
    info = metadata[b'info']
    info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()
    return info_hash

info_hash = get_info_hash('meine_datei.torrent')
print(f"Info-Hash: {info_hash}")