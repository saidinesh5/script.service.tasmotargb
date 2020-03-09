import xbmc
import xbmcaddon
import xbmcgui
import os

import sys
import requests

addon = xbmcaddon.Addon();

def log(msg):
  xbmc.log("### [Taslight] - %s" % (msg,),level=xbmc.LOGDEBUG)

log( "Started")

# Additional Settings to consider:
# Shortcut key
# minimum/maximum brightness
# complementary vs. parallel color

class Settings:
    def __init__(self, addon):
        self._addon = addon
        self.enabled = True
        self.refreshInterval = addon.getSettingInt("refreshInterval")
        self.ip = addon.getSettingString("ip")
        self.port = addon.getSettingString("port")
        self.captureWidth = 32
        self.captureHeight = 32

class Tasmota:
    def __init__(self, settings):
        self._settings = settings
        self._r = 0
        self._g = 0
        self._b = 0
        self._powerEnabled = False
        self._remoteUrl = 'http://{}:{}/cm'.format(self._settings.ip, self._settings.port)
        
    def initialize(self):
        #TODO: Move these to Settings
        #Disable SaveData to flash to save the flash from too many writes
        #requests.get(self._remoteUrl,
        #             params = {'cmnd': 'SaveData 0'})
        requests.get(self._remoteUrl,
                     params = {'cmnd': 'Fade 1'})
        requests.get(self._remoteUrl,
                     params = {'cmnd': 'Speed 10'})
    
    def sendRGB(self, r, g, b):
        if r != self._r or g != self._g or b != self._b:
            self._r = r
            self._g = g
            self._b = b
            self._powerEnabled = True
            requests.get(self._remoteUrl,
                         params = {'cmnd': 'Color1 {}'.format(hex((int(r) << 16) + (int(g) << 8)  + int(b))[2:])} )
    
    def enablePower(self, status):
        if self._powerEnabled != status:
            self._powerEnabled = status
            requests.get(self._remoteUrl,
                         params = {'cmnd': 'Power {}'.format(['OFF', 'ON'][int(bool(status))])} )

class PlayerMonitor(xbmc.Player):
    def __init__(self, settings, capture, *args, **kwargs):
        super(xbmc.Player, self).__init__(*args, **kwargs)
        self._settings = settings
        self._capture = capture
        self._isPlaying = False

    def onPlayBackStopped(self):
        self._isPlaying = False

    def onPlayBackPaused(self):
        self._isPlaying = False

    def onPlayBackEnded(self):
        self._isPlaying = False

    def onPlayBackStarted(self):
        self._isPlaying = True
        self._capture.capture(self._settings.captureWidth,
                              self._settings.captureHeight)

    def onPlayBackResumed(self):
        self._isPlaying = True
        self._capture.capture(self._settings.captureWidth,
                              self._settings.captureHeight)

    def isPlaying(self):
        return self._isPlaying

def main():
    settings = Settings(addon)
    tasmota = Tasmota(settings)
    capture = xbmc.RenderCapture()
    player = PlayerMonitor(settings = settings, capture = capture)

    while not xbmc.abortRequested:
        xbmc.sleep(settings.refreshInterval)
        
        if settings.enabled and player.isPlaying():
            width = capture.getWidth()
            height = capture.getHeight()
            pixels = capture.getImage(1000)

            r,g,b = (0,0,0)
            if len(pixels) > 0:
                for y in range(height):
                    row = width * y * 4
                    for x in range(width):
                        r += pixels[row + x * 4 + 2]
                        g += pixels[row + x * 4 + 1]
                        b += pixels[row + x * 4]

                pixels_per_color = len(pixels)/4
                tasmota.sendRGB(r//pixels_per_color, g//pixels_per_color, b//pixels_per_color)
        else:
            tasmota.enablePower(False)

    tasmota.enablePower(False)

if ( __name__ == "__main__" ):
    main()
