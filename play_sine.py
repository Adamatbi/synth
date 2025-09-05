#!/usr/bin/env python3
"""Play a sine signal."""
import argparse
import sys

import threading
import time
import numpy as np
import sounddevice as sd
import shared


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

base_freq = 400
base_amplitude = 0
start_idx = 0
phase = 0.0

def generate_audio():
    try:
        samplerate = sd.query_devices(None, 'output')['default_samplerate']

        def callback(outdata, frames, time_info, status):

            nonlocal samplerate
            global base_freq, phase
            if shared.location != (0,0):
                freq = base_freq# + (shared.location[0] * 100) - 50
                amplitude = base_amplitude + shared.distance#(shared.location[1] * 0.1)
            else:
                freq = base_freq
                amplitude = 0
          
            #print(shared.location)
            if status:
                print(status, file=sys.stderr)

            # phase increment per sample
            phase_inc = 2 * np.pi * freq / samplerate

            # generate continuous phase ramp
            phases = phase + phase_inc * np.arange(frames)
            out = np.sin(phases) * amplitude
            
            # update persistent phase (mod 2π to avoid overflow)
            phase = (phases[-1] + phase_inc) % (2 * np.pi)

            outdata[:] = out.reshape(-1, 1)


        with sd.OutputStream(device=None, channels=1, callback=callback,
                            samplerate=samplerate):
            while True:
                time.sleep(1000)
    except KeyboardInterrupt:
        parser.exit('')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))
