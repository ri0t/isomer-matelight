# AVIO - The Python Audio Video Input Output Suite
# ================================================
# Copyright (C) 2015 riot <riot@c-base.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'riot'

import socket
import numpy as np

from circuits import Event, Timer, handler

from isomer.component import ConfigurableComponent
from isomer.logger import verbose, critical
from isomer.debugger import cli_register_event


class clear_ml(Event):
    """Send a black frame"""
    pass


class fade_out_ml(Event):
    """Initiate hard fading out because of content loss or similar."""
    pass


class refresh_ml(Event):
    """Periodically sent last frame, so there's no idle-mode when there are no updated frames"""
    pass


class transmit_ml(Event):
    """Transmit a frame to the display"""

    def __init__(self, frame, *args, **kwargs):
        super(transmit_ml, self).__init__(*args, **kwargs)
        self.frame = frame


class cli_test_matelight(Event):
    pass

GAMMA = 0.9
BRIGHTNESS = 0.9


class Matelight(ConfigurableComponent):
    """Matelight connector with some minimal extra facilities"""

    channel = "matelight"

    configprops = {
        'host': {'type': 'string', 'default': 'matelight'},
        'port': {'type': 'integer', 'default': 1337},
        'gamma': {'type': 'number', 'default': 1.1},
        'size': {
            'type': 'object',
            'properties': {
                'width': {'type': 'integer', 'default': 40},
                'height': {'type': 'integer', 'default': 16}
            },
            'default': {
                'width': 40,
                'height': 16
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super(Matelight, self).__init__('MATELIGHT', *args, **kwargs)
        self.log("Initializing matelight output")

        self.log('CONFIG:', self.config.__dict__, pretty=True)

        self.size = (self.config.size['width'], self.config.size['height'])
        self.gamma = self.config.gamma

        self.fading = None

        self.auto_restart = True
        self.output_broken = False

        self.last_frame = np.zeros(self.size, np.uint8)

        self.fade_timer = None
        self.init_timer = Timer(5, fade_out_ml()).register(self)
        self.refresh_timer = None

        self.fireEvent(cli_register_event("test_matelight", cli_test_matelight))

        self.cli_test_matelight(None)

    def started(self, *args):
        self.log("Starting matelight output on device %s:%i" % (self.host, self.port))

    def cli_test_matelight(self, event):
        self.log('Displaying test image')
        import os, cv2 as cv

        path = os.path.abspath(os.path.join(__file__, "../../testscreen.png"))
        self.log("PATH:", path, lvl=critical)
        test_image = cv.imread(path)
        test_image = cv.cvtColor(test_image, cv.COLOR_BGR2RGB)
        self._transmit(test_image)

    def fade_out_ml(self, event):
        if self.fading is None:
            self.fading = 20
            self.fade_timer = Timer(1 / 60.0, fade_out_ml(), persist=True).register(
                self)
        elif self.fading > 0:
            new_frame = (self.last_frame * 0.9).astype(np.uint8)
            self._transmit(new_frame)
            self.fading -= 1
        elif self.fading <= 0:
            self._clear()
            self.fade_timer.unregister()
            self.fading = None

    def _clear(self):
        self.log('Clearing')
        img = np.zeros((self.config.size['width'], self.config.size['height'], 3),
                       np.uint8)
        self._transmit(img)

    def clear_ml(self, event):
        self._clear()

    @handler('refresh_ml')
    def refresh_ml(self, event):
        self._transmit(self.last_frame)
        self.refresh_timer = Timer(1, refresh_ml()).register(self)

    def _transmit(self, image):
        self.log("New transmission request", lvl=verbose)
        if self.output_broken and not self.auto_restart:
            return

        self.log('Transmitting image, shape:', image.shape, lvl=verbose)

        self.last_frame = image

        if self.gamma != 1:
            image = (image * self.gamma).astype(np.uint8)

        ml_data = bytearray(image) + b"\00\00\00\00"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(ml_data, (self.config.host, self.config.port))
        except Exception as e:
            self.log("Error during matelight transmission: ", e)
            self.output_broken = True

        if self.refresh_timer is not None:
            self.refresh_timer.unregister()
        self.refresh_timer = Timer(1, refresh_ml()).register(self)

    @handler("transmit_ml")
    def transmit_ml(self, event):
        if self.fade_timer is not None:
            self.fade_timer.unregister()
            self.fade_timer = None

        self._transmit(event.frame)
