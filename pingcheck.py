import subprocess
import xbmcgui

def ping_server(server):
    try:
        output = subprocess.check_output(["ping", "-c", "1", server], universal_newlines=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    server = "api.anilibria.tv"
    if ping_server(server):
        xbmcgui.Dialog().notification('Ping Result', f'Server {server} is reachable', xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcgui.Dialog().notification('Ping Result', f'Server {server} is not reachable', xbmcgui.NOTIFICATION_ERROR)

if __name__ == "__main__":
    main()
