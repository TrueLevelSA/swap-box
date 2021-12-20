from enum import Enum
from typing import Optional

from kivy.app import App
from kivy.lang import Builder

from src.components.boxlayout_bg import BoxLayoutBackground
from src.components.label_sb import LabelSB

Builder.load_string('''    
<ImageStep@Image>
    disabled: True
    color: color_gray_3 if self.disabled else color_off_white

<StepLabel@LabelLeft>
    disabled: True
    color: color_gray_3 if self.disabled else color_off_white

<StepsWidget>
    padding: (30, 30)
    background_color: color_darker_black
    BoxLayout:
        orientation: "vertical"
        spacing: 10
        
        LabelLeft:
            size_hint_y: 0.1
            text_id: 'your_selection'
        
        BoxLayout:
            orientation: "horizontal"
        
            BoxLayout:
                orientation: "vertical"
                size_hint_x: 0.4
        
                ImageStep:
                    id: img_action
                    source: "assets/img/action.png"
                ImageStep:
                    id: img_network
                    source: "assets/img/network.png"
                ImageStep:
                    id: img_currency
                    source: "assets/img/currency.png"
                ImageStep:
                    id: img_wallet
                    source: "assets/img/wallet.png"
                ImageStep:
                    id: img_amount
                    source: "assets/img/cash.png"
        
            BoxLayout:
                orientation: "vertical"
        
                StepLabel:
                    id: label_action
                StepLabel:
                    id: label_network
                    text_id: "step_network" if self.disabled else ""
                StepLabel:
                    id: label_currency
                    text_id: "step_currency" if self.disabled else ""
                StepLabel:
                    id: label_wallet
                    text_id: "step_wallet" if self.disabled else ""
                StepLabel:
                    id: label_amount
                    text_id: "step_amount" if self.disabled else ""
''')


class Action(Enum):
    BUY = 0
    SELL = 1


class Wallet(Enum):
    PAPER = 0
    HOT = 1


class TransactionOrder:
    """A transaction order representing what the user want to do.

    It is gradually built screen after screen, until when it's ready and will be sent to the connector.

    Attributes:
        action          The type of order, buy or sell.
        token           The token the user want to buy.
        backend         The backend of the token.
        to              To whom the token will be forwarded while/after the tx.
        amount_fiat     The amount of fiat the user cashed in.
        amount_crypto   The amount of crypto the user has received.
        wallet_type     The type of the wallet.
    """

    def __init__(self):
        self.action: Optional[Action] = None
        self.token: Optional[str] = None
        self.backend: str = None
        self.to: Optional[str] = None
        self.amount_fiat: Optional[int] = None
        self.amount_crypto: Optional[int] = None
        self.wallet_type: Optional[Wallet] = None


class StepsWidget(BoxLayoutBackground):

    def __init__(self, **kwargs):
        super(StepsWidget, self).__init__(**kwargs)
        self._app = App.get_running_app()

    def set_tx_order(self, tx_order: TransactionOrder):

        if tx_order.action is not None:
            self.ids.img_action.disabled = False
            l: LabelSB = self.ids.label_action
            l.disabled = False

            if tx_order.action == Action.BUY:
                l.text_id = "step_action_deposit"
            elif tx_order.action == Action.SELL:
                l.text_id = "step_action_withdraw"

        if tx_order.backend is not None:
            self.ids.img_network.disabled = False
            l: LabelSB = self.ids.label_network
            l.disabled = False
            l.text = tx_order.backend

        if tx_order.token is not None:
            self.ids.img_currency.disabled = False
            l: LabelSB = self.ids.label_currency
            l.disabled = False
            l.text = tx_order.token

        if tx_order.wallet_type is not None:
            self.ids.img_wallet.disabled = False
            l: LabelSB = self.ids.label_wallet
            l.disabled = False
            l.text = tx_order.wallet_type

        if tx_order.amount_fiat is not None and tx_order.amount_fiat > 0:
            self.ids.img_amount.disabled = False
            l: LabelSB = self.ids.label_amount
            l.disabled = False
            l.text = self._app.format_fiat_price(tx_order.amount_fiat)
