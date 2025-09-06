#!/usr/bin/env python3
"""Load an audio file into memory and play its contents.

NumPy and the soundfile module (https://python-soundfile.readthedocs.io/)
must be installed for this to work.

This example program loads the whole file into memory before starting
playback.
To play very long files, you should use play_long_file.py instead.

This example could simply be implemented like this::

    import sounddevice as sd
    import soundfile as sf

    data, fs = sf.read('my-file.wav')
    sd.play(data, fs)
    sd.wait()

... but in this example we show a more low-level implementation
using a callback stream.

"""
import argparse
import threading
import shared
import sounddevice as sd
import soundfile as sf


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def play_wav():
    event = threading.Event()

    runs = 0
    try:
        data, fs = sf.read("audio/gmajor.wav", always_2d=True)
        global current_frame
        current_frame = 0

        def callback(outdata, frames, time, status):
            global current_frame
            if status:
                print(status)   # keep if you need diagnostics
            frames = int(frames)
            tail = len(data) - current_frame
            if tail >= frames:
                outdata[:] = data[current_frame:current_frame + frames] * shared.distance_between_hands
                print(shared.distance_between_hands)
                current_frame += frames
            else:
                outdata[:tail] = data[current_frame:]
                outdata[tail:frames] = data[:frames - tail]
                current_frame = frames - tail
            # keep current_frame in range
            if current_frame >= len(data):
                current_frame %= len(data)
                

        stream = sd.OutputStream(
            samplerate=fs, channels=data.shape[1],
            callback=callback, finished_callback=event.set)
        with stream:
            event.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        parser.exit('\nInterrupted by user')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))