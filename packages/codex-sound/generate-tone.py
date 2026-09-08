"""Generate the original, gentle three-note Codex completion cue."""
import math
from pathlib import Path
import struct
import sys
import wave

RATE = 48000
# A short rising tu-lu-lu, with a slightly longer final note.
NOTES = [(523.25, 0.13), (659.25, 0.13), (880.0, 0.23)]
samples = []
for frequency, duration in NOTES:
    count = round(RATE * duration)
    for i in range(count):
        t = i / RATE
        attack = min(1.0, t / 0.012)
        release = min(1.0, (duration - t) / 0.065)
        envelope = attack * release * math.exp(-2.5 * t)
        phase = 2 * math.pi * frequency * t
        tone = math.sin(phase) + 0.16 * math.sin(2 * phase)
        samples.append(round(32767 * 0.35 * envelope * tone))
    samples.extend([0] * round(RATE * 0.045))

with wave.open(str(Path(sys.argv[1])), 'wb') as output:
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(RATE)
    output.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
