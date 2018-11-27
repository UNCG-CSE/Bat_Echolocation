"""
Module for data extraction, preprocessing and visulization.

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
import csv
from batcall import batcall
from scipy import interpolate
from scipy.signal import savgol_filter
import random
import matplotlib.pyplot as plt
import os
import math
import matplotlib.cm as cm
import pandas as pd
from sklearn.cluster import KMeans

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
    return s.decode().strip('\00\t ')

def hpf_zc(times_s, freqs_hz, amplitudes, cutoff_freq_hz):
    if not cutoff_freq_hz or len(freqs_hz) == 0:
        return times_s, freqs_hz, amplitudes
    hpf_mask = np.where(freqs_hz > cutoff_freq_hz)
    junk_count = len(freqs_hz) - np.count_nonzero(hpf_mask)
    log.debug('HPF throwing out %d dots of %d (%.1f%%)', junk_count, len(freqs_hz), float(junk_count)/len(freqs_hz)*100)
    return times_s[hpf_mask], freqs_hz[hpf_mask], amplitudes[hpf_mask] if amplitudes is not None else None


def extract_anabat(fdir, hpfilter_khz=8.0, **kwargs):
    """
    Extract (times, frequencies, amplitudes, metadata) from Anabat sequence file
    From ZCANT package
    """
    amplitudes = None
    with open(fdir, 'rb') as f, contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
        size = len(m)

        # parse header
        data_info_pointer, file_type, tape, date, loc, species, spec, note1, note2 = struct.unpack_from(ANABAT_129_HEAD_FMT, m)
        data_pointer, res1, divratio, vres = struct.unpack_from(ANABAT_129_DATA_INFO_FMT, m, data_info_pointer)
        species = [_s(species).split('(', 1)[0]] if '(' in species.decode() else [s.strip() for s in _s(species).split(',')]  # remove KPro junk
#         species = [_s(species).split('(', 1)[0]] if '(' in species.decode() else [s.strip() for s in _s(species).split(',')]  #version for python 3
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
                if status == 1:
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
            
        while(len(freqs_hz) < len(off_mask)):
            freqs_hz=np.append(freqs_hz,0)
            
        times_s = masked_array(times_s, mask=off_mask).compressed()
        freqs_hz = masked_array(freqs_hz, mask=off_mask).compressed()
        
    min_, max_ = min(freqs_hz) if any(freqs_hz) else 0, max(freqs_hz) if any(freqs_hz) else 0
    log.debug('%s\tDots: %d\tMinF: %.1f\tMaxF: %.1f', basename(fdir), len(freqs_hz), min_/1000.0, max_/1000.0)

    times_s, freqs_hz, amplitudes = hpf_zc(times_s, freqs_hz, amplitudes, hpfilter_khz*1000)

    assert(len(times_s) == len(freqs_hz) == len(amplitudes or freqs_hz))
    return times_s, freqs_hz, amplitudes, metadata


def remove_noise(time, freq, dy_cutoff = 100,cutoff = 2000,avg_d = 3000,pulse_size = 30):
    """
     Remove noises for bat echolocation and return pulses points.
     Input: 
         time -- seconds
         frequency -- Khz
         dy_cutoff -- threshold of points vertical distance for smoothing holes
         cutoff -- averge of the difference of smoothed and the original points in a group
         avg_d -- threshold distance of two points to determine a pulse point group
         pulse_size -- threshold to determine how many points make up of a pulse
     Output:
         bcs -- a list of valid pulses with time and freqency
     
     """

    # Format zc_str to floats 
    zc_x = time.astype(np.float)
    zc_y = freq.astype(np.float)

    # Get dy
    prev_y = 0
    dy = list()
    for y in zc_y:
        dy.append(abs(y-prev_y))
        prev_y = y

    # Smooth holes
    i = 1
    while i < len(dy):
        if dy[i] > dy_cutoff:
            if dy[i - 1] < dy_cutoff:
                if dy[i + 1] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 1] + zc_y[i + 1])/2
                elif dy[i + 2] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 1] + zc_y[i + 2])/2
            elif dy[i - 2] < dy_cutoff:
                if dy[i + 1] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 2] + zc_y[i + 1])/2
                elif dy[i + 2] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 2] + zc_y[i + 2])/2
        i += 1

    # Smooth graph- Savitsky-Golay filter
    yhat2 = savgol_filter(zc_y, 27, 2)
    yhat3 = savgol_filter(zc_y, 17, 3)
    yhat4 = savgol_filter(zc_y, 17, 4) # best fit so far

    # Compare smoothed and original
    i = 0
    noiseless_y = list()
    noiseless_x = list()
    pulses = list()
    dy = list()
    bcs = list()
    while i < len(zc_x):
        j = i - 1
        average = 0

        # Find closely grouped points and clump them together
        while j < len(zc_x) and np.sqrt((zc_x[j] - zc_x[j - 1])**2 + (zc_y[j] - zc_y[j - 1])**2) <= avg_d:

            # Variance between smooth graph and original
            average += abs(zc_y[j] - yhat4[j])
            j += 1

        # Filter out pulses that are too small or too noisy
        if j - i > pulse_size and average / (j - i) <= cutoff:

            # Add pulse lines
            pulses.append(zc_x[i])
            bc = list()

            # Build noiseless graph
            while i < j:
                noiseless_y.append(zc_y[i])
                noiseless_x.append(zc_x[i])
                bc.append([zc_x[i], zc_y[i]])
                i += 1

            # Add pulse lines
            pulses.append(zc_x[i])
            bcs.append(bc)
        i += 1

    return bcs


def remove_noise2(time, freq, dy_cutoff = 100,cutoff = 2000,avg_d = 3000,pulse_size = 30,pulse_dy_avg=500):
    """
     Remove noises for bat echolocation and return pulses points.
     Input: 
         time -- seconds
         frequency -- Khz
         dy_cutoff -- threshold of points vertical distance for smoothing holes
         cutoff -- averge of the difference of smoothed and the original points in a group
         avg_d -- threshold distance of two points to determine a pulse point group
         pulse_size -- threshold to determine how many points make up of a pulse
     Output:
         bcs -- a list of valid pulses with time and freqency
     
     """

    # Format zc_str to floats 
    zc_x = time.astype(np.float)
    zc_y = freq.astype(np.float)

    # Get dy
    prev_y = 0
    dy = list()
    for y in zc_y:
        dy.append(abs(y-prev_y))
        prev_y = y

    # Smooth holes
    i = 2
    while i < (len(dy)-2):
        if dy[i] > dy_cutoff:
            if dy[i - 1] < dy_cutoff:
                if dy[i + 1] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 1] + zc_y[i + 1])/2
                elif dy[i + 2] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 1] + zc_y[i + 2])/2
            elif dy[i - 2] < dy_cutoff:
                if dy[i + 1] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 2] + zc_y[i + 1])/2
                elif dy[i + 2] < dy_cutoff:
                    zc_y[i] = (zc_y[i - 2] + zc_y[i + 2])/2
        i += 1

    # Smooth graph- Savitsky-Golay filter
#     yhat2 = savgol_filter(zc_y, 27, 2)
#     yhat3 = savgol_filter(zc_y, 17, 3)
#     yhat4 = savgol_filter(zc_y, 17, 4) # best fit so far
    yhat4 = zc_y
    # Compare smoothed and original
    i = 2
    noiseless_y = list()
    noiseless_x = list()
    pulses = list()
    bcs = list()
    pulse_dy=[]
    while i < (len(zc_x)-1):
        j = i - 1
        average = 0

        # Find closely grouped points and clump them together
#         while j < (len(zc_x)-1) and np.sqrt((zc_x[j] - zc_x[j - 1])**2 + (zc_y[j] - zc_y[j - 1])**2) <= avg_d:
        while j < (len(zc_x)-1) and np.sqrt( (zc_y[j] - zc_y[j - 1])**2) <= avg_d:

            # Variance between smooth graph and original
            average += abs(zc_y[j] - yhat4[j])
            j += 1

        # Filter out pulses that are too small or too noisy
        if j - i > pulse_size and average / (j - i) <= cutoff:

            # Add pulse lines
            pulses.append(zc_x[i])
            bc = list()

            # Build noiseless graph
            while i < j:
                noiseless_y.append(zc_y[i])
                noiseless_x.append(zc_x[i])
                bc.append([zc_x[i], zc_y[i]])
                pulse_dy.append(dy[i])
                i += 1
            # Add pulse lines
            pulses.append(zc_x[i])
#             a=pd.DataFrame(bc)
#             print(a.shape)
#             i=0
#             for y in a[1]:
#                 if i==0:
#                     prev_y=y
#                 else:
#                     pulse_dy.append(abs(y-prev_y))
#                     prev_y = y
#                 i+=1
#             bcs.append(bc)
            
            if np.mean(pulse_dy)<pulse_dy_avg:
                bcs.append(bc)
            pulse_dy=[]
        i += 1

    return bcs


def display_pulses(pulses, size, nrows=4,figsize=(10,8),rand_flag=True,cluster=None):
    """
    If rand_flag is True,
    plot a few random sample of the valid pulses;
    If rand_flag is False,
    plot valid pulses by clusters
     
     """
    # number of the pulses
    num = len(pulses)
    colors = cm.rainbow(np.linspace(0, 1, len(pd.Series(cluster).unique())))
    
    idx = random.sample(range(0, num), size)
    if not rand_flag:
        idx=range(0,num)
    ix=0
    
    fig, axes = plt.subplots(nrows=nrows, ncols=int(math.ceil(size*1.0/nrows)), figsize=figsize)
    if nrows==1:
        for ax in axes:
            i=idx[ix]
            ax.set_xlabel('time')
            ax.set_ylabel('frequency')
            if cluster is None:
                ax.set_title('pulse '+str(i))
                ax.scatter([l[0] for l in pulses[i]], [l[1] for l in pulses[i]], s=2)
            else:
                ax.set_title('cluster '+str(cluster[i])+' pulse: '+str(i))
                ax.scatter([l[0] for l in pulses[i]], [l[1] for l in pulses[i]], s=2,c=colors[cluster[i]])
            
            ix+=1
            if ix==size:
                break
    else:
        for ax1 in axes:
            for ax in ax1:
                i=idx[ix]
                ax.scatter([l[0] for l in pulses[i]], [l[1] for l in pulses[i]], s=2)
                ax.set_xlabel('time')
                ax.set_ylabel('frequency')
                if cluster is None:
                    ax.set_title('pulse '+str(i))
                    ax.scatter([l[0] for l in pulses[i]], [l[1] for l in pulses[i]], s=2)
                else:
                    ax.set_title('cluster ' + str(cluster[i])+' pulse: '+str(i))
                    ax.scatter([l[0] for l in pulses[i]], [l[1] for l in pulses[i]], s=2,c=colors[cluster[i]])
                ix+=1
                if ix==size:
                    break
            

    fig.tight_layout()
    
# def get_labeled_file(datadir, label):
#     """
#      Given a folder directory and the abnormal label, return the filenames with abnormal label in metadata.
     
#      """
#     info=list()
#     lfiles=list()
#     for filename in os.listdir(datadir):
#         if filename.endswith("#"):
#             signal=list(extract_anabat(datadir+filename))
#             signal.append(filename)
#             info.append(signal)
#             continue
#         else:
#             continue
            
#     for batinfo in info:
#         if label in str(batinfo[3]['species']): 
#             lfiles.append(batinfo[4]) 
#     return lfiles


def get_labeled_file(datadir, label):
    """
     Given a folder directory and the abnormal label, return the filenames with abnormal label in metadata.
     
     """
    info=list()
    lfiles=list()
    
    for root, dirs, files in os.walk(datadir):
        for filename in files:
            if filename.endswith("#"):
                signal=list(extract_anabat(root+'\\'+filename))
                signal.append(filename)
                info.append(signal)
                continue
            else:
                continue
            
    for batinfo in info:
        if label in str(batinfo[3]['species']): 
            lfiles.append(batinfo) 
    return lfiles

def get_dy_dy2(pulses):
    pulse_dy=[]
    pulse_dy2=[]
    for pulse in pulses:
        i=0
        dy=[]
        dy2=[]
        for dot in pulse:
            if i==0:
                prev_y=dot[1]
            elif i==1:
                prev_dy=dot[1]-prev_y
                dy.append(prev_dy)
                prev_y=dot[1]
            else:
                cur_dy=dot[1]-prev_y
                dy.append(cur_dy)
                dy2.append(cur_dy-prev_dy)
                prev_y=dot[1]
                prev_dy=cur_dy
                
            i+=1
        
        pulse_dy.append(dy)
        pulse_dy2.append(dy2)
    return pulse_dy,pulse_dy2

# get mean, sd, and five-number summary features for pulses
def get_features(data):
    features=pd.DataFrame()
    for elem in data:
        a=pd.DataFrame(elem).describe().iloc[1:8,].T
        features=features.append(a)
    return features

def bulk_processing(datadir):
    metadata=[]
    filenames=[]
    valid_pulses=[]
    for root, dirs, files in os.walk(datadir):
        for filename in files:
            if filename.endswith("#"):
                signal=list(extract_anabat(root+'\\'+filename))           
                signal.append(filename)
                pulses=remove_noise2(signal[0],signal[1])
                valid_pulses=valid_pulses+pulses
                metadata.append(signal[3])
                filenames.append(signal[4])
                continue
            else:
                continue

    return valid_pulses,metadata,filenames

def cluster_pulses(label_bat_info,number_cluster):
    pulses=[]
    for info in label_bat_info:
        pulse=remove_noise2(info[0],info[1],avg_d = 3200,pulse_size = 25,pulse_dy_avg=400)
        pulses=pulses+pulse
    b,c=get_dy_dy2(pulses)
    bf=get_features(b)
    cf=get_features(c)
    X=pd.concat([bf.iloc[:,3:6], cf.iloc[:,3:6]], axis=1)
    est = KMeans(number_cluster)  # 3 clusters
    est.fit(X)
    y_kmeans = est.predict(X)
    return X,y_kmeans,pulses
