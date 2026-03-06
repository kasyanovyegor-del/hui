import sys
import subprocess
import socket
import threading
import queue
import ipaddress

def main():
    timeout = 0.5
    workers = 100
    no_ping = False
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'

    network = ipaddress.IPv4Network(f'{ip}/24', strict=False)

    q = queue.Queue()
    for ip in network.hosts():
        q.put(ip)

    results = []

    def worker():
        while True:
            try:
                ip = q.get_nowait()
            except queue.Empty:
                break
            host = str(ip)
            alive = False
            ports = []

            if not no_ping:
                if sys.platform.startswith('win'):
                    cmd = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), host]
                else:
                    cmd = ['ping', '-c', '1', '-W', str(int(timeout)), host]
                try:
                    subprocess.run(cmd, capture_output=True, timeout=timeout + 1, check=True)
                    alive = True
                except:
                    pass

            if not alive:
                try:
                    with socket.create_connection((host, 80), timeout=timeout):
                        alive = True
                        ports = [80]
                except:
                    pass

            if alive:
                results.append((host, ports))
            q.task_done()

    threads = []
    for _ in range(min(workers, q.qsize())):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    q.join()

    print(f' Найдено доступных хостов: {len(results)}')
    for host, ports in results:
            print(f'{host}')

if __name__ == '__main__':
    main()