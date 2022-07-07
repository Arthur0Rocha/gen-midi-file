#!/usr/bin/python3

from typing import List

# Refer to https://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html

DIVISIONS = 960

# <Header Chunk> = <chunk type><length><format><ntrks><division>

def header_chunk():
    header = b'MThd'
    length = [0x00, 0x00, 0x00, 0x06]
    h_data = [
                0x00, 0x00, # Format (Can be 0, 1 or 2)
                0x00, 0x01, # N of tracks
                0x03, 0xC0  # Division (96 = 0x00 0x60, 960 = 0x03 0xC0)
             ]
    return header + bytes(length + h_data)


# <Track Chunk> = <chunk type><length><MTrk event>+
# <MTrk event> = <delta-time><event>
# <delta-time> is stored as a variable-length quantity.
# <event> = <MIDI event> | <sysex event> | <meta-event>
# <meta-event> ex: FF 2F 00 - End of Track

def track_chunk(inputs: List, tempo: int = 200):
    header = b'MTrk'
    
    last_status = None
    events_bytes = bytes([
                            0x00, 0xFF, 0x58, 0x04, # <delta-time>, FF 58 04 nn dd cc bb -> Time Signature
                            0x04, 0x02, 0x18, 0x08, # 4/4 time; 24 MIDI clocks/click, 8 32nd notes/ 24 MIDI clocks (24 MIDI clocks = 1 crotchet = 1 beat)
                            0x00, 0xFF, 0x51, 0x03, # <delta-time>, FF 51 03 tttttt -> Set Tempo (in microseconds per MIDI quarter-note)
                        ]) + to_length_in_bytes(int(60*1e6/tempo))[1:]

    for inp in inputs:
        # One or more events of type: <delta-time><event>
        delta_time, channel, evtype, param_note, value_vel = inp
        bdtime = to_var_len_encoding(delta_time)
        events_bytes += bdtime
        status, data = event_to_bytes(channel, evtype, param_note, value_vel)
        if status != last_status:
            events_bytes += status
            last_status = status
        events_bytes += data

    ending = bytes([0x00, 0xFF, 0x2F, 0x00])
    events_bytes += ending

    length = to_length_in_bytes(len(events_bytes))

    return header + length + events_bytes
    
def to_var_len_encoding(value: int):
    if value == 0:
        return bytes([value])
    out = []
    while value > 0:
        out.append(value & 0x7F)
        if len(out) > 1:
            out[-1] += 0x80
        value >>= 7
    return bytes(reversed(out))

def to_length_in_bytes(num: int):
    b0 = num & 0xFF
    b1 = (num & 0xFF00) >> 8
    b2 = (num & 0xFF0000) >> 16
    b3 = (num & 0xFF000000) >> 24
    return bytes([b3, b2, b1, b0])

def event_to_bytes(channel: int, evtype, param_note: int, value_vel: int):
    if evtype == 'note_on':
        status = 0b10010000 + (channel & 0xF)
        data = [0x7F & param_note, 0x7F & value_vel]
    elif evtype == 'note_off':
        status = 0b10000000 + (channel & 0xF)
        data = [0x7F & param_note, 0x7F & value_vel]
    elif evtype == 'CC':
        status = 0b10110000 + (channel & 0xF)
        data = [0x7F & param_note, 0x7F & value_vel]
    elif evtype == 'pgm_chg':
        status = 0b11000000 + (channel & 0xF)
        data = [0x7F & param_note]
    else:
        print("Event type still not supported")
        return None, []

    return bytes([status]), bytes(data)

def gen_out_string(inputs: List):
    return header_chunk() + track_chunk(inputs)

def write(output, filename):
    f = open(filename, 'wb')
    f.write(output)
    f.close()

if __name__ == "__main__":
    inputs = [
        (0, 9, 'note_on', 35, 127),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 35, 0),
        (0, 9, 'note_off', 42, 0),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        (0, 9, 'note_on', 42, 127),
        (0, 9, 'note_on', 38, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        (0, 9, 'note_off', 38, 0),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        
        (0, 9, 'note_on', 35, 127),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 35, 0),
        (0, 9, 'note_off', 42, 0),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        (0, 9, 'note_on', 42, 127),
        (0, 9, 'note_on', 38, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        (0, 9, 'note_off', 38, 0),
        (0, 9, 'note_on', 42, 127),
        (DIVISIONS, 9, 'note_off', 42, 0),
        (0, 9, 'note_on', 49, 127),
        
        

        # (delta_time, channel, evtype, param_note, value_vel),

    ]

    write(gen_out_string(inputs), './local-files/test.mid')