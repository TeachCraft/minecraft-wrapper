# -*- coding: utf-8 -*-

import socket
import threading
import time
import json
import requests

from utils.helpers import getjsonfile, putjsonfile, find_in_json
from utils.helpers import epoch_to_timestr, read_timestr
from utils.helpers import isipv4address

try:
    import utils.encryption as encryption
except ImportError:
    encryption = False

if encryption:
    from proxy.clientconnection import Client
    from proxy.packet import Packet

else:
    Client = False
    Packet = False


class Proxy:
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.javaserver = wrapper.javaserver
        self.log = wrapper.log
        self.config = wrapper.config
        self.encoding = self.wrapper.encoding
        self.serverpath = self.config["General"]["server-directory"]
        self.proxy_bind = self.wrapper.config["Proxy"]["proxy-bind"]
        self.proxy_port = self.wrapper.config["Proxy"]["proxy-port"]
        self.silent_ip_banning = self.wrapper.config["Proxy"]["silent-ipban"]
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.usingSocket = False
        self.clients = []
        self.skins = {}
        self.skinTextures = {}
        self.uuidTranslate = {}
        # removed deprecated proxy-data.json

        self.privateKey = encryption.generate_key_pair()
        self.publicKey = encryption.encode_public_key(self.privateKey)

        # requests is required wrapper-wide now, so no checks here for that...
        if not encryption and self.wrapper.proxymode:
            raise Exception("You must have the pycryto installed to run in proxy mode!")

    def host(self):
        # get the protocol version from the server
        while not self.wrapper.javaserver.state == 2:
            time.sleep(.2)

        if self.wrapper.javaserver.version_compute < 10702:
            self.log.warning("\nProxy mode cannot start because the server is a pre-Netty version:\n\n"
                             "http://wiki.vg/Protocol_version_numbers#Versions_before_the_Netty_rewrite\n\n"
                             "Server will continue in non-proxy mode.")
            self.wrapper.disable_proxymode()
            return

        if self.proxy_port == self.wrapper.javaserver.server_port:
            self.log.warning("Proxy mode cannot start because the wrapper port is identical to the server port.")
            self.wrapper.disable_proxymode()
            return

        try:
            self.pollserver()
        except Exception as e:
            self.log.exception("Proxy could not poll the Minecraft server - check server/wrapper configs? (%s)", e)

        # open proxy port to accept client connections
        while not self.usingSocket:
            self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.proxy_socket.bind((self.proxy_bind, self.proxy_port))
            except Exception as e:
                self.log.exception("Proxy mode could not bind - retrying in ten seconds (%s)", e)
                self.usingSocket = False
                time.sleep(10)
            self.usingSocket = True
            self.proxy_socket.listen(5)

        # accept clients and start their threads
        while not self.wrapper.halt:
            try:
                sock, addr = self.proxy_socket.accept()
            except Exception as e:
                self.log.exception("An error has occured while trying to accept a socket connection \n(%s)", e)
                continue

            banned_ip = self.isipbanned(addr)
            if self.silent_ip_banning and banned_ip:
                sock.shutdown(0)  # 0: done receiving, 1: done sending, 2: both
                continue

            # spur off client thread
            # self.server_temp = ServerConnection(self, ip, port)
            client = Client(self, sock, addr, banned=banned_ip)
            t = threading.Thread(target=client.handle, args=())
            t.daemon = True
            t.start()
            # self.clients.append(client)  # append later (login)
            self.removestaleclients()

    def removestaleclients(self):
        """only removes aborted clients"""
        for i, client in enumerate(self.clients):
            if self.clients[i].abort:
                if str(client.username) in self.wrapper.javaserver.players:
                    self.clients.pop(i)
                    del self.wrapper.javaserver.players[str(client.username)]

    def pollserver(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server_sock = socket.socket()
        server_sock.settimeout(5)
        server_sock.connect(("localhost", self.javaserver.server_port))
        packet = Packet(server_sock, self)

        packet.send(0x00, "varint|string|ushort|varint", (5, "localhost",
                                                          self.javaserver.server_port, 1))
        packet.send(0x00, "", ())
        packet.flush()
        self.wrapper.javaserver.protocolVersion = -1
        while True:
            pkid, original = packet.grabpacket()
            if pkid == 0x00:
                data = json.loads(packet.read("string:response")["response"].decode(self.encoding))  # py3
                self.wrapper.javaserver.protocolVersion = data["version"]["protocol"]
                self.wrapper.javaserver.version = data["version"]["name"]
                break
        server_sock.close()

    def getplayerby_username(self, username):
        """
        :rtype: var
        this is only to quiet complaints PyCharm makes because in places like this we return booleans
        sometimes when we can't get valid data and our calling methods check for these booleans.
        """
        for client in self.clients:
            if client.username == username:
                try:
                    return self.wrapper.javaserver.players[client.username]
                except Exception as e:
                    self.log.error("getplayerby_username failed to get player %s: \n%s",
                                   username, e)
                    return False
        self.log.debug("Failed to get any player by name of: %s", username)
        return False

    def getclientbyofflineserveruuid(self, uuid):
        """
        :param uuid: - MCUUID
        :return: the matching client
        """
        attempts = ["Search: %s" % str(uuid)]
        for client in self.clients:
            attempts.append("try: client-%s uuid-%s serveruuid-%s name-%s" %
                            (client, client.uuid.string, client.serveruuid.string, client.username))
            if client.serveruuid.string == str(uuid):
                self.uuidTranslate[uuid] = client.uuid.string
                return client
        self.log.debug("getclientbyofflineserveruuid failed: \n %s", attempts)
        self.log.debug("POSSIBLE CLIENTS: \n %s", self.clients)
        return False  # no client

    def getplayerby_eid(self, eid):
        """
        :rtype: var
        this is only to quiet complaints PyCharm makes because in places like this we return booleans
        sometimes when we can't get valid data and our calling methods check for these booleans.
        """
        for client in self.clients:
            if client.server.eid == eid:
                try:
                    return self.wrapper.javaserver.players[client.username]
                except Exception as e:
                    self.log.error("getplayerby_eid failed to get player %s: \n%s",
                                   client.username, e)
                    return False
        self.log.debug("Failed to get any player by client Eid: %s", eid)
        return False

    def banplayer(self, playername, reason="Banned by an operator", source="Wrapper", expires="forever"):
        """
        * placeholder code for future feature* - This will be the pre-1.7.6 ban method (name only).
        This is not used by code yet... for banning by username only for pre-uuid servers
        :param playername:
        :param reason:
        :param source:
        :param expires:
        :return:
        """
        print(" # TODO - legacy server support (pre-1.7.6) %s%s%s%s%s" % (self, reason, source, expires, playername))

    def getuuidbanreason(self, uuid):
        """
        :param uuid: uuid of player as string
        :return: string representing ban reason
        """
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist:  # in this case we just care if banlist exits in any fashion
            banrecord = find_in_json(banlist, "uuid", uuid)
            return "%s by %s" % (banrecord["reason"], banrecord["source"])
        return "Banned by server"

    def banuuid(self, uuid, reason="The Ban Hammer has spoken!", source="Wrapper", expires=False):
        """
        Ban someone by UUID  This is the 1.7.6 way to ban..
        :param uuid - uuid to ban (MCUUID)
        :param reason - text reason for ban
        :param source - source (author/op) of ban.
        :param expires - expiration in seconds from epoch time.  Field exits but not used by the vanilla server
        - implement it for tempbans in future?  Gets converted to string representation in the ban file.

        This probably only works on 1.7.10 servers or later
        """
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                banlist = dict()  # ensure valid dict before operating on it
            if find_in_json(banlist, "uuid", str(uuid)):
                return "player already banned"  # error text
            else:
                if expires:
                    try:
                        expiration = epoch_to_timestr(expires)
                    except Exception as e:
                        print('Exception: %s' % e)
                        return "expiration date invalid"  # error text
                else:
                    expiration = "forever"
                name = self.wrapper.uuids.getusernamebyuuid(uuid.string)
                banlist.append({"uuid": uuid.string,
                                "name": name,
                                "created": epoch_to_timestr(time.time()),
                                "source": source,
                                "expires": expiration,
                                "reason": reason})
                if putjsonfile(banlist, "banned-players", self.serverpath):
                    self.wrapper.javaserver.console("kick %s Banned: %s" % (name, reason))
                    return "Banned %s: %s" % (name, reason)
                return "Could not write banlist to disk"
        else:
            return "Banlist not found on disk"

    def banuuidraw(self, uuid, username, reason="The Ban Hammer has spoken!", source="Wrapper", expires=False):
        """
        Ban a raw uuid/name combination with no mojang error checks
        :param uuid - uuid to ban (MCUUID)
        :param username - Name of player to ban
        :param reason - text reason for ban
        :param source - source (author/op) of ban.
        :param expires - expiration in seconds from epoch time.  Field exits but not used by the vanilla server
        - implement it for tempbans in future?  Gets converted to string representation in the ban file.

        This probably only works on 1.7.10 servers or later
        """
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                banlist = dict()  # ensure valid dict before operating on it
            if find_in_json(banlist, "uuid", str(uuid)):
                return "player already banned"  # error text
            else:
                if expires:
                    try:
                        expiration = epoch_to_timestr(expires)
                    except Exception as e:
                        print('Exception: %s' % e)
                        return "expiration date invalid"  # error text
                else:
                    expiration = "forever"
                banlist.append({"uuid": uuid.string,
                                "name": username,
                                "created": epoch_to_timestr(time.time()),
                                "source": source,
                                "expires": expiration,
                                "reason": reason})
                if putjsonfile(banlist, "banned-players", self.serverpath):
                    self.log.info("kicking %s... %s", username, reason)
                    self.wrapper.javaserver.console("kick %s Banned: %s" % (username, reason))
                    return "Banned %s: %s - %s" % (username, uuid, reason)
                return "Could not write banlist to disk"
        else:
            return "Banlist not found on disk"

    def banip(self, ipaddress, reason="The Ban Hammer has spoken!", source="Wrapper", expires=False):
        """
        Ban an IP address (IPV-4)
        :param ipaddress - ip address to ban
        :param reason - text reason for ban
        :param source - source (author/op) of ban.
        :param expires - expiration in seconds from epoch time.  Field exits but not used by the vanilla server
        - implement it for tempbans in future?  Gets converted to string representation in the ban file.

        This probably only works on 1.7.10 servers or later
        """
        if not isipv4address(ipaddress):
            return "Invalid IPV4 address: %s" % ipaddress
        banlist = getjsonfile("banned-ips", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                banlist = dict()  # ensure valid dict before operating on it
            if find_in_json(banlist, "ip", ipaddress):
                return "address already banned"  # error text
            else:
                if expires:
                    try:
                        expiration = epoch_to_timestr(expires)
                    except Exception as e:
                        print('Exception: %s' % e)
                        return "expiration date invalid"  # error text
                else:
                    expiration = "forever"
                banlist.append({"ip": ipaddress,
                                "created": epoch_to_timestr(time.time()),
                                "source": source,
                                "expires": expiration,
                                "reason": reason})
                if putjsonfile(banlist, "banned-ips", self.serverpath):
                    banned = ""
                    for i in self.wrapper.javaserver.players:
                        player = self.wrapper.javaserver.players[i]
                        if str(player.client.ip) == str(ipaddress):
                            self.wrapper.javaserver.console("kick %s Your IP is Banned!" % player.username)
                            banned += "\n%s" % player.username
                    return "Banned ip address: %s\nPlayers kicked as a result:%s" % (ipaddress, banned)
                return "Could not write banlist to disk"
        else:
            return "Banlist not found on disk"

    def pardonip(self, ipaddress):
        if not isipv4address(ipaddress):
            return "Invalid IPV4 address: %s" % ipaddress
        banlist = getjsonfile("banned-ips", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                return "No IP bans have ever been recorded."
            banrecord = find_in_json(banlist, "ip", ipaddress)
            if banrecord:
                for x in banlist:
                    if x == banrecord:
                        banlist.remove(x)
                if putjsonfile(banlist, "banned-ips", self.serverpath):
                    return "pardoned %s" % ipaddress
                return "Could not write banlist to disk"
            else:
                return "That address was never banned"  # error text

        else:
            return "Banlist not found on disk"  # error text

    def pardonuuid(self, uuid):
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                return "No bans have ever been recorded..?"
            banrecord = find_in_json(banlist, "uuid", str(uuid))
            if banrecord:
                for x in banlist:
                    if x == banrecord:
                        banlist.remove(x)
                if putjsonfile(banlist, "banned-players", self.serverpath):
                    name = self.wrapper.uuids.getusernamebyuuid(str(uuid))
                    return "pardoned %s" % name
                return "Could not write banlist to disk"
            else:
                return "That person was never banned"  # error text
        else:
            return "Banlist not found on disk"  # error text

    def pardonname(self, username):
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist is not False:  # file and directory exist.
            if banlist is None:  # file was empty or not valid
                return "No bans have ever been recorded..?"
            banrecord = find_in_json(banlist, "name", str(username))
            if banrecord:
                for x in banlist:
                    if x == banrecord:
                        banlist.remove(x)
                if putjsonfile(banlist, "banned-players", self.serverpath):
                    return "pardoned %s" % username
                return "Could not write banlist to disk"
            else:
                return "That person was never banned"  # error text
        else:
            return "Banlist not found on disk"  # error text

    def isuuidbanned(self, uuid):  # Check if the UUID of the user is banned
        banlist = getjsonfile("banned-players", self.serverpath)
        if banlist:  # in this case we just care if banlist exits in any fashion
            banrecord = find_in_json(banlist, "uuid", str(uuid))
            if banrecord:
                if read_timestr(banrecord["expires"]) < int(time.time()):  # if ban has expired
                    pardoning = self.pardonuuid(str(uuid))
                    if pardoning[:8] == "pardoned":
                        self.log.info("UUID: %s was pardoned (expired ban)", str(uuid))
                        return False  # player is "NOT" banned (anymore)
                    else:
                        self.log.warning("isuuidbanned attempted a pardon of uuid: %s (expired ban), "
                                         "but it failed:\n %s", uuid, pardoning)
                return True  # player is still banned
        return False  # banlist empty or record not found

    def isipbanned(self, ipaddress):  # Check if the IP address is banned
        banlist = getjsonfile("banned-ips", self.serverpath)
        if banlist:  # in this case we just care if banlist exits in any fashion
            for record in banlist:
                _ip = record["ip"]
                if _ip in ipaddress:
                    _expires = read_timestr(record["expires"])
                    if _expires < int(time.time()):  # if ban has expired
                        pardoning = self.pardonip(ipaddress)
                        if pardoning[:8] == "pardoned":
                            self.log.info("IP: %s was pardoned (expired ban)", ipaddress)
                            return False  # IP is "NOT" banned (anymore)
                        else:
                            self.log.warning("isipbanned attempted a pardon of IP: %s (expired ban), "
                                             "but it failed:\n %s", ipaddress, pardoning)
                    return True  # IP is still banned
        return False  # banlist empty or record not found

    def getskintexture(self, uuid):
        """
        Args:
            uuid: uuid (accept MCUUID or string)
        Returns:
            skin texture (False if request fails)
        """
        if "MCUUID" in str(type(uuid)):
            uuid = uuid.string
        if uuid not in self.skins:
            return False
        if uuid in self.skinTextures:
            return self.skinTextures[uuid]
        skinblob = json.loads(self.skins[uuid].decode("base64"))
        if "SKIN" not in skinblob["textures"]:  # Player has no skin, so set to Alex [fix from #160]
            skinblob["textures"]["SKIN"] = {
                "url": "http://hydra-media.cursecdn.com/minecraft.gamepedia.com/f/f2/Alex_skin.png"
            }
        r = requests.get(skinblob["textures"]["SKIN"]["url"])
        if r.status_code == 200:
            self.skinTextures[uuid] = r.content.encode("base64")
            return self.skinTextures[uuid]
        else:
            self.log.warning("Could not fetch skin texture! (status code %d)", r.status_code)
            return False
