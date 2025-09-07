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
import numpy as np


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

right_hand_prev_amp = 0.0
left_hand_prev_amp = 0.0

def play_wav():
    event = threading.Event()

        
    try:
        gmajor_data, gmajor_fs = sf.read("audio/Gmajor.wav", always_2d=True)
        emajor_data, emajor_fs = sf.read("audio/Emajor.wav", always_2d=True)

        global current_frame, amplitude_index, data_length
        data_length = min(len(gmajor_data), len(emajor_data))
        amplitude_index = 0
        current_frame = 0

        def callback(outdata, frames, time, status):
            global current_frame, amplitude_index, right_hand_prev_amp,left_hand_prev_amp, data_length
            
            if status:
                print(status)   # keep if you need diagnostics
            frames = int(frames)

            # loop back to start of file if at the end
            if data_length <= current_frame + frames:
                current_frame = 0


            left_hand_amplitude = shared.scale_value_to_range(shared.left_hand_height,0,0.85) if shared.tracking else 0
            right_hand_amplitude = shared.scale_value_to_range(shared.right_hand_height,0,0.85) if shared.tracking else 0
            
            gmajor_amplitude = (1-shared.right_hand_height) * shared.left_hand_height
            emajor_amplitude = shared.right_hand_height * shared.left_hand_height


            

        
            right_hand_ramp = np.linspace(right_hand_prev_amp, right_hand_amplitude, frames).reshape(-1, 1)
            left_hand_ramp = np.linspace(left_hand_prev_amp, left_hand_amplitude, frames).reshape(-1, 1)

            combined_data = (gmajor_data[current_frame:current_frame + frames] * right_hand_ramp +
                            emajor_data[current_frame:current_frame + frames] * left_hand_ramp)
            right_hand_prev_amp = right_hand_amplitude
            left_hand_prev_amp = left_hand_amplitude

            outdata[:] = combined_data
            current_frame += frames
            

        stream = sd.OutputStream(
            samplerate=gmajor_fs, channels=gmajor_data.shape[1],
            callback=callback, finished_callback=event.set)
        with stream:
            event.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        parser.exit('\nInterrupted by user')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))