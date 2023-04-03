import math
import os
import random
import threading
import time
import numpy as np
import spotipy
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec3, loadPrcFileData
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE

loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "window-title Music Visualizer")


class AudioData:
    def __init__(self, token, sample_rate=44100):
        self.sample_rate = sample_rate
        self.token = token
        self.sp = spotipy.Spotify(auth=token)
        self.track_id = None

    def get_current_track_id(self):
        playback = self.sp.current_playback()
        if playback is not None and playback["item"] is not None:
            track_id = playback["item"]["id"]
            return track_id
        else:
            return None

    def get_track_danceability(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["danceability"]
        return None

    def get_track_energy(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["energy"]
        return None

    def get_track_tempo(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["tempo"]
        return None

    def get_track_liveness(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["liveness"]
        return None

    def get_track_loudness(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["loudness"]
        return None

    def get_track_valence(self):
        if self.track_id is not None:
            features = self.sp.audio_features(self.track_id)
            if features is not None and len(features) > 0:
                return features[0]["valence"]
        return None

    def refresh_token(self, refresh_token):
        sp_oauth = spotipy.oauth2.SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE)
        new_tokens = sp_oauth.refresh_access_token(refresh_token)
        self.token = new_tokens['access_token']
        self.sp = spotipy.Spotify(auth=self.token)
        return new_tokens['refresh_token']


class Laser:
    def __init__(self, pos, vel, color):
        self.pos = pos
        self.vel = vel
        self.color = color


class LaserShow(ShowBase):
    def __init__(self, audio_data):
        ShowBase.__init__(self)
        self.strobe_on = True
        self.audio_data_instance = audio_data
        self.sample_rate = audio_data.sample_rate
        self.block_size = 1024
        self.num_lasers = 0
        self.lasers = []
        self.laser_nodes = []
        self.setBackgroundColor(0, 0, 0, 1)  # Set the background color to black
        self.init_lasers()
        self.taskMgr.add(self.update_lasers, "updateLasers")
        track_update_thread = threading.Thread(target=self.update_track)
        track_update_thread.daemon = True
        track_update_thread.start()
        self.tempo = None
        self.danceability = None
        self.energy = None
        self.valence = None
        self.loudness = None
        self.liveness = None
        self.strobe_phase = 0
        self.current_track_id = None

    def init_lasers(self):
        for i in range(self.num_lasers):
            pos = Vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1))
            vel = Vec3(np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1)) * 1.5
            color = (np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1), 1)
            laser = Laser(pos, vel, color)
            self.lasers.append(laser)
            model_path = os.path.join("models", "laser.egg")
            node = self.loader.loadModel(model_path)
            node.reparentTo(self.render)
            node.setPos(pos)
            node.setColor(*color)
            node.setScale(.002, 200, .000000005)
            self.laser_nodes.append(node)

    def update_track(self):
        refresh_token = None
        while True:
            try:
                track_id = self.audio_data_instance.get_current_track_id()

                if track_id is not None and track_id != self.current_track_id:
                    self.current_track_id = track_id
                    self.audio_data_instance.track_id = track_id
                    self.reset_lasers()
                    self.tempo = self.audio_data_instance.get_track_tempo()
                    self.danceability = self.audio_data_instance.get_track_danceability()
                    self.energy = self.audio_data_instance.get_track_energy()
                    self.loudness = self.audio_data_instance.get_track_loudness()
                    self.valence = self.audio_data_instance.get_track_valence()
                    self.liveness = self.audio_data_instance.get_track_liveness()
                    self.update_num_lasers()
                    print('Number of lasers:', self.num_lasers, 'Tempo:', self.tempo, 'Energy:', self.energy,
                          'Danceability:', self.danceability, 'Liveness', self.liveness, 'Valence:', self.valence,
                          'Loudness:', self.loudness, 'Track ID:', self.current_track_id)

            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 401:  # Access token expired
                    refresh_token = self.audio_data_instance.refresh_token(refresh_token)
                else:
                    raise e

            time.sleep(1)

    def reset_lasers(self):
        while len(self.lasers) < self.num_lasers:  # Add more lasers if needed
            pos = Vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1))
            vel = Vec3(np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1)) * 8
            color = (np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1), 1)
            laser = Laser(pos, vel, color)
            self.lasers.append(laser)
            model_path = os.path.join("models", "laser.egg")
            node = self.loader.loadModel(model_path)
            node.reparentTo(self.render)
            node.setPos(pos)
            node.setColor(*color)
            node.setScale(3, 200, 3)
            self.laser_nodes.append(node)

    def update_num_lasers(self):
        if self.energy is not None and self.tempo is not None:
            self.num_lasers = int(random.randint(0, 5) + (self.energy * (52 - 2)))
            # print(self.num_lasers)
            self.num_lasers = int(self.num_lasers * (1 - (120 / (self.tempo + 120))))
            while len(self.lasers) < self.num_lasers:  # Add more lasers if needed
                pos = Vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1))
                vel = Vec3(np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1)) * 8
                color = (np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1), 1)
                laser = Laser(pos, vel, color)
                self.lasers.append(laser)
                model_path = os.path.join("models", "laser.egg")
                node = self.loader.loadModel(model_path)
                node.reparentTo(self.render)
                node.setPos(pos)
                node.setColor(*color)
                node.setScale(.000009, 1000, .002)  # Scale the laser model to make it more visible .0009, 200, .0009
                self.laser_nodes.append(node)

    def update_lasers(self, task):
        dt = globalClock.getDt()

        if self.tempo is not None and self.danceability is not None and self.energy is not None:
            strobe_frequency = self.tempo / 60  # Convert BPM to Hz
            strobe_on_time = random.uniform(.03, 1) / strobe_frequency  # Set strobe on time to 3% - 100% of period of strobe frequency
            strobe_off_time = random.uniform(.03, 1) / strobe_frequency  # Set strobe off time to 3% - 100% of period of strobe frequency

            if self.strobe_on:
                self.strobe_phase += dt
                if self.strobe_phase >= strobe_on_time:
                    self.strobe_on = False
                    self.strobe_phase = 0
            else:
                self.strobe_phase += dt
                if self.strobe_phase >= strobe_off_time:
                    self.strobe_on = True
                    self.strobe_phase = 0

            num_strobe_lasers = int(self.energy * self.num_lasers)

            for i in range(len(self.lasers)):
                if i >= len(self.laser_nodes):  # Check if laser_nodes has enough elements
                    break

                laser = self.lasers[i]
                node = self.laser_nodes[i]

                # Modify laser velocity based on dancability and tempo
                laser.vel = laser.vel.normalized() * self.danceability * (1 - (120 / (self.tempo + 120))) * 2
                laser.pos += laser.vel * dt

                # Update the laser position with the sweeping motion
                sweep_angle = 5 * math.sin(2 * math.pi * self.tempo * task.time / (
                        60 * 25 * self.danceability)) * (1 - (
                        120 / (self.tempo + 120)))
                node.setHpr(sweep_angle, 0, 0)
                sweep_offset_x = .001 * math.sin(2 * math.pi * self.tempo * task.time / (60 * 1))
                sweep_offset_z = .001 * math.sin(2 * math.pi * self.tempo * task.time / (
                        60 * 1) + math.pi / 2)  # Add a phase shift for vertical sweep
                sweep_offset_y = .001 * math.sin(2 * math.pi * self.tempo * task.time / (
                        60 * 1) + math.pi / 2)
                node.setPos(laser.pos + Vec3(sweep_offset_x, sweep_offset_y, sweep_offset_z))

                if not (-1 < laser.pos.getX() < 1 and -1 < laser.pos.getY() < 1 and -1 < laser.pos.getZ() < 1):
                    laser.pos = Vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1))
                    laser.vel = Vec3(np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1),
                                     np.random.uniform(-0.1, 0.1)) * 1.5
                    node.setPos(laser.pos)

                # Update laser color based on strobe effect
                color = (np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1), 1)
                if i < num_strobe_lasers:
                    if self.strobe_on:
                        node.setColor(*color)
                    else:
                        node.setColor(*laser.color)
                else:
                    node.setColor(*laser.color)

        return task.cont


def start_visualizer(token):
    audio_data = AudioData(token, sample_rate=44100)
    while True:
        laser_show = LaserShow(audio_data)
        laser_show.run()
