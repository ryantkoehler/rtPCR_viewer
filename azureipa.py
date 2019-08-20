#!/usr/bin/env python
# 1/29/18 RTK
# 2/15/18 RTK update first minimally complete version; V0.12 2/16/18
# 3/2/18 RTK; V0.14, plate grid selection
# 3/31/18 RTK; V0.18
# 4/7/18 RTK; V0.19
# 4/10/18 RTK; V0.2; Fix threshold sliders
# 4/12/18 RTK; V0.21; Bug with threshold (non)display
# 8/17/19 RTK; V0.22; Clean up code some (pylint; DEBUG)
#
# Main module for Azure In-house PCR Analysis tool
#
DEBUG = False

PROG_NAME   = "AzureIPA"
PROG_TITLE  = "Azure In-house PCR Analysis Tool"
VERSION_S   = "AzureIPA Version 0.22; RTK 8/17/19"
COPYRIGHT_S = "(c) 2019 ryan@verdascend.com"


import sys
import os

# wxPython GUI dependency
try:
    import wx
except ImportError:
    print("Need the 'wxPython' library installed")
    print(" ... Sorry, can't run without it ...")
    sys.exit()

import azipa_gui as azgui
import azipa_df as azdf
import azipa_util as azu
import azipa_defs as azdef




class AzureIpaApp:
    """ Main top-level application class
    """
    def __init__(self):
        self.window = None
        self.dset = None
        self.initialize()
        self.init_settings()
        self.load_settings(popup=False)
        # Main wxpython window
        self.window = azgui.AzwinMain(self, None)
        self.set_status_text("Just started...")


    def initialize(self):
        """ Initialize run-time fields
        """
        self.fields = {}
        self.fields['PROG_TITLE'] = PROG_TITLE
        self.fields['PROG_NAME'] = PROG_NAME
        self.fields['VERSION_S'] = VERSION_S
        self.fields['COPYRIGHT_S'] = COPYRIGHT_S


    def init_settings(self):
        """ Initialize (ui) values / settings
        """
        # Settings are kept in dict, loaded from default
        self.def_settings = azdef.settings
        # Create copy of defs that can be modified; Only has strings and numbers
        self.settings = dict(self.def_settings)


    def load_settings(self, popup=False):
        """ Get settings from file
        """
        self.load_user_prefs(popup=popup)


    def close(self):
        """ Handle closing
        """
        self.save_settings()
        print("All done")
        sys.exit(0)


    # ------------------------------------------------
    # util GUI functions (for access by children)
    def set_status_text(self, story):
        message = self.get_field('PROG_NAME')
        if story:
            message = message + ": " + story
        self.window.statusbar.SetStatusText(message)


    def popup_message(self, message):
        azgui.popup_message(self.window, message)


    def apply_gui_settings(self, color=True, geom=False):
        self.window.apply_gui_settings(color=color, geom=geom)


    def report_text(self, text):
        self.window.report.report_text(text)


    def window_update(self):
        self.window.update_main()


    def window_init_dset(self, setdefs=True):
        self.window.reset_dset()
        if setdefs:
            # Set window default dataframes
            self.window.curves.set_dfkey('DF_BLCOR')
            self.window.plots.set_dfkey('DF_RAW')


    # ------------------------------------------------
    # Access to settings / working-data collection
    def have_dset(self):
        return bool(self.dset)


    def get_setting(self, key, default=None):
        return self.settings.get(key, default)


    def get_defsetting(self, key, default=None):
        return self.def_settings.get(key, default)


    def set_setting(self, key, value):
        self.settings[key] = value


    def get_field(self, key, default=None):
        return self.fields.get(key, default)


    def set_field(self, key, value):
        self.fields[key] = value


    def get_chan_1index_cols(self, chidx):
        # Convience access function to dset cols
        cols = []
        if self.dset is not None:
            cols = self.dset.get_chan_1index_cols(chidx)
        return cols


    def chan_1index_color(self, idx):
        # Color for channel index
        color = '#000099'
        if idx > 0:
            key = 'COLOR_CHANNEL_' + str(idx)
            color = self.get_setting(key, color)
        return color


    # ------------------------------------------------
    def load_user_prefs(self, fname=None, popup=True, guiup=True):
        """ Get and set user prefs from file
        If popup is true, feedback via GUI popup
        """
        if fname is None:
            fname = self.get_setting('FNAME_PREFS')
        usettings = azu.dict_from_json(fname, failok=True)
        if usettings is not None:
            self.settings.update(usettings)
            if guiup:
                self.window_update()
        if popup:
            if usettings is not None:
                message = "Loaded preferences from {}".format(fname)
            else:
                message = "Failed to get preferences from {}".format(fname)
            self.popup_message(message)


    def save_settings(self, popup=False):
        self.save_user_prefs(popup=popup)


    def save_user_prefs(self, fname=None, popup=True):
        """ Save user prefs to file
        If popup is true, feedback via GUI popup
        """
        if fname is None:
            fname = self.get_setting('PREFS_FNAME')
        # User-settable dic
        udic = self.usetting_dict()
        ok = azu.dict_to_json(udic, fname, failok=True)
        if popup:
            if ok:
                message = "Saved preferences to {}".format(fname)
            else:
                message = "Failed to save preferences to {}".format(fname)
            self.popup_message(message)


    def usetting_list(self):
        """List of user-settable things
        """
        nolis = azdef.uset_filtwords
        ulis = []
        for k in self.settings.keys():
            # If any bad-list-word is in key, it's out
            use = True
            for b in nolis:
                if b in k:
                    use = False
                    break
            if use:
                ulis.append(k)
        return sorted(ulis)


    def usetting_dict(self):
        ulis = self.usetting_list()
        udic = {k: v for k, v in self.settings.items() if k in ulis}
        return udic


    # ------------------------
    # High level processing functions
    def handle_load_data(self, fname):
        """ Handle loading data file
        """
        filename = os.path.basename(fname)
        filepath = os.path.dirname(fname)
        try:
            dset = azdf.platedataset_from_azcsv(fname)
            # Save dir
            self.set_setting('DEF_FILE_PATH', filepath)
            # Set things up
            self.set_dset(dset)
            # GUI updates
            self.window_init_dset()
            self.update_status()
            self.window_update()
        except:
            popmsg = "Failed to loaded data from {}".format(filename)
            self.popup_message(popmsg)


    def update_status(self):
        if self.dset is None:
            message = "Nothing loaded ..."
        else:
            ncol = len(self.dset.get_chan_1index_cols(0))
            nchan = self.dset.num_channels()
            fname = self.dset.fname
            message = "Have {0} data cols, {1} channels from: {2}".format(ncol, nchan, fname)
        self.set_status_text(message)


    def set_dset(self, dset):
        """ Update working vars for plate dataset
        """
        if DEBUG: print(">> set_dset", type(dset))
        self.dset = dset
        if dset is not None:
            # Save attributes into run-time fields
            self.set_field('DF_RAW', dset.df)
            if DEBUG: print("+ df", dset.df.shape)
            self.set_field('DSET_CHANNELS', dset.channel_list())
            self.set_field('DSET_NUM_CHAN', dset.num_channels())
            # First and second derivative dfs
            dfd1 = azdf.df_1st_deriv(dset.df)
            dfd2 = azdf.df_2nd_deriv(dset.df)
            self.set_field('DF_1ST_DERIV', dfd1)
            self.set_field('DF_2ND_DERIV', dfd2)
            # Init various dataset-based things...
            self.init_baselines()
            self.init_minmaxthresh()
            self.init_cq2nds()
            self.init_cqts()

        # Set up channel and cell working collections
        self.init_channel_sets()
        self.init_cell_sets()
        if DEBUG: print("<< set_dset")


    def init_channel_sets(self):
        """ Collect and save channel set and label list
        """
        clabs = []
        cset = set()
        if self.dset is not None:
            for c in range(self.dset.num_channels()):
                clabs.append(azu.channel_1index_label(c+1))
                cset.add(c)
        # Save channel list, set
        self.set_field('LIS_CHAN_LABELS', clabs)
        self.set_field('ACTIVE_CHANNEL_SET', cset)


    def init_cell_sets(self):
        """ Collect and save cell sets
        """
        cset = set()
        if self.dset is not None:
            # Index 0 yields all columns, then tranlate cols to cells, to set
            cset = set(azu.col_to_cell_list(self.get_chan_1index_cols(0)))
        self.set_field('ACTIVE_CELL_SET', cset)
        # Any data = copy of current set
        self.set_field('ANYDATA_CELL_SET', set(cset))
        # No data = all-96-cells minus any-data
        self.set_field('NODATA_CELL_SET', set(azu.plate96_cell_list()) - cset)


    def get_active_wells(self):
        """ List of active wells; A1, G4
        """
        return azu.cell_to_well_list(self.get_active_cells())


    def get_active_cells(self):
        """ List of active cells; (0,0), (5,3)
        """
        return list(self.get_field('ACTIVE_CELL_SET', []))


    def get_anydata_cells(self):
        """ List of no-data cells; (0,0), (5,3)
        """
        return list(self.get_field('ANYDATA_CELL_SET', []))


    def get_active_channels(self):
        """ List of active channel indexes
        """
        return list(self.get_field('ACTIVE_CHANNEL_SET', []))


    def get_active_cols(self):
        """ List of (dataframe) columns for active channels + cells; A1_1, G4_1, A1_3
        """
        cols = []
        if self.dset is not None:
            a_channels = self.get_field('ACTIVE_CHANNEL_SET')
            a_cells = self.get_field('ACTIVE_CELL_SET')
            # Get all columns with index 0
            allcols = self.dset.get_chan_1index_cols(0)
            #print("+ get_active_cols", allcols)
            for col in allcols:
                # Get channel index and cell from col
                cidx = azu.col_to_chan_index(col)
                cell = azu.col_to_cell(col)
                # Keep if index and cell in active sets
                if (cidx in a_channels) and (cell in a_cells):
                    cols.append(col)
        return cols


    def mod_active_cells(self, alis=None, dlis=None, guiup=False):
        """ Modify the active cell set
        Add cells in alis
        Delete cells in dlis

        return the number of changes made
        """
        nmod = 0
        # Local var pointing to set
        aset = self.get_field('ACTIVE_CELL_SET', [])
        # Adding anything?
        if alis is not None:
            for cell in alis:
                if cell not in aset:
                    aset.add(cell)
                    nmod += 1
        # Deleting?
        if dlis is not None:
            for cell in dlis:
                if cell in aset:
                    aset.remove(cell)
                    nmod += 1
        # If any mods and updating gui
        if (nmod > 0) and guiup:
            self.window_update()
        return nmod


    def init_baselines(self):
        if DEBUG: print(">> init_baselines")
        if self.dset is not None:
            #print("+ init_baselines not None")
            # TODO; Simple shift to first element
            df = self.dset.df
            bcdf = df - df.iloc[0].values.squeeze()
            self.set_field('DF_BLCOR', bcdf)
        if DEBUG: print("<< init_baselines")


    def init_minmaxthresh(self):
        """ Calculate and save default thresholds as fraction of max-min range
        Save min, max, thresh for channel
        """
        min_vals = []
        max_vals = []
        th_vals = []
        if self.dset is not None:
            # Baseline corrected df
            df = self.get_field('DF_BLCOR')
            # Fraction (of range) for default threholds
            frac = self.get_setting('DEF_THRESH_FRAC', 0.5)
            # Each channel
            for i in range(self.dset.num_channels()):
                cols = self.dset.get_chan_1index_cols(i+1)
                dfs = azdf.df_col_slice(df, cols)
                min_v = dfs.values.min()
                max_v = dfs.values.max()
                th_v = min_v + frac * (max_v - min_v)
                min_vals.append(min_v)
                max_vals.append(max_v)
                th_vals.append(th_v)
        # Keep lists in field collection
        self.set_field('LIS_CHAN_MINS', min_vals)
        self.set_field('LIS_CHAN_MAXS', max_vals)
        self.set_field('LIS_CHAN_THRESH', th_vals)


    def init_cq2nds(self):
        """ Get per-col (well+channel) dict of 2'nd derivative max Cq numbers
        Sets dict field
        """
        th_vals = {}
        if self.dset is not None:
            cqs = {}
            df = self.get_field('DF_2ND_DERIV')
            #print("+ init_cq2nd_sham", df.shape)
            for col in df.columns:
                v = df[col].idxmax()
                cqs[col] = v
        self.set_field('DIC_COL_CQ2ND', cqs)


    def init_cqts(self, default=100):
        """ Get per-col dict of Cq values, using per-channel thresholds
        Sets dict field
        """
        if DEBUG: print(">> init_cqts")
        cqs = {}
        if self.dset is not None:
            #print(">> init_cqts")
            thresh = self.get_field('LIS_CHAN_THRESH')
            #print(type(thresh))
            df = self.get_field('DF_BLCOR')
            #print("+ init_cqts", df.shape)
            for col in df.columns:
                chan = azu.col_to_chan_index(col)
                th = thresh[chan]
                # TODO; There's surely a pandas way to do this...
                v = get_thresh_cross_pos(df[col].values, th, default=default)
                #print("col, chan th v", col, chan, th, v)
                cqs[col] = v
                #print("col cq",col,v)
        self.set_field('DIC_COL_CQT', cqs)
        if DEBUG: print("<< init_cqts")


def get_thresh_cross_pos(dvals, th, default=None):
    """ Get (X) position where dvals "curve" crosses (Y) threshold
    Returns X, interpolated via bracketing values, or default if no cross
    """
    val = default
    for i, _ in enumerate(dvals):
        if dvals[i] > th:
            if i > 0:
                v1 = dvals[i-1]
                v2 = dvals[i]
                val = i + (th - v1) / (v2 - v1)
            break
    return val


# Main loop = cook up GUI window, init then start loop
if __name__ == "__main__":
    win_root = wx.App()
    app = AzureIpaApp()
    app.window.Show()
    win_root.MainLoop()

