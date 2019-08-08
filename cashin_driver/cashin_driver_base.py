from abc import ABC, abstractmethod
from threading import Event, Thread

class CashinDriver(ABC):

    def __init__(self, callback_message):
        super().__init__()
        self._stop_cashin = Event()
        self._callback_message = callback_message

    def start_cashin(self):
        ''' async method, is stopped by calling stop_cashin '''
        self._stop_cashin.clear()
        thread = Thread(target=self._start_cashin, daemon=True)
        thread.start()
   
    @abstractmethod
    def _start_cashin(self):
        ''' this function is to be started in a separated thread and should loop while 
        self._stop_cashin is not set'''
        pass

    def stop_cashin(self):
        self._stop_cashin.set()
