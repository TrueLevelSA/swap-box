# Swap-box
# Copyright (C) 2019  TrueLevel SA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
from threading import Lock

import strictyaml
from kivy.app import App
from kivy.config import Config as KivyConfig
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import RiseInTransition
from path import Path

# stays here because kivy global scope yolo
from src.components.recycle_view_crypto import TokensRecycleView
from src.screens.main import Manager, SyncPopup
from src_backends.config_tools import Config
from src_backends.config_tools import parse_args as parse_args
from src_backends.custom_threads.zmq_subscriber import ZMQSubscriber


def set_kivy_log_level(debug: bool):
    if debug:
        KivyConfig.set('kivy', 'log_level', 'debug')
    else:
        KivyConfig.set('kivy', 'log_level', 'warning')
    KivyConfig.write()


def set_window(fullscreen: bool):
    Window.size = (1280, 720)
    if fullscreen:
        Window.fullscreen = True
        Window.show_cursor = False


class TemplateApp(App):
    # with only eth/fiat, that's ok but might have to
    # try to share a variable in another way
    _fiat_to_eth = NumericProperty(0)
    _eth_to_fiat = NumericProperty(0)
    _selected_language = StringProperty('English')
    # _current_block = NumericProperty(-1)
    # _sync_block = NumericProperty(-1)
    _stablecoin_reserve = NumericProperty(-1e18)
    _eth_reserve = NumericProperty(-1e18)
    kv_directory = 'template'

    def __init__(self, config: Config):
        super().__init__()
        self._config = config

        self.thread_status = ZMQSubscriber(
            self._update_message_status,
            config.zmq.status,
            ZMQSubscriber.TOPIC_STATUS
        )

        self._machine_currency = config.note_machine.currency
        self._config = config
        self._manager = None
        self._fiat_to_eth = -1
        self._eth_to_fiat = -1
        self._popup_sync = None
        self._overlay_lock = Lock()
        self._popup_count = 0
        self._first_status_message_received = False
        languages_yaml = strictyaml.load(Path("lang_template.yaml").bytes().decode('utf8')).data
        self._languages = {k: dict(v) for k, v in languages_yaml.items()}

    def build(self):
        self._selected_language = next(iter(self._languages))  # get a language

        self._manager = Manager(self._config, transition=RiseInTransition())
        self.thread_status.start()
        return self._manager

    def change_language(self, selected_language):
        self._selected_language = selected_language

    def _update_message_pricefeed(self, message):
        """ only updates the _fiat_to_eth attribute """
        """ only dispatching the message to the right screen"""

        #
        # eth_reserve = msg_json['eth_reserve']
        # self._eth_reserve = int("0x" + eth_reserve, 16)
        # stablecoin_reserve = msg_json['token_reserve']
        # self._stablecoin_reserve = int("0x" + stablecoin_reserve, 16)
        #
        # self._buy_fee = msg_json['buy_fee']
        # self._sell_fee = msg_json['sell_fee']
        # # we use 20CHF as the standard amount people will buy
        # sample_amount = 20e18
        # # received values are in weis
        # one_stablecoin_buys = price_tools.get_buy_price(sample_amount, self._stablecoin_reserve,
        #                                                 self._eth_reserve) / sample_amount
        # self._fiat_to_eth = 1 / one_stablecoin_buys
        # sample_fiat_buys = price_tools.get_sell_price(sample_amount, self._eth_reserve, self._stablecoin_reserve)
        # self._eth_to_fiat = sample_amount / sample_fiat_buys

    def _update_message_status(self, message):
        self._first_status_message_received = True
        msg_json = json.loads(message)
        is_in_sync = msg_json["blockchain"]["is_in_sync"]

        self._show_sync_popup(is_in_sync)

    def _show_sync_popup(self, is_in_sync):
        if not is_in_sync:
            self._create_popup()
        if is_in_sync:
            self._delete_popup()

    def _create_popup(self):
        if self._popup_sync is None:
            self.before_popup()
            self._popup_sync = SyncPopup()
            self._popup_sync.open()

    def _delete_popup(self):
        if self._popup_sync is not None:
            self._popup_sync.dismiss()
            self._popup_sync = None
            self.after_popup()

    def on_stop(self):
        self._config.NODE_RPC.stop()

    # this method is ugly but we play with the raspicam overlay and have no choice
    def before_popup(self):
        """ used to cleanup the overlay in case a popup is opened while in scanning mode
        this method must be called before a popup is opened"""
        driver = self._config.QR_SCANNER
        # this will raise an error when the driver has no _overlay_auto_on attribute
        # aka we're not on raspberry pi + raspicam
        try:
            _ = driver._overlay_auto_on
        except:
            return
        with self._overlay_lock:
            self._popup_count += 1
            if driver._overlay_auto_on and self._popup_count == 1:
                driver._hide_overlay()

    # this method is ugly but we play with the raspicam overlay and have no choice
    def after_popup(self):
        """ used to show the overlay in case a popup is closed while in scanning mode
        this method must be called after a popup is closed"""
        driver = self._config.QR_SCANNER
        # this will raise an error when the driver has no _overlay_auto_on attribute
        # aka we're not on raspberry pi + raspicam
        try:
            _ = driver._overlay_auto_on
        except:
            return

        with self._overlay_lock:
            self._popup_count -= 1
            if driver._overlay_auto_on and self._popup_count == 0:
                driver._show_overlay()


if __name__ == '__main__':
    args = parse_args()
    config = Config(args.config)

    set_kivy_log_level(config.debug)
    set_window(config.is_fullscreen)

    app = TemplateApp(config)
    app.run()
