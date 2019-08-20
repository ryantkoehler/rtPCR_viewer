#!/usr/bin/env python
# 2/12/18 RTK;
# 2/28/18 RTK; Updates (CFX data ETL shams)
# 3/4/18 RTK; Simplify into one class, multi-channel DataFrame
# 3/24/18 RTK; Clean up, simple non-df things to util
# 8/17/19 RTK; V0.22; Clean up code some (pylint; DEBUG)
#
# Dataframes for 96-well plate stuff for Azure In-house PCR Analysis tool
#   Classes and util functions
#
# Conventions
#   (plate)     Well = position like 'A3' 'G4'
#   (grid)      Cell = coords like (0,2) (5,4)
#   (dataframe) Cols = columns in (multi-channel) dataset like 'A3_1' 'G4_1'
#   (dataset)   Channel = channel label string like 'Channel_1'
#   (dataset)   Chidx = channel 1-based int index
#

# Input may have non-ascii chars; need this for parsing
import codecs
import string
import getpass

import os
import time

import numpy as np
import pandas as pd


import azipa_util as azu


# ----------------------
# Main data colleciton class
class PlateDataSet:
    """ Collection (96-well) plate data...
    """
    def __init__(self, fname=''):
        self.fname = fname
        self.channels = []
        self.ch_names = []
        self.df = None


    def add_df_chan(self, df, chan, name=''):
        """ Add channel dataframe to collection

        chan is the channel name (e.g. filekey 'Step1Channel2')
        df is dataframe; If already have one, new number of rows must be same
        """
        if chan in self.channels:
            raise ValueError('Add channel df name', chan, 'already in collection')
        # Suffix (channel index number) for columns
        #   e.g. First channel cols end with 0, second with 1, etc
        suf = azu.chan_index_col_suf(len(self.channels))
        # Add channel and name to collection
        self.channels.append(chan)
        self.ch_names.append(name)
        # Update column labels to include channel number
        df.columns = [str(col) + suf for col in df.columns]
        # If none already, just keep this one
        if self.df is None:
            self.df = df
        else:
            # Check number of rows matches
            row, _ = self.df.shape
            nrow, _ = df.shape
            if row != nrow:
                raise ValueError('Add channel df nrow missmatch', nrow, row)
            if self.df.index.name != df.index.name:
                raise ValueError('Add channel df nrow missmatch', self.df.index.name, df.index.name)
            # Append column-wise
            self.df = pd.concat([self.df, df], axis=1)


    def num_channels(self):
        return len(self.channels)


    def channel_list(self):
        return self.channels


    def ch_name_list(self):
        return self.ch_names


    def get_chan_1index_cols(self, idx):
        """ Get list of (dataframe) columns for (channel) index
        1-based index; zero = all
        """
        cols = []
        if (self.df is not None) and (idx >= 0):
            if idx == 0:
                cols = list(self.df.columns)
            else:
                suf = azu.chan_1index_col_suf(idx)
                cols = [c for c in self.df.columns if c.endswith(suf)]
        return cols


# ----------------------
def platedataset_from_azcsv(fname, sep=',', com='#'):
    """ Parse Azure multi-channel multi-well csv file

    Return PlateDataSet
    """
    # Check if file exists up front
    if not os.path.isfile(fname):
        print("File does not exist: {0}".format(fname))
        return None
    # Collection for dataframes for each channel
    dset = PlateDataSet(fname=fname)
    tab = None
    # Open for unicode in case non-ascii chars...
    with codecs.open(fname, 'r', encoding='utf-8') as infile:
        for line in infile:
            # Strip out any non-print chars from line
            cline = ''.join(filter(lambda x: x in string.printable, line)).strip()
            # Ignore if comment line
            if com and cline.startswith(com):
                continue
            # Split line into tokens; If nothing, ignore
            parts = cline.split(sep)
            if not parts:
                continue
            # Data series rows start like: 'Step1Channel1'
            if parts[0].startswith('Step'):
                if tab:
                    df = dataframe_from_tab(tab, chan)
                    dset.add_df_chan(df, chan, name=tabname)
                # Init new table and name
                tab = []
                # In case start-line has multiple (space-delim) parts, key = first, name = last
                parts = parts[0].split()
                chan = parts[0]
                tabname = parts[-1]
            else:
                if tab is not None:
                    tab.append(parts)
    # Last one
    if tab:
        df = dataframe_from_tab(tab)
        dset.add_df_chan(df, chan, name=tabname)
    return dset


def dataframe_from_tab(tab, dropna=True):
    # Assume first row = column labels
    # Assume first row, first col = index column name
    indexcol = tab[0][0]
    df = pd.DataFrame(tab[1:], columns=tab[0])
    # Make sure all values are numbers or np.NaN (the coerce part)
    df = df.apply(pd.to_numeric, errors='coerce')
    # Removing columns with missing values?
    if dropna:
        df.dropna(axis=1, how='any', inplace=True)
    # Set index
    df.set_index(indexcol, inplace=True)
    return df


def platedataset_to_azcsv(dset, fname, com=True, dropna=True):
    """ Write Azure multi-channel 96-well csv file

    Write to fname
    If com is True, write comment lines
    If dropna is True, drop (skip) cols with missing values (NA)

    Returns number of dataframes written
    """
    n = 0
    print("trying to open", fname)
    with open(fname, 'w') as ofile:
        print("opened", fname)
        if com:
            bname = os.path.basename(fname)
            print("# File:", bname, file=ofile)
            print("# 96-well plate, {} channel dataset".format(dset.num_channels()), file=ofile)
            print("# Source: {}".format(dset.fname), file=ofile)
            print("# Date: {}".format(time.strftime("%B %d, %Y")), file=ofile)
            print("# User:", getpass.getuser(), file=ofile)
        for i, _ in enumerate(dset.channel_list()):
            name = dset.ch_name_list()[i]
            df = dset.get_index_df(i)
            if com:
                print("# Dataset {} {}".format(name, df.shape), file=ofile)
            # 1 based output
            startkey = "Step1Channel" + str(i+1)
            print(startkey, name, file=ofile)
            # Clean up column labels in case they have channel-number suffixes...
            # Strip whatever's after underscore e.g. 'B6_2' >--> 'B6'
            df.columns = [p.split('_')[0] for p in df.columns]
            # Write as csv with column lable header
            df.to_csv(ofile, sep=',', header=True, na_rep='NaN')
    return n


def platedataset_details(dset, sindex=True, rowrange=True, colrange=True):
    """ Return list of strings detailing data contents

    If sindex, report index stuff;
        If also rowrange, report row details too
    If colrange, report column stuff
    """
    slis = []
    for chan in dset.pdf_chan_list():
        pdf = dset.get_chan_pdf(chan)
        story = "{} ({})".format(chan, pdf.name)
        if sindex:
            idx = pdf.df.index
            part = "\t{}: {} rows".format(idx.name, len(idx))
            story += part
            if rowrange:
                part = " ({} to {})".format(idx[0], idx[-1])
                story += part
        if colrange:
            part = "\t{} cols".format(len(pdf.df.columns))
            story += part
        slis.append(story)
    return slis


# ---------------------------------------------------------------------------
# DataFrame functions

def df_col_slice(df, cols, copy=False):
    if copy:
        return df_col_slice_df(df, cols)
    return df_col_slice_view(df, cols)


def df_col_slice_view(df, cols):
    """ Get dataframe slice with subset of columns given in list (or pdIndex)

    Returns a view of original DataFrame
    """
    assert (type(df) == pd.DataFrame)
    # All rows, but only subset of cols in list
    #   Subset of passed cols that are actually in df
    kcols = [k for k in cols if k in df.columns]
    return df.loc[:, kcols]


def df_col_slice_df(df, cols):
    """ Get dataframe slice with subset of columns given in list (or pdIndex)

    Returns a copy of original DataFrame
    """
    assert (type(df) == pd.DataFrame)
    # Filter columns in list; Returns copy (not just view)
    #   Subset of passed cols that are actually in df
    kcols = [k for k in cols if k in df.columns]
    return df[[kcols]]


def df_1st_deriv(df):
    """ Get first derivative of columns in dataframe
    Returns (copy of) DataFrame
    """
    assert (type(df) == pd.DataFrame)
    ddf = df.copy(deep=True)
    ddf = ddf.shift(-1) - ddf
    # N-1 row diffs in N-row dataframe; Drop last row which has NaN
    ddf.dropna(inplace=True)
    return ddf


def df_2nd_deriv(df):
    """ Get second derivative of columns in dataframe
    Returns (copy of) DataFrame
    """
    assert (type(df) == pd.DataFrame)
    df1 = df_1st_deriv(df)
    df2 = df_1st_deriv(df1)
    return df2


def df_get_minmax(df, mindif=None):
    """ Get min and max for dataframe
    Returns (min, max)
    """
    assert (type(df) == pd.DataFrame)
    minval = df.values.min()
    maxval = df.values.max()
    if mindif is not None:
        if (maxval - minval) < mindif:
            maxval = minval + mindif
    return(minval, maxval)


def df_get_rowminmax(df, mindif=None):
    """ Get row min max for dataframe; Basically use index
    Returns (min, max)
    """
    assert (type(df) == pd.DataFrame)
    minval = float(df.index[0])
    maxval = float(df.index[-1])
    if mindif is not None:
        if (maxval - minval) < mindif:
            maxval = minval + mindif
    return(minval, maxval)



# ---------------------------------------------------------------------------
if __name__ == "__main__":

    pdset = PlateDataSet("data test")
    print(pdset)
