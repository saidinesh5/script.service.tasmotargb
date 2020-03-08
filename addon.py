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
        requests.get(self._remoteUrl,
                     params = {'cmnd': 'SaveData 0'})
        requests.get(self._remoteUrl,
                     params = {'cmnd': 'Fade 1'})
        requests.get(self._remoteUrl,
                     params = {'cmnd': 'Speed 10'})
        self.enablePower(True)
    
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

def main():
    settings = Settings(addon)
    tasmota = Tasmota(settings)
    capture = xbmc.RenderCapture()
    capture.capture(32, 32)

    while not xbmc.abortRequested:
        xbmc.sleep(settings.refreshInterval)
        
        if settings.enabled:
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
