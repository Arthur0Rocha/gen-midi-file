#!/usr/bin/python3
import re
import sys
from typing import List

from gen_midi_file import gen_out_string, write

DIVISIONS = 960

class TokenReader:
    def __init__(self, input: str) -> None:
        self.string = re.sub(r'[\s\t\n]+', ' ', input).strip()
        self.index = 0
    def next(self) -> str:
        if self.index >= len(self.string):
            return None
        token = ''
        while self.string[self.index] in [' ', '\t', '\n', '\r']:
            self.index += 1
            if self.index >= len(self.string):
                return None
        while True:
            if self.index >= len(self.string) or self.string[self.index] in [' ', ':', ';', '=']:
                self.index += 1
                break
            token += self.string[self.index]
            self.index += 1
        return token

    def digest_note(self, note_str: str, key):
        
        def calc(note_):
            if len(note_) < 3:
                n, o = note_, 0
            else:
                n, o = note_[:-2], int(note_[-2:])
            if n in drum_notes:
                n = drum_values[drum_notes.index(n)]
            else:
                if minor:
                    if n == '2':
                        n = '2+'
                    elif n == '3':
                        n = '3-'
                    elif n == '6':
                        n = '6-'
                    elif n == '7':
                        n = '7-'
                else:
                    if n == '2':
                        n = '2+'
                    elif n == '3':
                        n = '3+'
                    elif n == '6':
                        n = '6+'
                    elif n == '7':
                        n = '7-'
                n = tonic + int_semi_tones[intervals.index(n)]
            return n + 12 * o

        minor = 'm' in key
        tonic = key if not minor else key[:-1]

        tonic = 24 + ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].index(tonic)

        intervals =     ['1', '2-', '2+', '3-', '3+', '4', '4+', '5-', '5', '5+', '6-', '6+', '7-', '7+']
        int_semi_tones = [0 ,   1 ,   2 ,   3 ,   4 ,  5 ,   6 ,   6 ,  7 ,   8 ,   8 ,   9 ,  10 ,  11 ]
        drum_notes = ['ch', 'oh', 'sn', 'rg', 'bd', 'cr', 'ta', 'tb', 'tc', 'td', 'fl']
        drum_values = [42 ,  46 ,  38 ,  37 ,  35 ,  49 ,  50 ,  48 ,  47 ,  45 ,  43 ]
        durations = ['w', 'h', 'q', 'e', 's', 't']
        dura_vals = [ 4.,  2.,  1., 1/2, 1/4, 1/8]
        velocities = ['fff', 'ff', 'f', 'mf', 'mp', 'p', 'pp', 'ppp']
        velocitval = [ 127 , 116 , 105,  94 ,  83 , 72 ,  61 ,   50 ]
        
        note = ''
        velo = ''
        dura = ''
        posi = ''

        durv = 0.

        curr = 0

        while note_str[curr] not in ['m', 'p', 'f']:
            note += note_str[curr]
            curr += 1

        if '{' in note:
            note = note.replace('{', '').replace('}', '').split(',')
        else:
            note = [note]

        note = list(map(calc, note))

        while note_str[curr] in ['m', 'p', 'f']:
            velo += note_str[curr]
            curr += 1

        while note_str[curr] not in list(map(str,range(1,8))) + ['{']:
            if note_str[curr] == '.':
                durv *= 1.5
            else:
                durv += dura_vals[durations.index(note_str[curr])]
            dura += note_str[curr]
            curr += 1

        while curr < len(note_str):
            posi += note_str[curr]
            curr += 1

        if '{' in posi:
            posi = posi.replace('{', '').replace('}', '').split(',')
        else:
            posi = [posi]

        posi = list(map(float,posi))
        
        out = []
        aux = []
        for n in note:
            aux.append( (n, velocitval[velocities.index(velo)], durv) )

        for p in posi:
            for aux_ in aux:
                out.append( aux_ + (p,) )
        
        return out

def parse(input: str):
    reader = TokenReader(input)

    token = reader.next() # Must be sign
    assert token == 'sign'
    sign = reader.next()
    token = reader.next() # Must be key
    assert token == 'key'
    key = reader.next()
    token = reader.next() # Must be tempo
    assert token == 'tempo'
    tempo = int(reader.next())

    sections = {}
    play_order = []

    while True:
        token = reader.next()
        if token is None:
            break

        if token == 'config':
            # TODO
            while token != '||':
                token = reader.next()
        elif token == 'play':
            while True:
                last_token = token
                token = reader.next()
                if token is None:
                    break
                if re.match(r'^x[0-9]+$', token):
                    play_order += [last_token] * (int(token[1:]) - 1)
                else:
                    play_order += [token]
        else:
            section_name = token
            sections[section_name] = []
            while token != '.':
                token = reader.next()
                if token == '.':
                    break
                channel = {'D': 9, 'B': 8}[token] if token in ['D', 'B'] else int(token[1:])
                bar = -1
                while True:
                    token = reader.next()
                    if token == '||':
                        break
                    if token == '|':
                        bar += 1
                    else:
                        arr = reader.digest_note(token, key)
                        sections[section_name] += [(channel, bar, ) + tup for tup in arr]

    out = []

    aux_time = 0.

    for sec in play_order:
        bars = max([x[1] for x in sections[sec]]) + 1

        for event in sections[sec]:
            channel, bar, note, velocity, duration, position = event

            out.append( [aux_time + 4*bar + position - 1 + duration, channel, 'note_off', note,     0   ] )
            out.append( [aux_time + 4*bar + position - 1           , channel, 'note_on' , note, velocity] )
        aux_time += 4. * bars

    out = sorted(out, key=lambda v: v[0] + 1e-4*v[4])
    # print(str(out).replace('],','\n'))

    times = [0.] + [v[0] for v in out]
    for i in range(len(out)):
        out[i][0] = int((out[i][0] - times[i]) * DIVISIONS)
        


    return out, tempo

    # print(str(out).replace('),', '\n'))

if __name__ == "__main__":
    out, tempo = parse(open(sys.argv[1]).read())
    write(gen_out_string(out, tempo), sys.argv[2])
