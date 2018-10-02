"""
Module for reading zero-crossing files.

Extract (times, frequencies, amplitudes, metadata) from Anabat sequence file

"""

from __future__ import division

import io
import mmap
import struct
import unicodedata
import contextlib
from os.path import basename
from datetime import datetime
from collections import OrderedDict

import numpy as np
from numpy.ma import masked_array

from guano import GuanoFile, base64decode, base64encode

import logging
log = logging.getLogger(__name__)


Byte = struct.Struct('< B')


ANABAT_129_HEAD_FMT = '< H x B 2x 8s 8s 40s 50s 16s 73s 80s'  # 0x0: data_info_pointer, file_type, tape, date, loc, species, spec, note1, note2
ANABAT_129_DATA_INFO_FMT = '< H H B B'  # 0x11a: data_pointer, res1, divratio, vres
ANABAT_132_ADDL_DATA_INFO_FMT = '< H B B B B B B H 6s 32s'  # 0x120: year, month, day, hour, minute, second, second_hundredths, microseconds, id_code, gps_data

GuanoFile.register('ZCANT', 'Amplitudes',
                   lambda b64data: np.frombuffer(base64decode(b64data)),
                   lambda data: base64encode(data.tobytes()))

def _s(s):
    """Strip whitespace and null bytes from string"""
    return s.strip('\00\t ')

def hpf_zc(times_s, freqs_hz, amplitudes, cutoff_freq_hz):
    if not cutoff_freq_hz or len(freqs_hz) == 0:
        return times_s, freqs_hz, amplitudes
    hpf_mask = np.where(freqs_hz > cutoff_freq_hz)
    junk_count = len(freqs_hz) - np.count_nonzero(hpf_mask)
    log.debug('HPF throwing out %d dots of %d (%.1f%%)', junk_count, len(freqs_hz), float(junk_count)/len(freqs_hz)*100)
    return times_s[hpf_mask], freqs_hz[hpf_mask], amplitudes[hpf_mask] if amplitudes is not None else None


def extract_anabat(fname, hpfilter_khz=8.0, **kwargs):
    """Extract (times, frequencies, amplitudes, metadata) from Anabat sequence file"""
    amplitudes = None
    with open(fname, 'rb') as f, contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
        size = len(m)

        # parse header
        data_info_pointer, file_type, tape, date, loc, species, spec, note1, note2 = struct.unpack_from(ANABAT_129_HEAD_FMT, m)
        data_pointer, res1, divratio, vres = struct.unpack_from(ANABAT_129_DATA_INFO_FMT, m, data_info_pointer)
        species = [_s(species).split('(', 1)[0]] if '(' in species else [s.strip() for s in _s(species).split(',')]  # remove KPro junk
        metadata = dict(date=date, loc=_s(loc), species=species, spec=_s(spec), note1=_s(note1), note2=_s(note2), divratio=divratio)
        if file_type >= 132:
            year, month, day, hour, minute, second, second_hundredths, microseconds, id_code, gps_data = struct.unpack_from(ANABAT_132_ADDL_DATA_INFO_FMT, m, 0x120)
            try:
                timestamp = datetime(year, month, day, hour, minute, second, second_hundredths * 10000 + microseconds)
            except ValueError as e:
                log.exception('Failed extracting timestamp')
                timestamp = None
            metadata.update(dict(timestamp=timestamp, id=_s(id_code), gps=_s(gps_data)))
            if data_pointer - 0x150 > 12:  # and m[pos:pos+5] == 'GUANO':
                try:
                    guano = GuanoFile.from_string(m[0x150:data_pointer])
                    log.debug(guano.to_string())
                    amplitudes = guano.get('ZCANT|Amplitudes', None)
                except:
                    log.exception('Failed parsing GUANO metadata block')
            else:
                log.debug('No GUANO metadata found')
        log.debug('file_type: %d\tdata_info_pointer: 0x%3x\tdata_pointer: 0x%3x', file_type, data_info_pointer, data_pointer)
        log.debug(metadata)
        if res1 != 25000:
            raise ValueError('Anabat files with non-standard RES1 (%s) not yet supported!' % res1)

        # parse actual sequence data
        i = data_pointer   # byte index as we scan through the file (data starts at 0x150 for v132, 0x120 for older files)
        intervals_us = np.empty(2**14, np.dtype('uint32'))
        offdots = OrderedDict()  # dot index -> number of subsequent dots
        int_i = 0  # interval index

        while i < size:
            
            if int_i >= len(intervals_us):
                # Anabat files were formerly capped at 16384 dots, but may now be larger; grow
                intervals_us = np.concatenate((intervals_us, np.empty(2**14, np.dtype('uint32'))))

            byte = Byte.unpack_from(m, i)[0]

            if byte <= 0x7F:
                # Single byte is a 7-bit signed two's complement offset from previous interval
                offset = byte if byte < 2**6 else byte - 2**7  # clever two's complement unroll
                if int_i > 0:
                    intervals_us[int_i] = intervals_us[int_i-1] + offset
                    int_i += 1
                else:
                    log.warning('Sequence file starts with a one-byte interval diff! Skipping byte %x', byte)
                    #intervals.append(offset)  # ?!

            elif 0x80 <= byte <= 0x9F:
                # time interval is contained in 13 bits, upper 5 from the remainder of this byte, lower 8 bits from the next byte
                accumulator = (byte & 0b00011111) << 8
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0]
                intervals_us[int_i] = accumulator
                int_i += 1

            elif 0xA0 <= byte <= 0xBF:
                # interval is contained in 21 bits, upper 5 from the remainder of this byte, next 8 from the next byte and the lower 8 from the byte after that
                accumulator = (byte & 0b00011111) << 16
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0] << 8
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0]
                intervals_us[int_i] = accumulator
                int_i += 1

            elif 0xC0 <= byte <= 0xDF:
                # interval is contained in 29 bits, the upper 5 from the remainder of this byte, the next 8 from the following byte etc.
                accumulator = (byte & 0b00011111) << 24
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0] << 16
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0] << 8
                i += 1
                accumulator |= Byte.unpack_from(m, i)[0]
                intervals_us[int_i] = accumulator
                int_i += 1

            elif 0xE0 <= byte <= 0xFF:
                # status byte which applies to the next n dots
                status = byte & 0b00011111
                i += 1
                dotcount = Byte.unpack_from(m, i)[0]
                if status == DotStatus.OFF:
                    offdots[int_i] = dotcount
                else:
                    log.debug('UNSUPPORTED: Status %X for %d dots at dot %d (file offset 0x%X)', status, dotcount, int_i, i)

            else:
                raise Exception('Unknown byte %X at offset 0x%X' % (byte, i))

            i += 1

    intervals_us = intervals_us[:int_i]  # TODO: should we free unused memory?

    intervals_s = intervals_us * 1e-6
    times_s = np.cumsum(intervals_s)
    freqs_hz = 1 / (times_s[2:] - times_s[:-2]) * divratio
    freqs_hz[freqs_hz == np.inf] = 0  # TODO: fix divide-by-zero
    freqs_hz[freqs_hz < 4000] = 0
    freqs_hz[freqs_hz > 250000] = 0

    if offdots:
        n_offdots = sum(offdots.values())
        log.debug('Throwing out %d off-dots of %d (%.1f%%)', n_offdots, len(times_s), float(n_offdots)/len(times_s)*100)
        off_mask = np.zeros(len(intervals_us), dtype=bool)
        for int_i, dotcount in offdots.items():
            off_mask[int_i:int_i+dotcount] = True
        times_s = masked_array(times_s, mask=off_mask).compressed()
        freqs_hz = masked_array(freqs_hz, mask=off_mask).compressed()

    min_, max_ = min(freqs_hz) if any(freqs_hz) else 0, max(freqs_hz) if any(freqs_hz) else 0
    log.debug('%s\tDots: %d\tMinF: %.1f\tMaxF: %.1f', basename(fname), len(freqs_hz), min_/1000.0, max_/1000.0)

    times_s, freqs_hz, amplitudes = hpf_zc(times_s, freqs_hz, amplitudes, hpfilter_khz*1000)

    assert(len(times_s) == len(freqs_hz) == len(amplitudes or freqs_hz))
    return times_s, freqs_hz, amplitudes, metadata
