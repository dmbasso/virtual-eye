#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import socketserver
from ctypes import Structure, c_byte, c_float, c_int, sizeof

import bpy
from mathutils import Euler


HOST, PORT = "0.0.0.0", 9999


def get_list(s):
    llen = ord(s.recv(1))
    retv = []
    for i in range(llen):
        slen = ord(s.recv(1))
        retv.append(s.recv(slen).decode("ascii"))
    return retv


class EyeParameters(Structure):
     _fields_ = [ 
        ('eye', c_byte),
        ('retina', c_byte),
        ('yaw', c_float),
        ('pitch', c_float),
        ('aperture', c_float),
        ('distance', c_float),
        ('samples', c_int),
        ('format', c_int),
        ]


class EyeClientHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("New client {}.".format(self.client_address))
        socket = self.request.fileno()
        self.request.sendall(b"EyeServer")
        if self.request.recv(9) != b"EyeClient":
            print("Bad request, closed.")
            return
        cams, retinas = (get_list(self.request) for i in range(2))
        print(cams)
        print(retinas)
        e = EyeParameters()
        while True:
            if self.request.recv_into(e) != sizeof(e):
                print("Client closed the connection.")
                break
            if e.eye == -1 or e.eye == 0xff:
                print(e.eye)
                print("Client requested server termination.")
                EyeServer.quit = True
                break

            cam = bpy.data.objects[cams[e.eye]]
            bpy.context.scene.camera = cam
            bpy.context.scene.cycles.samples = e.samples
            bpy.context.scene.cycles.seed += 1
            cam.rotation_euler = Euler((e.yaw, e.pitch, 0))
            cam.data.dof_distance = e.distance
            cam.data.cycles.aperture_size = e.aperture
            cam.data.cycles.retina = retinas[e.retina]
            cam.data.cycles.retina_socket = socket | (e.format << 16)
            bpy.ops.render.render()


class EyeServer:
    quit = False
    server = socketserver.TCPServer((HOST, PORT), EyeClientHandler)
    @classmethod
    def serve(self):
        while not self.quit:
            self.server.handle_request()

try:
    EyeServer.serve()
except KeyboardInterrupt:
    print("EyeServer will shutdown now.")

