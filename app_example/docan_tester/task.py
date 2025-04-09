import threading
from time import sleep

class Task:
    def __init__(self, ctrl):
        self.thread = threading.Thread(target=self.run, args=(ctrl,))
        self.thread.setDaemon(True)
        self.thread.start()

    def run(self, ctrl):
        while True:
            # ctrl.set_spinbox(ctrl.cnt)
            a = ctrl.ui.spinbox.get()
            ctrl.ui.spinbox.set(float(a) + 1)
            sleep(1)

