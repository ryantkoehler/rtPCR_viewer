#!/usr/bin/env python
# 3/18/18 RTK; Place for needed general util functions
# 8/17/19 RTK; V0.22; Clean up code some (pylint; DEBUG)
#
# Conventions
#   (plate)     Well = position like 'A3' 'G4'
#   (grid)      Cell = coords like (0,2) (5,4)
#   (dataframe) Cols = columns in (multi-channel) dataset like 'A3_1' 'G4_1'
#   (dataset)   Channel = channel label string like 'Channel_1'
#   (dataset)   Chidx = channel 1-based int index
#

import json
import re


# ------------------------------------------------
# json IO
def dict_from_json(fname, failok=False):
    try:
        with open(fname, 'r') as IFILE:
            dic = json.load(IFILE)
            return dic
    except Exception as e:
        if failok:
            return None
        else:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise


def dict_to_json(dic, fname, failok=False):
    try:
        with open(fname, 'w') as OFILE:
            json.dump(dic, OFILE)
            return True
    except Exception as e:
        if failok:
            return None
        else:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise


# ------------------------------------------------
# Variable type matching / parsing functions
INT_PATTERN     = re.compile('\d+')
FLOAT_PATTERN   = re.compile('\d+\.\d+')
# hex RGB from https://stackoverflow.com/questions/1636350/how-to-identify-a-given-string-is-hex-color-format?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
COLOR_PATTERN   = re.compile('^#(?:[0-9a-fA-F]{3}){1,2}$')


def re_float(s):
    match = FLOAT_PATTERN.match(str(s))
    if match:
        return float(s)


def re_int(s):
    match = INT_PATTERN.match(str(s))
    if match:
        return int(s)


def re_number(s):
    n = re_float(s)
    if n is None:
        n = re_int(s)
    return n


def re_color(s):
    # Match color as hex like '#80a0c0'
    match = COLOR_PATTERN.match(str(s))
    if match:
        return s


# ------------------------------------------------
# Label utils
#
# Well, cell, dataset (dataframe) column interconversions
#
# General 96 well-to-cell mapping dicts
#   Well to Cell maps 'B3' >--> (1,2)
W2CMAP = {}
for i, r in enumerate(list('ABCDEFGH')):
    for c in range(12):
        W2CMAP[r + str(c+1)] = (i, c)

#   Cell to Well maps (1,2) >--> 'B3'
C2WMAP = {v: k for k, v in W2CMAP.items()}


def chan_1index_col_suf(idx):
    """ Plate df channel column name suffix for 1-based channel index
    e.g. First channel with 1-based index 1 ends with '_0'
    """
    return chan_index_col_suf(idx-1)


def chan_index_col_suf(idx):
    """ Plate df channel column name suffix for channel index
    e.g. First channel with index 0 ends with '_0'
    """
    return '_' + str(idx)


def channel_1index_label(idx):
    """ String lable for 1-based channel index; 0 = all
    e.g. First channel with 1-based index 1 ends with '_1'
    """
    if idx < 0:
        lab = 'None'
    elif idx == 0:
        lab = 'All'
    else:
        lab = 'Channel_' + str(idx)
    return lab


def index_from_chanlab(lab):
    """ Get 0-based int index from 1-based channel label
    e.g. 'Channel_1' gives 0
    """
    return int(lab.split('_')[1]) - 1


def plate96_row_label_list():
    return list('ABCDEFGH')


def plate96_col_label_list():
    return [str(v+1) for v in range(12)]


def plate96_well_list():
    llis = []
    for r in plate96_row_label_list():
        for c in plate96_col_label_list():
            llis.append(r+c)
    return llis


def plate96_cell_list():
    clis = []
    for r in range(8):
        for c in range(12):
            clis.append((r, c))
    return clis


def col_to_well_list(clis):
    """ Convert list of col lables to well; 'B4_1' >--> 'B4'
    """
    return list( set([c.split('_')[0] for c in clis]) )


def col_to_cell_list(clis):
    return well_to_cell_list(col_to_well_list(clis))


def col_to_well(col):
    return col.split('_')[0]


def col_to_cell(col):
    return well_to_cell(col_to_well(col))


def col_to_chan_index(col):
    return int(col.split('_')[1])


def cell_to_well_list(clis):
    """ Convert list of cell to well; (1,3) >--> 'B4'
    """
    return [C2WMAP[c] for c in clis]


def well_to_cell_list(wlis):
    """ Convert list of well to cell; 'B4' >--> (1,3)
    """
    return [W2CMAP[w] for w in wlis]


def cell_to_well(cell):
    return C2WMAP[cell]


def well_to_cell(well):
    return W2CMAP[well]

