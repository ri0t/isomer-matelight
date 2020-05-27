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

from circuits import Event

from isomer.events.system import authorized_event
from isomer.events.client import broadcast
from isomer.component import ConfigurableComponent, handler
from isomer.logger import verbose, critical
from isomer.debugger import cli_register_event
from .matelight import transmit_ml


class subscribe(authorized_event):
    pass

class cli_test_matelight_sim(Event):
    pass

class MatelightSim(ConfigurableComponent):
    """Matelight connector with some minimal extra facilities"""

    channel = "matelight"

    configprops = {
        'gamma': {'type': 'number', 'default': 0.5},
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
        super(MatelightSim, self).__init__('MATELIGHTSIM', *args, **kwargs)
        self.log("Initializing matelight simulator")

        self.size = (self.config.size['width'], self.config.size['height'])
        self.gamma = self.config.gamma

        self.clients = []

        self.fireEvent(cli_register_event("test_matelightsim", cli_test_matelight_sim))

    def _transmit(self, image):
        message = {
            'component': 'isomer.matelightsim',
            'action': 'update',
            'data': image.tolist()
        }
        self.fireEvent(
            broadcast("clientgroup", message, group=self.clients),
            "isomer-web"
        )

    def transmit_ml(self, event):
        self._transmit(event.frame)

    def cli_test_matelight_sim(self, event):
        self.log('Displaying test image')
        import os, cv2 as cv

        path = os.path.abspath(os.path.join(__file__, "../../testscreen.png"))
        test_image = cv.imread(path)
        test_image = cv.cvtColor(test_image, cv.COLOR_BGR2RGB)
        self.fireEvent(transmit_ml(test_image), "matelight")

    @handler(subscribe, channel="isomer-web")
    def subscribe(self, event):
        self.log("Subscription Event:", event.client)
        if event.client.uuid not in self.clients:
            self.clients.append(event.client.uuid)

    @handler("userlogout", channel="isomer-web")
    def userlogout(self, event):
        self.stop_client(event)

    @handler("clientdisconnect", channel="isomer-web")
    def clientdisconnect(self, event):
        """Handler to deal with a possibly disconnected simulation frontend

        :param event: ClientDisconnect Event
        """

        self.stop_client(event)

    def stop_client(self, event):
        try:
            if event.clientuuid in self.clients:
                self.clients.remove(event.clientuuid)

                self.log("Remote simulator disconnected")
            else:
                self.log("Client not subscribed")
        except Exception as e:
            self.log("Strange thing while client disconnected", e, type(e))
