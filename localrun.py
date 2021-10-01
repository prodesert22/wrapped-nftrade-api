import sys

from src.server import Server

def main():
    try:
        server = Server()
    except Exception as e:
        print(f'Error \n{e}')
        sys.exit(1)
    server.run_local()

if __name__ == '__main__':
    main()