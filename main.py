import threading

from play_sine import *
from vision import *
from shared import *



threading.Thread(target=generate_audio, daemon=True).start()
track_hand()