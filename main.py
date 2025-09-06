import threading

from play_sine import *
from play_wav import *
from vision import *
from pose import *
from shared import *


threading.Thread(target=play_wav, daemon=True).start()
track_body()