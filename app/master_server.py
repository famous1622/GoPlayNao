from database import *
import socket, thread, json

PLUGIN_VERSION = redis.get("plugin_version") or 1

class Connection(object):
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def push(self, obj):
        self.conn.sendall(json.dumps(obj))

    def getPacket(self, id):
        if hasattr(self, "packet_%s" % id):
            return getattr(self, "packet_%s" % id)
        return None

    def handle(self):
        while True:
            data = self.conn.recv(2048)
            if not data or not data.strip(): break

            try:
                obj = json.loads(data.strip())
            except:
                print "Error decoding data: `%s`" % data
                break

            if 'id' in obj:
                data = self.getPacket(obj['id'])(obj)
                if data:
                    self.push(data)

        self.conn.close()

    def packet_0(self, data):
        try:
            s = Server.select().where(Server.id == data.get("id")).get()
        except Server.DoesNotExist:
            return {"sucess": False, "msg": "Invalid Server ID!", "pid": 1}

        if s.hash != data.get("hash"):
            return {"success": False, "msg": "Invalid Server HASH!", "pid": 1}

        if self.addr not in s.hosts:
            return {"success": False, "msg": "That IP is not authorized for that server!", "pid": 1}

        version = int(data.get("version", 0))
        if PLUGIN_VERSION != version:
            msg = "Invalid Plugin Version, server has %s, master has %" (version, PLUGIN_VERSION)
            return {"success": False, "msg": msg}

        self.server = s

        if data.get("mid", -1) != -1:
            # TODO: grab existing match
            pass

        try:
            m = self.server.findWaitingMatch()
        except:
            return {"success": True, "has_match": False, "match": {}}

        return {"success": True, "has_match": True, "match": m.format(forServer=True)}

class Server(object):
    def __init__(self, host="", port=5595):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active = False

    def connect(self):
        self.s.bind((self.host, self.port))
        self.s.listen(1)
        self.active = True

    def loop(self):
        while self.active:
            con = Connection(self.s.accept())
            thread.start_new_thread(con.handle, (   ))

s = Server()
s.connect()
try:
    s.loop()
except:
    s.s.close()