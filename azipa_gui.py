#!/usr/bin/env python
# 1/29/18 RTK
# 2/16/18 RTK; 
# 3/2/18 RTK; Plate grid selection shams
# 3/31/18 RTK; Popup channel, thresh select; Panel for matplotlib, thresh, Y range
# 4/7/18 RTK; Clean up Y min/max sliders, add X for plots
# 8/17/19 RTK; V0.22; Clean up code some (pylint; DEBUG)
#
# GUI stuff for Azure In-house PCR Analysis tool
#
DEBUG = False

# numbers / DataFrames
import numpy as np
import pandas as pd

# Plotting stuff
import matplotlib 
matplotlib.use('TkAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx, wxc
from matplotlib.figure import Figure

# GUI stuff
import wx
import wx.adv
import wx.grid as gridlib

import azipa_defs as azdef
import azipa_df as azdf
import azipa_util as azu


class AzwinMain(wx.Frame):
    """ Top level window
    """
    def __init__(self, app, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        # Main parent object
        self.app = app
        self.create_panels()
        self.create_menu_status()
        self.config_layout()
        self.apply_gui_settings(color=True, geom=True)
        self.init_dset()
        self.update_main()


    def create_panels(self):
        """ Create window sub-panels and containers for these
        Layout = two nested split windows in main panel
        --------------
        | C     | G  |
        |       |----|
        |-------| R  |
        | P     |    |
        |       |    |
        --------------

        Curves (raw-ish) plots of data
        Plots (e.g. derived model, histogram, etc)
        Grid for plate layout
        Report area ... numbers, stats, etc
        """
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        # Vertical split window horizontal into Left Right
        self.splitterLR = new_splitter(self)
        self.panelL = new_panel(self.splitterLR)
        self.sizerL = wx.BoxSizer(wx.VERTICAL)
        self.panelR = new_panel(self.splitterLR)
        self.sizerR = wx.BoxSizer(wx.VERTICAL)
        # Left side split window and plot panels
        self.splitterLTB = new_splitter(self.panelL)
        self.curves = AzwinPlotPanel(self.splitterLTB, self.app, "Curves")
        self.plots = AzwinPlotPanel(self.splitterLTB, self.app, "Plots")
        # Right side split window for plate and report
        self.splitterRTB = new_splitter(self.panelR)
        self.plate = AzwinPlatePanel(self.splitterRTB, self.app)
        self.report = AzwinReportPanel(self.splitterRTB, self.app)


    def create_menu_status(self):
        """ Create menus and status bar
        """
        self.menu = AzwinMenu(self, self.app)
        self.SetMenuBar(self.menu)
        # A Statusbar at the bottom of the window
        self.statusbar = self.CreateStatusBar() 
        # Preferences dialog
        self.prefs_dialog = AzwinPrefs(self, self.app)


    def config_layout(self):
        # Left, top / bottom curves and plots 
        self.splitterLTB.SplitHorizontally(self.curves, self.plots)
        self.sizerL.Add(self.splitterLTB, 1, wx.EXPAND, azdef.SIZER_BORDER)
        wrap_up_sizing(self.panelL, self.sizerL)
        # Right, top / bottom plate and report
        self.splitterRTB.SplitHorizontally(self.plate, self.report)
        self.sizerR.Add(self.splitterRTB, 1, wx.EXPAND, azdef.SIZER_BORDER)
        wrap_up_sizing(self.panelR, self.sizerR)
        # Main top left and right
        self.splitterLR.SplitVertically(self.panelL, self.panelR)
        self.sizer_main.Add(self.splitterLR, 1, wx.EXPAND, azdef.SIZER_BORDER)
        self.SetSizer(self.sizer_main)
        self.Layout()


    def apply_gui_settings(self, color=True, geom=True):
        """ Set GUI configuration things from settings 
        """
        if geom:
            self.apply_win_geometry()
        if color:
            self.apply_win_colors()

    
    def apply_win_geometry(self):
        """ Set window geometry stuff
        Some of these (e.g. splitter sash) only work after layout is setup
        """
        # Main window 
        winsize = self.app.get_setting('MAIN_WIN_SIZE')
        self.SetSize(winsize)
        winpos = self.app.get_setting('MAIN_WIN_POS')
        self.SetPosition(winpos)
        title = self.app.get_field('PROG_TITLE')
        self.SetTitle(title)
        # Window split fractions
        spos = self.app.get_setting('MAIN_SPLIT_LR_POS')
        config_splitter(self.splitterLR, sashpos=spos)
        spos = self.app.get_setting('MAIN_SPLIT_LTB_POS')
        config_splitter(self.splitterLTB, sashpos=spos)
        spos = self.app.get_setting('MAIN_SPLIT_RTB_POS')
        config_splitter(self.splitterRTB, sashpos=spos)
        # Plate grid
        csize = self.app.get_setting('PGRID_COL_SIZE')
        self.plate.grid.SetDefaultColSize(csize, True)
        rsize = self.app.get_setting('PGRID_ROW_SIZE')
        self.plate.grid.SetDefaultRowSize(rsize, True)


    def apply_win_colors(self):
        # Main panel background colors
        color = self.app.get_setting('COLOR_WIN_PLOT')
        config_panel(self.plots, color=color)
        config_panel(self.plots.panel_mp, color=color)
        color = self.app.get_setting('COLOR_WIN_CURVE')
        config_panel(self.curves, color=color)
        config_panel(self.curves.panel_mp, color=color)
        color = self.app.get_setting('COLOR_WIN_PLATE')
        config_panel(self.plate, color=color)
        color = self.app.get_setting('COLOR_WIN_REPORT')
        config_panel(self.report, color=color)
        self.report.tex.SetBackgroundColour(color)


    def init_dset(self):
        # Set data-set dependent dialogs to None
        self.chan_dialog = None
        self.thresh_dialog = None


    def reset_dset(self):
        """ Reset dataset-specific things (e.g. on new load)
        """
        # Get new channel dialog; If exists, destroy first
        if self.chan_dialog is not None:
            self.chan_dialog.Destroy()
        self.chan_dialog = AzwinChannels(self, self.app)
        # Threshold dialog; If exists, destroy first
        if self.thresh_dialog is not None:
            self.thresh_dialog.Destroy()
        self.thresh_dialog = AzwinThresholds(self, self.app)


    def popup_preferences(self):
        self.prefs_dialog.Show()


    def popup_channels(self):
        if self.chan_dialog is None:
            self.chan_dialog = AzwinChannels(self, self.app)
        self.chan_dialog.Show()
        

    def popup_thresh(self):
        if self.thresh_dialog is None:
            self.thresh_dialog = AzwinThresholds(self, self.app)
        self.thresh_dialog.Show()
        

    def update_main(self, reset=True, plate=True, plots=True, report=True):
        if DEBUG: print(">> update_main")
        if plate:
            self.plate.update_grid_cells(reset=reset)

        if plots:
            self.curves.draw_plot()
            self.plots.draw_plot()

        if report:
            self.report.report()
        if DEBUG: print("<< update_main")


# ---------------------------------------------------------------------------
# Plotting window
class AzwinPlotPanel(wx.Panel):
    """ Panel with plot and control subpanels
    """
    def __init__(self, parent, app, name, color=None):
        #super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        wxid = wx.NewId()
        super().__init__(parent, wxid)
        self.parent = parent 
        self.app = app
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.setup_button_panel(name)
        self.setup_plot()
        wrap_up_sizing(self, self.sizer)
        # Init default settings
        self.set_dfkey('DF_RAW')


    def setup_button_panel(self, name):
        """ Set up button panel and install buttons, etc
        """
        self.panel_but = new_panel(self)
        self.sizer_but = wx.BoxSizer(wx.HORIZONTAL)
        self.win_label = new_statext(self.panel_but, name + " window", self.sizer_but)
        # Plot data source pulldown
        self.cbox_plotdata = new_choice(self.panel_but, self.cb_plotdata, 
             chlis=azdef.CM_PLOT_DATA, sizer=self.sizer_but, sizerprop=0)
        # Add spacing to push choice box to left size
        self.panel_padding = new_panel(self.panel_but, sizer=self.sizer_but, sizerprop=1)
        # Finish button panel, add to main sizer. Proportion = 0 = don't stretch
        wrap_up_sizing(self.panel_but, self.sizer_but)
        self.sizer.Add(self.panel_but, 0, wx.EXPAND|wx.ALL, azdef.SIZER_BORDER)


    def setup_plot(self):
        self.panel_mp = AzwinMatplotlibPanel(self, self.app)
        # Proportion = 1 = full size
        self.sizer.Add(self.panel_mp, 1, wx.EXPAND|azdef.SIZER_FLAG_NTOP, azdef.SIZER_BORDER)


    def set_dfkey(self, dfkey):
        """ Set dfkey (specifying dataset for current plot). Also updates menu choice 
        """
        self.dfkey = dfkey
        self.plotdata_set_choice()
        self.panel_mp.set_dfkey(dfkey)


    def get_dfkey(self):
        return self.dfkey


    def will_draw_thresh(self):
        return self.panel_mp.will_draw_thresh()


    def cb_plotdata(self, event):
        # Handle plot data options:
        dfkey = None
        if event.GetString().upper().startswith('BASE'):
            dfkey = 'DF_BLCOR'     #   Baseline corrected
        elif event.GetString().upper().startswith('RAW'):
            dfkey = 'DF_RAW'        #   Raw
        elif event.GetString().upper().startswith('1ST'):
            dfkey = 'DF_1ST_DERIV'  #   1st derivative
        elif event.GetString().upper().startswith('2ND'):
            dfkey = 'DF_2ND_DERIV'  #   2st derivative
        else:
            raise ValueError('Event', event.GetString(), 'unknown')
        # Set and draw
        self.set_dfkey(dfkey)
        self.draw_plot(dfkey)


    def plotdata_set_choice(self):
        choice = None
        dfkey = self.get_dfkey()
        if dfkey == 'DF_BLCOR':
            choice = 'BASE'
        elif dfkey == 'DF_RAW':
            choice = 'RAW'
        elif dfkey == 'DF_1ST_DERIV':
            choice = '1ST'
        elif dfkey == 'DF_2ND_DERIV':
            choice = '2ND'
        if choice is None:
            raise ValueError('dfkey', dfkey, 'unknown')
        set_choice_label(self.cbox_plotdata, choice)


    def draw_plot(self, dfkey=None, clear=True):
        """ Handle plotting for given dataframe
        """
        if DEBUG: print("\n>> draw_plot")
        if clear:
            self.panel_mp.clear_plot()

        #print("+ draw_plot dfkey", dfkey)
        # Dataframe key; Recover or save
        if dfkey is None:
            dfkey = self.get_dfkey()
        else:
            self.set_dfkey(dfkey)
        assert(dfkey is not None)
        #print("+ draw_plot dfkey", dfkey)

        # Get source dataframe
        st_df = self.app.get_field(dfkey, None)
        if st_df is None:
            return
        #print("+ draw_plot st_df", st_df.shape)

        # Get active-col slice from source dataframe
        cols = self.app.get_active_cols()
        if len(cols) < 1:
            return
        ac_df = azdf.df_col_slice(st_df, cols)
        #print("===============================")
        #print("ccc0", st_df.columns)
        #print("ccc0", cols)
        #print("ccc0", ac_df.columns)
        #print("+ draw_plot ac_df", ac_df.shape)

        # Thresholds
        if self.will_draw_thresh():
            thvals = self.app.get_field('LIS_CHAN_THRESH')
        else:
            thvals = None
        #print("+ draw_plot thvals", thvals)

        # Each active channel
        for idx in self.app.get_active_channels():
            cols = self.app.get_chan_1index_cols(idx+1) 
            if len(cols) < 1:
                continue

            df = azdf.df_col_slice(ac_df, cols)
            color = self.app.chan_1index_color(idx+1)
            if thvals is None:
                th = None
            else:
                th = thvals[idx]
            self.panel_mp.df_plot(df, color, thresh=th)

        self.panel_mp.refresh_plot()
        if DEBUG: print("<< draw_plot")


# ---------------------------------------------------------------------------
# Matplotlib plotting window 
class AzwinMatplotlibPanel(wx.Panel):
    """ Panel with matplotlib plot and controls

    Plots 'current dataframe' specified by dfkey 

    Plot range real limits and values held as y_min, y_minval etc..
    Range slider values held in sliders
    """
    def __init__(self, parent, app):
        wxid = wx.NewId()
        super().__init__(parent, wxid)
        self.parent = parent 
        self.app = app
        # Init default settings
        self.init_dset()
        self.set_logy(False, guiup=False)
        self.set_thresh(guiup=False)
        self.set_yauto(True, guiup=False)
        # gui parts
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.setup_plot()
        self.setup_button_panel()
        wrap_up_sizing(self, self.sizer)


    def init_dset(self):
        # Initialize things that should be reset with new datasets
        self.set_dfkey(None)
        self.set_yminmax()
        self.set_yrange(guiup=False)


    def setup_plot(self):
        # MMM matplotlib stuff 
        self.mpl_figure = Figure()
        self.mpl_axes = self.mpl_figure.add_subplot(111)
        self.mpl_figurecanvas = FigureCanvas(self, -1, self.mpl_figure)
        self.sizer.Add(self.mpl_figurecanvas, 1, wx.GROW, azdef.SIZER_BORDER)
        # MMM feedback shams???
        #self.mpl_figurecanvas.mpl_connect('motion_notify_event', self.cb_grid_statusbar)
        #self.mpl_figurecanvas.Bind(wx.EVT_ENTER_WINDOW, self.cb_grid_changecursor)


    def setup_button_panel(self):
        """ Set up button panel stuff
        """
        self.panel_but = new_panel(self)
        self.sizer_but = wx.BoxSizer(wx.VERTICAL)
        self.cbx_logscale = new_checkbox(self.panel_but, "Log", self.cb_logscale, sizer=self.sizer_but, sizerprop=0) 
        self.cbx_thresh = new_checkbox(self.panel_but, "Thresh", self.cb_thresh, sizer=self.sizer_but, sizerprop=0)
        self.cbx_yauto = new_checkbox(self.panel_but, "Auto Y", self.cb_yauto, sizer=self.sizer_but, sizerprop=0)
        # Max X scale adjustment; Text, then sliders in subpanel
        self.btn_xfrange = new_button(self.panel_but, "X full", self.cb_xfrange, sizer=self.sizer_but)
        self.panel_slX2 = new_panel(self.panel_but, sizer=self.sizer_but, sizerprop=1)
        self.sizer_slX2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sld_xmax = new_slider(self.panel_slX2, "X-max", self.cb_xsmax, horiz=False, sizer=self.sizer_slX2)
        self.sld_xmin = new_slider(self.panel_slX2, "X-min", self.cb_xsmin, horiz=False, sizer=self.sizer_slX2)
        wrap_up_sizing(self.panel_slX2, self.sizer_slX2)
        # Max Y scale adjustment; Text, then sliders in subpanel
        self.btn_yfrange = new_button(self.panel_but, "Y full", self.cb_yfrange, sizer=self.sizer_but)
        self.panel_slY2 = new_panel(self.panel_but, sizer=self.sizer_but, sizerprop=1)
        self.sizer_slY2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sld_ymax = new_slider(self.panel_slY2, "Y-max", self.cb_ysmax, horiz=False, sizer=self.sizer_slY2)
        self.sld_ymin = new_slider(self.panel_slY2, "Y-min", self.cb_ysmin, horiz=False, sizer=self.sizer_slY2)
        wrap_up_sizing(self.panel_slY2, self.sizer_slY2)
        # Finish button panel, add to main sizer; Proportion = 0 = don't stretch
        wrap_up_sizing(self.panel_but, self.sizer_but)
        flag = wx.LEFT | wx.GROW | wx.EXPAND
        self.sizer.Add(self.panel_but, 0, flag, azdef.SIZER_BORDER)
        # Set status for checkboxes
        self.init_checkbox_vals()
        self.init_slider_vals()


    def set_dfkey(self, dfkey=None):
        # If legit dataframe, set min, max values with it
        self.dfkey = dfkey
        if dfkey is not None:
            df = self.get_df()
            if df is not None:
                # X min/max values, current range 
                minval, maxval = azdf.df_get_rowminmax(df, mindif=1.0)
                self.set_xminmax(minval=minval, maxval=maxval)
                self.set_xrange(minval=minval, maxval=maxval, guiup=True)
                # Y min/max values, current range 
                minval, maxval = azdf.df_get_minmax(df, mindif=1.0)
                self.set_yminmax(minval=minval, maxval=maxval)
                self.set_yrange(minval=minval, maxval=maxval, guiup=True)


    def get_dfkey(self):
        # Current dfkey
        return self.dfkey


    def get_df(self):
        # Dataframe for current dfkey
        return self.app.get_field(self.get_dfkey(), None)


    def set_xminmax(self, minval=0.0, maxval=1.0):
        # Set (real-value) data X min / max; Absolute and display limits
        self.x_min = minval
        self.x_max = maxval
        self.x_minval = minval
        self.x_maxval = maxval


    def set_yminmax(self, minval=0.0, maxval=1.0):
        # Set (real-value) data Y min / max; Absolute and display limits
        self.y_min = minval
        self.y_max = maxval
        self.y_minval = minval
        self.y_maxval = maxval
        self.y_delta = (maxval - minval) * azdef.PLOT_YDELTA_MIN


    def init_checkbox_vals(self):
        # Set checkbox values based on settings
        self.cbx_logscale.SetValue(self.use_logy())
        self.cbx_thresh.SetValue(self.show_thresh())
        self.cbx_yauto.SetValue(self.use_yauto())


    def init_slider_vals(self):
        # Init scale slider values to full range
        # Since slider display is inverted, max gets min and vice versa
        self.sld_ymax.SetValue(self.sld_ymax.GetMin())
        self.sld_xmax.SetValue(self.sld_xmax.GetMin())
        self.sld_ymin.SetValue(self.sld_ymin.GetMax())
        self.sld_xmin.SetValue(self.sld_xmin.GetMax())


    def set_yauto(self, yauto=False, guiup=True):
        self.do_yauto = yauto
        if guiup:
            # Set dfkey (to current) forces Y limits
            self.set_dfkey(self.get_dfkey())
            self.parent.draw_plot()


    def use_yauto(self):
        return self.do_yauto


    def set_logy(self, logy=False, guiup=True):
        self.do_logy = logy
        if guiup:
            self.parent.draw_plot()


    def use_logy(self):
        return self.do_logy


    def set_thresh(self, thresh=False, guiup=True):
        self.do_thresh = thresh
        # If GUI update; Need thresh==False to because we've just set flag
        if guiup and (self.will_draw_thresh() or (thresh==False)):
            self.parent.draw_plot()


    def show_thresh(self):
        return self.do_thresh


    def will_draw_thresh(self):
        return self.show_thresh() and (self.get_dfkey() == 'DF_BLCOR')


    def cb_logscale(self, event):
        val = event.GetEventObject().GetValue()
        self.set_logy(val, guiup=True)


    def cb_thresh(self, event):
        val = event.GetEventObject().GetValue()
        self.set_thresh(event.GetEventObject().GetValue(), guiup=True)


    def cb_yauto(self, event):
        val = event.GetEventObject().GetValue()
        self.set_yauto(event.GetEventObject().GetValue(), guiup=True)


    def cb_yfrange(self, event):
        self.set_yrange(minval=self.y_min, maxval=self.y_max, guiup=True)


    def cb_xfrange(self, event):
        self.set_xrange(minval=self.x_min, maxval=self.x_max, guiup=True)


    # ---- X scale sliders
    def set_xrange(self, minval=None, maxval=None, guiup=True):
        # Set X values for range display; If guiup, also set sliders, draw
        #print(">> set_xrange", minval, maxval, guiup)
        if minval is not None:
            self.x_minval = minval
        if maxval is not None:
            self.x_maxval = maxval
        #print("+ set_xrange vals", self.x_minval, self.x_maxval)
        # Only draw if guiup flag 
        if guiup:
            val_to_slider(self.sld_xmin, minval, self.x_min, self.x_max, setpos=True)
            val_to_slider(self.sld_xmax, maxval, self.x_min, self.x_max, setpos=True)
            self.parent.draw_plot()
        #print("<< set_xrange")


    def get_xrange(self):
        # Settings-based x value min max range
        return (self.x_minval, self.x_maxval)


    def get_sld_xrange(self):
        # Slider-based x value min max range
        # Upsidedown slider; Have to invert things
        xmin = slider_to_val(self.sld_xmin, self.x_min, self.x_max, invert=True)
        xmax = slider_to_val(self.sld_xmax, self.x_min, self.x_max, invert=True)
        return xmin, xmax


    def cb_xsmax(self, event):
        if not self.app.have_dset():
            return
        xmin,xmax = self.get_sld_xrange()
        # If min beyond max, move min
        if xmin > (xmax - azdef.PLOT_XDELTA_MIN):
            xmin = xmax - azdef.PLOT_XDELTA_MIN
        self.set_xrange(minval=xmin, maxval=xmax, guiup=True)


    def cb_xsmin(self, event):
        if not self.app.have_dset():
            return
        xmin,xmax = self.get_sld_xrange()
        # If min beyond max, move max
        if xmax < (xmin + azdef.PLOT_XDELTA_MIN):
            xmax = xmin + azdef.PLOT_XDELTA_MIN
        self.set_xrange(minval=xmin, maxval=xmax, guiup=True)


    # ---- Y scale sliders
    def set_yrange(self, minval=None, maxval=None, guiup=True):
        # Set Y values for range display; If guiup, also set sliders, draw
        #print(">> set_yrange", minval, maxval, guiup)
        if minval is not None:
            self.y_minval = minval
        if maxval is not None:
            self.y_maxval = maxval
        #print("+ set_yrange vals", self.y_minval, self.y_maxval)
        # Only draw if guiup flag and if not Y autoscale
        if guiup and not self.use_yauto():
            val_to_slider(self.sld_ymin, minval, self.y_min, self.y_max, setpos=True)
            val_to_slider(self.sld_ymax, maxval, self.y_min, self.y_max, setpos=True)
            self.parent.draw_plot()
        #print("<< set_yrange")


    def get_yrange(self):
        # Settings-based y value min max range
        return (self.y_minval, self.y_maxval)


    def get_sld_yrange(self):
        # Slider-based y value min max range
        # Upsidedown slider; Have to invert things
        ymin = slider_to_val(self.sld_ymin, self.y_min, self.y_max, invert=True)
        ymax = slider_to_val(self.sld_ymax, self.y_min, self.y_max, invert=True)
        return ymin, ymax


    def cb_ysmax(self, event):
        if not self.app.have_dset():
            return
        ymin,ymax = self.get_sld_yrange()
        # If min beyond max, move min
        if ymin > (ymax - self.y_delta):
            ymin = ymax - self.y_delta
        self.set_yrange(minval=ymin, maxval=ymax, guiup=True)


    def cb_ysmin(self, event):
        if not self.app.have_dset():
            return
        ymin,ymax = self.get_sld_yrange()
        # If min beyond max, move max
        if ymax < (ymin + self.y_delta):
            ymax = ymin + self.y_delta
        self.set_yrange(minval=ymin, maxval=ymax, guiup=True)


    def clear_plot(self):
        self.mpl_axes.cla()
        self.refresh_plot()


    def refresh_plot(self):
        self.mpl_figurecanvas.draw()
        self.Refresh()


    def df_plot(self, df, color, clear=False, thresh=None):
        """ Plot dataframe with given color 

        DataFrame plot output set to axis:
        https://stackoverflow.com/questions/45620789/pandas-dataframe-plot-resets-pyplot-current-figure
        """
        assert(type(df) == pd.DataFrame)
        if DEBUG: print(">> df_plot", df.shape, thresh)
        if clear:
            self.clear_plot()
        logy = self.use_logy()

        # Only plot curves if df has any data; Could be empty if all -NA-
        if not df.empty:
            # Auto Y scale or explicit?
            if self.use_yauto():
                df.plot(ax=self.mpl_axes, logy=logy, legend=False, color=color, 
                        xlim=self.get_xrange())
            else:
                df.plot(ax=self.mpl_axes, logy=logy, legend=False, color=color, 
                        xlim=self.get_xrange(), ylim=self.get_yrange())

        # Threshold?
        if self.show_thresh() and (thresh is not None):
            # As dotted horizontal line
            self.mpl_axes.axhline(y=thresh, color=color, linestyle=':')
        if DEBUG: print("<< df_plot")


    # NOT USED
    def cb_grid_statusbar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            text = "x= " + str(x) + "  y=" + str(y)
            self.app.set_status_text(text)


    # NOT USED
    def cb_grid_changecursor(self, event):
        self.mpl_figurecanvas.SetCursor(wxc.StockCursor(wx.CURSOR_BULLSEYE))


# ---------------------------------------------------------------------------
# Plate grid window 
class AzwinPlatePanel(wx.Panel):
    """ Panel with 96 well plate grid
    """
    def __init__(self, parent, app):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.parent = parent 
        self.app = app
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.setup_button_panel()
        self.setup_grid()
        wrap_up_sizing(self, self.sizer)

        # default settings
        self.do_select = False


    def set_select(self, what):
        self.do_select = what
        

    def get_select(self):
        return self.do_select


    def setup_button_panel(self):
        """ Set up button panel stuff
        """
        self.panel_but = new_panel(self)
        self.sizer_but = wx.BoxSizer(wx.HORIZONTAL)
        self.win_label = new_statext(self.panel_but, "Plate window", self.sizer_but)
        self.btn_channel = new_button(self.panel_but, "Channels", self.cb_channel, sizer=self.sizer_but)
        self.btn_thresh = new_button(self.panel_but, "Thresholds", self.cb_thresh, sizer=self.sizer_but)
        # Select grid mode
        self.cbox_select = new_choice(self.panel_but, self.cb_selectmode, 
                                            chlis=azdef.CM_PLATE_SELECT, sizer=self.sizer_but)
        # Colorby
        self.cbox_colorby = new_choice(self.panel_but, self.cb_colorby, 
                                            chlis=azdef.CM_PLATE_COLORBY, sizer=self.sizer_but)
        # Add button panel to main sizer; Proportion = 0 = don't stretch
        wrap_up_sizing(self.panel_but, self.sizer_but)
        self.sizer.Add(self.panel_but, 0, wx.EXPAND|wx.ALL, azdef.SIZER_BORDER)

    
    def cb_channel(self, event):
        # Handle channel selection
        if not self.app.have_dset():
            self.app.popup_message("No data loaded, so no channels")
        else:
            self.app.window.popup_channels()


    def cb_thresh(self, event):
        # Handle channel selection
        if not self.app.have_dset():
            self.app.popup_message("No data loaded, so no threhsolds")
        else:
            self.app.window.popup_thresh()


    def cb_colorby(self, event):
        if DEBUG: print(">> cb_colorby", event.GetString())


    def cb_selectmode(self, event):
        # Handle selection options:
        #   Idle = do nothing; Turn off select
        if event.GetString().upper().startswith('ID'):
            self.set_select(False)
            return
        #   Select = turn on select
        if event.GetString().upper().startswith('SEL'):
            self.set_select(True)
            return
        #   All = select all with any data, then set select on
        if event.GetString().upper().startswith('ALL'):
            cells = self.app.get_anydata_cells()
            # Set label before GUI update
            self.set_select(True)
            set_choice_label(self.cbox_select, 'SEL')
            self.app.mod_active_cells(alis=cells, dlis=None, guiup=True)
            return
        #   None = deselect all, then set select on 
        if event.GetString().upper().startswith('NO'):
            cells = self.app.get_active_cells()
            self.set_select(True)
            set_choice_label(self.cbox_select, 'SEL')
            self.app.mod_active_cells(alis=None, dlis=cells, guiup=True)
            return


    def setup_grid(self):
        """ Set up grid stuff
        """
        # Grid for '96 well plate' 
        self.grid = wx.grid.Grid(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.grid.CreateGrid(8, 12)
        # Selection callback binding
        # XXX Sham; Turned this off ... sort of helps clean up grid select???
        #self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.cb_grid_sel_cell)
        self.grid.Bind(gridlib.EVT_GRID_RANGE_SELECT, self.cb_grid_sel_cellrange)
        # Set grid attributes
        self.grid.EnableEditing(False)
        self.grid.EnableGridLines(True)
        # No resize xxx TODO Doesn't seem to work???
        self.grid.DisableDragGridSize()
        # Col and row labels
        self.grid.SetColLabelSize(20)
        for c in range(12):
            self.grid.SetColLabelValue(c, str(c+1))
        self.grid.SetRowLabelSize(40)
        for r, v in enumerate(list('ABCDEFGH')):
            self.grid.SetRowLabelValue(r, v)
        # Cell Defaults
        self.grid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)
        self.update_grid_cells(reset=True)
        # Add grid to main sizer; Proportion 1 = expand; Borders not on top
        self.sizer.Add(self.grid, 1, wx.EXPAND|azdef.SIZER_FLAG_NTOP, azdef.SIZER_BORDER)


    # XXX Sham, not calling this ... only cellrange
    def cb_grid_sel_cell(self, event):
        # Update for one cell; Cook up [(row,col)] list with tuple 
        self.update_cell_select([(event.GetRow(), event.GetCol())])


    def cb_grid_sel_cellrange(self, event):
        # Selected region
        if self.grid.GetSelectionBlockTopLeft():
            rows_start, cols_start = self.grid.GetSelectionBlockTopLeft()[0]
            rows_end, cols_end = self.grid.GetSelectionBlockBottomRight()[0]
        # Selected rows
        elif self.grid.GetSelectedRows():
            rows_start = self.grid.GetSelectedRows()[0]
            rows_end = self.grid.GetSelectedRows()[-1]
            cols_start = 0
            cols_end = self.grid.GetNumberCols()
        # Selected rows
        elif self.grid.GetSelectedCols():
            rows_start = 0
            rows_end = self.grid.GetNumberRows()
            cols_start = self.grid.GetSelectedCols()[0]
            cols_end = self.grid.GetSelectedCols()[-1]
        # Nothing
        else:
            return
        # Collect cells in range to update
        #print("+ cb_grid_sel_cellrange rows cols", rows_start,rows_end,cols_start,cols_end)
        cells = []
        for row in range(rows_start, rows_end+1):
            for col in range(cols_start, cols_end+1):
                cells.append((row, col))
        self.update_cell_select(cells)


    def update_cell_select(self, cells):
        """Update well selection via list of cells
        """
        #print(">> update_cell_select", cells)
        # If no dataset or not select mode, ignore
        if (not self.app.have_dset()) or (not self.get_select()):
            return
        # List of currently acive and any-data cells; If no data, can't select
        actives = self.app.get_active_cells()
        anydata = self.app.get_anydata_cells()
        # Collect cells to add / delete
        newadd = []
        newdel = []
        for cell in cells:
            if cell in actives:
                newdel.append(cell)
            elif cell in anydata:
                newadd.append(cell)
        #print("+ update_cell_select newadd", newadd)
        #print("+ update_cell_select newdel", newdel)
        self.app.mod_active_cells(newadd, newdel, guiup=True)


    def update_grid_cells(self, reset=True):
        on_color = self.app.get_setting('COLOR_GRID_WELL_ON')
        off_color = self.app.get_setting('COLOR_GRID_WELL_OFF')
        none_color = self.app.get_setting('COLOR_GRID_WELL_NONE')
        ontxt_color = self.app.get_setting('COLOR_GRID_TXT_ON')
        offtxt_color = self.app.get_setting('COLOR_GRID_TXT_OFF')
        # If reset, set everything to none; clis=None
        if reset:
            label_grid_cells(self.grid, clis=None, color=ontxt_color, show=False)
            color_grid_cells(self.grid, none_color, clis=None)
        # Background any-data cells set to off colors
        cells = self.app.get_anydata_cells()
        if len(cells) > 0:
            label_grid_cells(self.grid, clis=cells, color=offtxt_color, show=True)
            color_grid_cells(self.grid, off_color, clis=cells)
        # Active cells 
        cells = self.app.get_active_cells()
        if len(cells) > 0:
            label_grid_cells(self.grid, clis=cells, color=ontxt_color, show=True)
            color_grid_cells(self.grid, on_color, clis=cells)
    
        #print("+ update_grid_cells calling ClearSelection()")
        self.grid.ClearSelection()


# ---------------------------------------------------------------------------
# Report window 
class AzwinReportPanel(wx.Panel):
    """ Panel for various reporting
    """
    def __init__(self, parent, app):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.parent = parent 
        self.app = app
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.setup_button_panel()
        self.setup_report_space()
        wrap_up_sizing(self, self.sizer)
        # init default
        self.set_rpkey('Well')


    def setup_button_panel(self):
        """ Set up button panel stuff
        """
        self.panel_but = new_panel(self)
        self.sizer_but = wx.BoxSizer(wx.HORIZONTAL)
        self.win_label = new_statext(self.panel_but, "Report window", self.sizer_but)
        self.cbox_reportdata = new_choice(self.panel_but, self.cb_reportdata, 
             chlis=azdef.CM_REPORT_DATA, sizer=self.sizer_but, sizerprop=0)

        # Add button panel to main sizer; Proportion = 0 = don't stretch
        wrap_up_sizing(self.panel_but, self.sizer_but)
        self.sizer.Add(self.panel_but, 0, wx.EXPAND|wx.ALL, 5)


    def set_rpkey(self, rpkey):
        self.rpkey = rpkey.upper()


    def cb_reportdata(self, event):
        self.set_rpkey(event.GetString())
        self.report()


    def setup_report_space(self):
        """ Set up report text space
        """
        self.panel_rep = new_panel(self)
        self.sizer_rep = wx.BoxSizer(wx.HORIZONTAL)
        self.tex = new_text(self.panel_rep, '', sizer=self.sizer_rep, sizerprop=1)
        # Add report panel to main sizer; Proportion 1 = expand; Borders not on top
        wrap_up_sizing(self.panel_rep, self.sizer_rep)
        self.sizer.Add(self.panel_rep, 1, wx.EXPAND|azdef.SIZER_FLAG_NTOP, azdef.SIZER_BORDER)


    def report_text(self, text):
        self.tex.SetValue(str(text))

    # rrr
    def report(self):
        if self.rpkey.startswith('WELL'):
            self.report_wells()
        elif self.rpkey.startswith('CHAN'):
            self.report_channels()
        elif self.rpkey.startswith('THRESH'):
            self.report_thresholds()
        else:
            raise ValueError('Bogus report key', self.rpkey)


    def report_wells(self):
        # Local vars for dataframe and collections of Cq values
        df = self.app.get_field('DF_BLCOR')
        cqtdic = self.app.get_field('DIC_COL_CQT')
        cq2dic = self.app.get_field('DIC_COL_CQ2ND')
        # Collect lines of text 
        lines = []
        line = "Well Channel CqTh Cq2d Min Max".replace(' ', '\t')
        lines.append(line)
        # Each active columns
        cols = self.app.get_active_cols()
        for col in sorted(cols):
            well = azu.col_to_well(col)
            cidx = str(azu.col_to_chan_index(col) + 1)
            cqt = '{:5.2f}'.format(cqtdic[col])
            cq2 = '{:2d}'.format(cq2dic[col])
            cmin = '{:5.2f}'.format(df[col].min())
            cmax = '{:5.2f}'.format(df[col].max())
            # Cook up line
            words = [well, cidx, cqt, cq2, cmin, cmax]
            line = '\t'.join(words)
            lines.append(line)
        # New lines and show
        story = '\n'.join(lines)
        self.report_text(story)


    def report_channels(self):
        # Collect lines of text 
        lines = []
        line = "Channel Wells Name".replace(' ', '\t')
        lines.append(line)
        # Only if have data
        if self.app.have_dset():
            acols = self.app.get_active_cols()
            dset = self.app.dset
            # Each active channel
            chanlis = self.app.get_field('ACTIVE_CHANNEL_SET')
            for i in sorted(chanlis):
                cidx = str(i + 1)
                name = dset.ch_name_list()[i]
                # Active channels 
                chcols = self.app.get_chan_1index_cols(i+1) 
                num = len([x for x in acols if x in chcols])
                wells = '{:2d}'.format(num)
                # Cook up line
                words = [cidx, wells, name]
                line = '\t'.join(words)
                lines.append(line)
        # New lines and show
        story = '\n'.join(lines)
        self.report_text(story)


    def report_thresholds(self):
        # Collect lines of text 
        lines = []
        line = "Channel Thresh Min Max".replace(' ', '\t')
        lines.append(line)
        # Only if have data
        if self.app.have_dset():
            thvals = self.app.get_field('LIS_CHAN_THRESH')
            minvals = self.app.get_field('LIS_CHAN_MINS')
            maxvals = self.app.get_field('LIS_CHAN_MAXS')
            dset = self.app.dset
            # Each active channel
            chanlis = self.app.get_field('ACTIVE_CHANNEL_SET')
            for i in sorted(chanlis):
                cidx = str(i + 1)
                thresh = '{:6.1f}'.format(thvals[i])
                minv = '{:6.1f}'.format(minvals[i])
                maxv = '{:6.1f}'.format(maxvals[i])
                # Cook up line
                words = [cidx, thresh, minv, maxv]
                line = '\t'.join(words)
                lines.append(line)
        # New lines and show
        story = '\n'.join(lines)
        self.report_text(story)


# ---------------------------------------------------------------------------
# Menu 
class AzwinMenu(wx.MenuBar):
    """ Menu bar, menus and callbacks
    """
    def __init__(self, parent, app):
        super().__init__() 
        self.parent = parent 
        self.app = app

        # Using unicode strings as wxformbuilder generates this
        # File
        self.menu_file = wx.Menu()
        self.mentit_newproj = new_menu_item(self.menu_file, u"New project", self.cb_newproj)
        # File submenu open 
        self.menu_file_open = wx.Menu()
        self.menu_file.AppendSubMenu(self.menu_file_open, u"Open" )
        self.mentit_open_data = new_menu_item(self.menu_file_open, u"Data", self.cb_open_data)
        self.mentit_open_plate = new_menu_item(self.menu_file_open, u"Plate", self.cb_open_plate)
        self.mentit_open_proj = new_menu_item(self.menu_file_open, u"Project", self.cb_open_proj)
        self.mentit_open_proj = new_menu_item(self.menu_file_open, u"Prefs", self.cb_open_prefs)
        # File submenu save
        self.menu_file_save = wx.Menu()
        self.menu_file.AppendSubMenu(self.menu_file_save, u"Save" )
        self.mentit_save_plate = new_menu_item(self.menu_file_save, u"Plate", self.cb_save_plate)
        self.mentit_save_proj = new_menu_item(self.menu_file_save, u"Project", self.cb_save_proj)
        self.mentit_save_plate = new_menu_item(self.menu_file_save, u"Prefs", self.cb_save_prefs)
        # File submenu save as
        self.menu_file_saveas = wx.Menu()
        self.menu_file.AppendSubMenu(self.menu_file_saveas, u"Save as" )
        self.mentit_saveas_plate = new_menu_item(self.menu_file_saveas, u"Plate", self.cb_saveas_plate)
        self.mentit_saveas_proj = new_menu_item(self.menu_file_saveas, u"Project", self.cb_saveas_proj)
        self.mentit_saveas_proj = new_menu_item(self.menu_file_saveas, u"Prefs", self.cb_saveas_prefs)
        # File quit
        self.mentit_quit = new_menu_item(self.menu_file, u"Quit", self.cb_quit)
        self.Append(self.menu_file, u"File")

        # Tools
        self.menu_tools = wx.Menu()
        self.mentit_about = new_menu_item(self.menu_tools, "About", self.cb_about)
        self.mentit_simu = new_menu_item(self.menu_tools, "Simulation", self.cb_simu)
        self.mentit_prefs = new_menu_item(self.menu_tools, "Preferences", self.cb_prefs)
        self.mentit_resetlay = new_menu_item(self.menu_tools, "Reset layout", self.cb_resetlay)
        self.Append(self.menu_tools, "Tools")


    # Callback handlers
    def cb_newproj(self, event):
        not_yet(self, "new project")


    def cb_open_data(self, event):
        cfile = file_open_choose(self, ftype='data', wildcard=azdef.FILE_CSV_WCARD)
        if cfile:
            self.app.handle_load_data(cfile)


    def cb_open_plate(self, event):
        not_yet(self, "open plate")


    def cb_open_proj(self, event):
        not_yet(self, "open project")


    def cb_open_prefs(self, event):
        cfile = file_open_choose(self, ftype='prefs', wildcard=azdef.FILE_JSON_WCARD)
        if cfile:
            self.app.load_user_prefs(cfile, popup=True)


    def cb_save_proj(self, event):
        not_yet(self, "save project")


    def cb_save_plate(self, event):
        not_yet(self, "save plate")


    def cb_save_prefs(self, event):
        self.app.save_user_prefs(popup=True)


    def cb_saveas_proj(self, event):
        not_yet(self, "save project (as)")


    def cb_saveas_plate(self, event):
        not_yet(self, "save plate (as)")


    def cb_saveas_prefs(self, event):
        cfile = file_open_choose(self, ftype='prefs', save=True, wildcard=azdef.FILE_JSON_WCARD)
        if DEBUG: print("prefs", type(cfile), cfile)
        if cfile:
            self.app.save_user_prefs(fname=cfile, popup=True)


    def cb_quit(self, event):
        self.app.close()


    def cb_about(self, event):
        # Create and fill the info object
        info = wx.adv.AboutDialogInfo()
        info.Name = self.app.get_field('PROG_NAME')
        info.Version = self.app.get_field('VERSION_S')
        info.Copyright = self.app.get_field('COPYRIGHT_S')
        info.Description = self.app.get_field('PROG_TITLE')
        # call wx.AboutBox with info 
        wx.adv.AboutBox(info)


    def cb_prefs(self, event):
        self.app.window.popup_preferences()


    def cb_simu(self, event):
        not_yet(self, "simulation")


    def cb_resetlay(self, event):
        self.app.apply_gui_settings()


# ---------------------------------------------------------------------------
# Channels dialog
class AzwinChannels(wx.Dialog):
    """ Channel selection dialog; All / None buttons, per-channel checkbox
    """
    def __init__(self, parent, app):
        super().__init__(parent, title="Channels")
        self.parent = parent 
        self.app = app
        # Should never get here without any channels
        n = self.app.get_field('DSET_NUM_CHAN', None)
        assert(n > 0)

        # Get and set window size
        winsize = self.app.get_setting('CHANNEL_WIN_SIZE')
        self.SetSize(winsize)
        # Main panel and sizer
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Local vars pointing to global channel list and set
        #   Modifying these, modifies main 
        self.clabs = self.app.get_field('LIS_CHAN_LABELS')
        self.cset = self.app.get_field('ACTIVE_CHANNEL_SET')

        # Buttons and check boxes for each channel
        self.btn_all = new_button(self.panel, "All", self.cb_all, sizer=self.sizer)
        self.btn_none = new_button(self.panel, "None", self.cb_none, sizer=self.sizer)
        self.checks = {}
        for lab in self.clabs:
            cbox = new_checkbox(self.panel, lab, self.cb_check, sizer=self.sizer)
            self.checks[lab] = cbox
        # Set checkboxes to reflect to channel set
        self.set_checkbox_vals()
        # Final sizing stuff
        wrap_up_sizing(self.panel, self.sizer)


    def set_checkbox_vals(self):
        """ Update checkboxes based on channel set membership
        """
        for idx, lab in enumerate(self.clabs):
            if idx in self.cset:
                val = True
            else:
                val = False
            self.checks[lab].SetValue(val)


    def cb_all(self, event):
        # All channels = set of all indices
        self.cset |= set(range(len(self.clabs)))
        self.set_checkbox_vals()
        self.app.window_update()


    def cb_none(self, event):
        self.cset.clear()
        self.set_checkbox_vals()
        self.app.window_update()


    def cb_check(self, event):
        # Channel check box event
        #   Get channel labels and checkbox value (true/false) and update set
        lab = event.GetEventObject().GetLabel()
        # Channel label to index; e.g. 'Channel_2' >--> 1
        idx = int(lab.split('_')[1]) - 1
        val = event.GetEventObject().GetValue()
        if val:
            self.cset.add(idx)
        else:
            self.cset.remove(idx)
        self.app.window_update()


# ---------------------------------------------------------------------------
# Thresholds dialog
class AzwinThresholds(wx.Dialog):
    """ Threshold selection dialog; per-channel slider
    """
    def __init__(self, parent, app):
        super().__init__(parent, title="Thresholds")
        self.parent = parent 
        self.app = app
        # Should never get here without any channels
        n = self.app.get_field('DSET_NUM_CHAN', None)
        assert(n > 0)

        #print(">> AzwinThresholds")
        # Get and set window size
        winsize = self.app.get_setting('THRESH_WIN_SIZE')
        self.SetSize(winsize)
        # Main panel and sizer
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Local vars pointing to global thresh list
        #   Keep initial values for reset
        self.clabs = self.app.get_field('LIS_CHAN_LABELS')
        self.minvals = self.app.get_field('LIS_CHAN_MINS')
        self.maxvals = self.app.get_field('LIS_CHAN_MAXS')
        self.thresh = self.app.get_field('LIS_CHAN_THRESH')
        self.o_thresh = [x for x in self.thresh]

        # Label, slider, button for each channel; Only keep sliders
        self.sliders = {}
        self.rbuts = {}
        for i, lab in enumerate(self.clabs):
            # color, panel and sizer
            color = self.app.chan_1index_color(i+1)
            span = new_panel(self.panel)
            spsizer = wx.BoxSizer(wx.HORIZONTAL)
            # Label, slider, button
            slab = new_statext(span, lab, spsizer, sizerprop=0)
            slider = new_slider(span, lab, self.cb_adjust, sizer=spsizer, sizerprop=1)
            slider.SetBackgroundColour(color)
            rbut = new_button(span, "Reset", self.cb_reset, name=lab, sizer=spsizer, sizerprop=0)
            wrap_up_sizing(span, spsizer)
            self.sizer.Add(span, 0, wx.EXPAND|azdef.SIZER_FLAG_NTOP, azdef.SIZER_BORDER)
            # Keep for call backs
            self.sliders[lab] = slider
            self.rbuts[lab] = rbut

        # Final sizing stuff
        wrap_up_sizing(self.panel, self.sizer)
        # Set intial parameters
        self.set_slider_params()
        #print("<< AzwinThresholds")


    def set_slider_params(self):
        # Update parameters for all sliders
        for i, lab in enumerate(self.clabs):
            slider = self.sliders[lab]
            # Set position for thresh value
            val_to_slider(slider, self.thresh[i], self.minvals[i], self.maxvals[i], invert=False, setpos=True)


    def cb_adjust(self, event):
        # Channel slider, name for index, then value from pos
        slider = event.GetEventObject()
        name = slider.GetName()
        idx = azu.index_from_chanlab(name)
        # Value needs real (channel) min, max
        val = slider_to_val(slider, self.minvals[idx], self.maxvals[idx], invert=False)
        if DEBUG: print(">> cb_adjust", name, idx, val)
        self.set_chidx_thresh(idx, val)
        if DEBUG: print("<< cb_adjust")


    def cb_reset(self, event):
        # Reset thresh to defaults
        name = event.GetEventObject().GetName()
        if DEBUG: print(">> cb_reset", name)
        idx = azu.index_from_chanlab(name)
        # Get thresh from original copy and set this
        self.set_chidx_thresh(idx, self.o_thresh[idx])
        self.set_slider_params()


    def set_chidx_thresh(self, idx, thresh):
        self.thresh[idx] = float(thresh)
        self.app.init_cqts()
        self.app.window_update()


# ---------------------------------------------------------------------------
# Preferences dialog
class AzwinPrefs(wx.Dialog):
    """ Preferences dialog
    """
    def __init__(self, parent, app):
        super().__init__(parent, title="Preferences")
        self.parent = parent 
        self.app = app
        # Main panel and sizer
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Button panel 
        self.panel_but = new_panel(self, sizer=self.sizer)
        self.sizer_but = wx.BoxSizer(wx.HORIZONTAL)
        # XXX interesting sham; Buttons with panel_but parent don't work on windows?
        self.btn_edit = new_button(self.panel_but, "Edit", self.cb_edit, sizer=self.sizer_but)
        self.btn_apply = new_button(self.panel_but, "Apply", self.cb_apply, sizer=self.sizer_but)
        self.btn_default = new_button(self.panel_but, "Default", self.cb_default, sizer=self.sizer_but)
        self.btn_cancel = new_button(self.panel_but, "Cancel", self.cb_cancel, sizer=self.sizer_but)

#        self.btn_edit = new_button(self.panel, "Edit", self.cb_edit, sizer=self.sizer_but)
#        self.btn_apply = new_button(self.panel, "Apply", self.cb_apply, sizer=self.sizer_but)
#        self.btn_default = new_button(self.panel, "Default", self.cb_default, sizer=self.sizer_but)
#        self.btn_cancel = new_button(self.panel, "Cancel", self.cb_cancel, sizer=self.sizer_but)

        wrap_up_sizing(self.panel_but, self.sizer_but)

        # Get two copies of settings; Orig in case canel, other to modify 
        self.origdic = dict(self.app.settings)
        self.udic = dict(self.app.settings)
        # List of user-settable keys
        ulis = self.app.usetting_list()
        self.cbox = new_combobox(self.panel, "Settings", self.cb_cbox, ulis, self.sizer)
        # Init stat has no user key
        self.ukey = None
        self.modified = False
        self.n_mods = 0

        # Report window for feedback
        self.text = new_text(self, message='', sizer=self.sizer)

        # Main panel / sizer
        wrap_up_sizing(self.panel, self.sizer)


    def cb_edit(self, event):
        val = self.app.get_setting(self.ukey, None)
        if val is None:
            return
        # Based on type, get different dialog
        if azu.re_color(val):
            res = popup_getcolor(self, val)
        else:
            # Pick checking function based on setting value type
            if azu.re_float(val):
                ckfunc = azu.re_float
            elif azu.re_number(val):
                ckfunc = azu.re_number
            else:
                ckfunc = None
            # Call to get value
            res = popup_getval(self, "Enter new setting", self.ukey, val, ckfunc=ckfunc)
        # Keep result
        if res is not None:
            self.udic[self.ukey] = res
            self.text.SetValue("{} Set to: {} (Not saved)".format(self.ukey, res))
            self.modified = True
            self.n_mods += 1
        else:
            self.text.SetValue("{} Not modified".format(self.ukey))


    def cb_apply(self, event):
        if not self.modified:
            self.text.SetValue("Nothing to save")
            return
        # Copy local settings dict back to main
        self.app.settings = dict(self.udic)
        self.modified = False
        self.text.SetValue("All settings saved")
        self.app.apply_gui_settings()
        self.app.window_update()
        

    def cb_default(self, event):
        # Copy default value
        val = self.app.get_defsetting(self.ukey, None)
        if val is not None:
            self.udic[self.ukey] = val
            self.text.SetValue("{} set to default: {}".format(self.ukey, val))
            self.modified = True


    def cb_cancel(self, event):
        if not self.n_mod < 1:
            self.text.SetValue("Nothing changed, nothing to restore")
            return
        # Copy original settings dict back to main
        self.app.settings = dict(self.origdic)
        self.text.SetValue("Original settings restored")
        self.app.apply_gui_settings()
        self.app.window_update()
        

    def cb_cbox(self, event):
        self.ukey = event.GetEventObject().GetValue()


# ---------------------------------------------------------------------------
# General functions

def new_splitter(parent, sashfrac=0.5, sashpos=-1, gravity=0.5, sashsize=10, minpane=20, color=None):
    """ Create new splitter window in standard way
    Code based on wxformbuilder auto-gen code

    Returns wxSplitterWindow
    """
    wxid = wx.NewId()
    splitter = wx.SplitterWindow(parent, id=wxid, style=wx.SP_3D)
    config_splitter(splitter, gravity=gravity, sashsize=sashsize, minpane=minpane, color=color)
    return splitter


def config_splitter(splitter, sashfrac=0.5, sashpos=-1, gravity=None, sashsize=None, minpane=None, color=None):
    """ Standardish config settings for splitter

    sashfrac = fraction of window for sash position; Not used if sashpos >= 0
    sashpos = absolute sash position; If negative, use fraction
    Saves sashfrac (either given or computed) in splitter var

    Other parameters are set only if not None
    """
    if sashpos < 0:
        sashpos = splitter_sash_pos4frac(splitter, sashfrac)
        given_frac = sashfrac
    else:
        given_frac = splitter_sash_frac4pos(splitter, sashpos)
    splitter.SetSashPosition(sashpos)
    splitter.given_frac = given_frac
    # Only if real arguments
    if gravity:
        splitter.SetSashGravity(gravity)
    if sashsize:
        splitter.SetSashSize(sashsize)
    if minpane:
        splitter.SetMinimumPaneSize(minpane)
    if color:
        splitter.SetBackgroundColour(color)


def reset_splitter_sash(splitter):
    """ Reset splitter sash position based on (saved) fractional value
    """
    config_splitter(splitter, sashfrac=splitter.given_frac)


def splitter_sash_pos4frac(splitter, frac):
    """ Get splitter sash position based on fraction and window orientation/size
    """
    parent = splitter.GetParent()
    if splitter.GetSplitMode() == wx.SPLIT_HORIZONTAL:
        tot = max(splitter.GetMinimumPaneSize(), splitter.GetParent().GetClientSize().height)
    else:
        tot = max(splitter.GetMinimumPaneSize(), splitter.GetParent().GetClientSize().width)
    return int(round(tot * frac))


def splitter_sash_frac4pos(splitter, spos):
    """ Get splitter sash fraction based on position and window orientation/size
    """
    parent = splitter.GetParent()
    if splitter.GetSplitMode() == wx.SPLIT_HORIZONTAL:
        tot = max(splitter.GetMinimumPaneSize(), splitter.GetParent().GetClientSize().height)
    else:
        tot = max(splitter.GetMinimumPaneSize(), splitter.GetParent().GetClientSize().width)
    return spos/tot


def new_panel(parent, color=None, sizer=None, sizerprop=0):
    """ Create new panel in standard way
    Code based on wxformbuilder auto-gen code

    Returns wxPanel
    """
    wxid = wx.NewId()
    panel = wx.Panel(parent, id=wxid, style=wx.TAB_TRAVERSAL)
    config_panel(panel, color=color)
    if sizer is not None:
        sizer.Add(panel, sizerprop, wx.ALL | wx.EXPAND, azdef.SIZER_BORDER)
    return panel


def config_panel(panel, color=None):
    """ Standardish config settings for panel
    """
    if color is not None:
        panel.SetBackgroundColour(color)
    else:
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))


def new_menu_item(parent, label, cbfunc):
    """ Standardish creation and setup of menu item
    Creates menu item with given label
    Binds cbfunc as callback
    Attaches item to parent (menu)

    Returns wxMenuItem
    """
    wxid = wx.NewId()
    menit = wx.MenuItem(parent, id=wxid, text=label, helpString="")
    parent.Append(menit)
    parent.Bind(wx.EVT_MENU, cbfunc, menit)
    return menit


def new_button(parent, label, cbfunc, name=wx.ButtonNameStr, sizer=None, sizerprop=0):
    """ Standardish create and setup of button
    Creates button item with given label
    Binds cbfunc as callback
    If sizer, adds to that

    Returns wxButton 
    """
    wxid = wx.NewId()
    button = wx.Button(parent, id=wxid, name=name, label=label)
    button.Bind(wx.EVT_BUTTON, cbfunc, button)
    if sizer is not None:
        sizer.Add(button, sizerprop, wx.ALL, azdef.SIZER_BORDER)
    return button


def new_text(parent, message='', readonly=True, sizer=None, sizerprop=1):
    """ Standardish text controler (dynamic writing space)
    If message, set that
    If sizer, add to that

    Returns wxTxtClrl
    """
    wxid = wx.NewId()
    # Style = always multi-line, maybe readonly
    if readonly:
        style = wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_READONLY
    else:
        style = wx.BORDER_NONE | wx.TE_MULTILINE
    # Get text, add to sizer if we've got one
    position = (20, 20)
    tex = wx.TextCtrl(parent, id=wxid, value=str(message), pos=position, style=style)
    if sizer is not None:
        sizer.Add(tex, sizerprop, wx.ALL | wx.EXPAND, azdef.SIZER_BORDER)
    return tex


def new_statext(parent, message, sizer=None, sizerprop=0):
    """ Standardish text controler (static writing space)
    If sizer, add to that

    Returns wxStaticText
    """
    wxid = wx.NewId()
    tex = wx.StaticText(parent, id=wxid, label=message)
    if sizer is not None:
        sizer.Add(tex, sizerprop, wx.ALL, azdef.SIZER_BORDER)
    return tex


def new_choice(parent, cbfunc, chlis=None, sizer=None, sizerprop=0):
    """ Standardish choice picker 
    Set callback
    If sizer, add to that

    Returns wxChoice
    """
    wxid = wx.NewId()
    choice = wx.Choice(parent, id=wxid, choices=chlis)
    choice.SetSelection(0)
    choice.Bind(wx.EVT_CHOICE, cbfunc, choice)
    if sizer is not None:
        sizer.Add(choice, sizerprop, wx.ALL, azdef.SIZER_BORDER)
    return choice


def set_choice_label(wxchoice, label):
    """ Attempt to set given label as active in given wxChoice
    First case-insensitive choice starting with given label matches
    
    If found, sets choice and returns True; Else False
    """
    for i in range(wxchoice.GetCount()):
        c = wxchoice.GetString(i).upper()
        if c.startswith(label.upper()):
            wxchoice.SetSelection(i)
            return True
    return False


def new_combobox(parent, what, cbfunc, chlis=None, sizer=None, sizerprop=1):
    """ Standardish picker 
    Set callback
    If sizer, add to that

    Returns wxComboBox
    """
    if chlis is None:
        choices = [what]
    else:
        choices = [what] + chlis
    style = wx.CB_READONLY | wx.CB_DROPDOWN
    wxid = wx.NewId()
    cbox = wx.ComboBox(parent, wxid, what, choices=choices, style=style)
    cbox.Bind(wx.EVT_COMBOBOX, cbfunc, cbox)
    if sizer is not None:
        sizer.Add(cbox, sizerprop, wx.ALL, azdef.SIZER_BORDER)
    return cbox


def new_checkbox(parent, label, cbfunc, sizer=None, sizerprop=0):
    """ Standardish checkbox
    Set callback
    If sizer, add to that

    Returns wxCheckBox
    """
    wxid = wx.NewId()
    cbox = wx.CheckBox(parent, id=wxid, label=label)
    cbox.Bind(wx.EVT_CHECKBOX, cbfunc)
    if sizer is not None:
        sizer.Add(cbox, sizerprop, wx.ALL, azdef.SIZER_BORDER)
    return cbox


def new_slider(parent, label, cbfunc, horiz=True, sizer=None, sizerprop=1, lab=False):
    """ Standardish slider
    Set callback
    If sizer, add to that

    Returns wxSlider
    """
    #print(">> new_slider horiz, sizer", horiz, sizer)
    wxid = wx.NewId()
    if horiz:
        style = wx.SL_HORIZONTAL
    else:
        style = wx.SL_VERTICAL
    if lab:
        style |= wx.SL_LABELS
    slider = wx.Slider(parent, id=wxid, name=label, style=style)
    # NOTE; All commented out shams didn't prevent excess callbacks ...
    #slider.Bind(wx.EVT_SCROLL, cbfunc)
    #slider.Bind(wx.EVT_SLIDER, cbfunc)
    #slider.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, cbfunc)
    # This seems to work
    slider.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, cbfunc)
    if sizer is not None:
        flag = wx.ALL | wx.EXPAND
        sizer.Add(slider, sizerprop, flag, azdef.SIZER_BORDER)
    #print("<< new_slider", slider)
    return slider


def slider_to_val(slider, vmin, vmax, invert=True):
    """Take slider and get real-scale value from settings
    Requires real-scale min and max
    Flag inverted means that scale is displayed backwards
    Return value
    """    
    srange = float(slider.GetMax() - slider.GetMin())
    vrange = vmax - vmin
    if invert:
        sd = float(slider.GetMax() - slider.GetValue())
    else:
        sd = float(slider.GetValue() - slider.GetMin())
    v = vmin + vrange * sd / srange
    return v


def val_to_slider(slider, val, vmin, vmax, invert=True, setpos=True):
    """Take slider and real-scale values to get slider-scale value
    Requires real-scale value, min and max
    Flag inverted means that scale is displayed backwards
    If setpos is True, update slider position
    Return slider position value
    """    
    srange = float(slider.GetMax() - slider.GetMin())
    vrange = vmax - vmin
    vdelta = val - vmin
    if invert:
        p = slider.GetMax() - int(srange * vdelta / vrange)
    else:
        p = slider.GetMin() + int(srange * vdelta / vrange)
    # Set slider position?
    if setpos:
        slider.SetValue(p)
    return p


def color_grid_cells(grid, color, clis=None):
    """ Set color for list of grid cells (as row,col tuples)
    If no list is given, set all
    """
    if clis is None:
        clis = azu.plate96_cell_list()
    for cell in clis:
        r,c = cell
        grid.SetCellBackgroundColour(r, c, color)


def label_grid_cells(grid, clis=None, color=None, show=True):
    """ Set label for list of grid cells 
    If no list is given, set all
    """
    if clis is None:
        clis = azu.plate96_cell_list()
    for cell in clis:
        r,c = cell
        # Show = text or not
        if show:
            well = azu.cell_to_well(cell)
            grid.SetCellValue(r, c, well)
        else:
            grid.SetCellValue(r, c, '')
        # Set color?
        if color is not None:
            grid.SetCellTextColour(r, c, color)


def wrap_up_sizing(obj, sizer):
    """ Tie together sizing shams for obj and its sizer
    """
    obj.SetSizer(sizer)
    obj.Layout()
    sizer.Fit(obj)


def popup_message(parent, message):
    title = parent.app.get_field('PROG_NAME') + " message"
    dlg = wx.MessageDialog(parent, message, title, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


def popup_getval(parent, title, message, val, ckfunc=None):
    """ Get input value via popup box
    title is for the popup window
    message is printed above input
    val is the default value (as string or could-be-string)
    ckfunc is value checking function; If present, input checked with this

    Returns value; If ckfunc, whatever that returns, else raw
    """
    dlg = wx.TextEntryDialog(parent, message, title)
    dlg.SetValue(str(val))
    new_val = None
    if dlg.ShowModal() == wx.ID_OK:
        v = dlg.GetValue()
        if ckfunc is not None:
            new_val = ckfunc(v)
        else:
            new_val = v
    dlg.Destroy()
    return new_val


def popup_getcolor(parent, val):
    """ Get color via popup picker dialog
    Val = current/default color, as string like '#80a0c0'

    Returns color as string like '#80a0c0'
    """
    # Need 'ColourData' to set existing value
    col = wx.Colour()
    col.Set(val)
    cd = wx.ColourData()
    cd.SetColour(col)
    # print("ggg", val, col, x, cd)
    dlg = wx.ColourDialog(parent, cd)
    col = None
    if dlg.ShowModal() == wx.ID_OK:
        col = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
    dlg.Destroy()
    return col


def not_yet(parent, message):
    message = "Sorry, " + message + " isn't available"
    popup_message(parent, message)


def file_open_choose(parent, ftype=None, save=False, wildcard=azdef.FILE_DEF_WCARD):
    """ Standardish file open dialog

    Returns filename / None
    """ 
    if ftype:
        message="Choose a " + ftype + " file"
    else:
        message="Choose a file"
    # Default dir = current file path
    defdir = parent.app.get_setting('DEF_FILE_PATH', '.')
    if save:
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    else:
        style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW
    # Popup 
    dlg = wx.FileDialog(parent, message=message, defaultFile='', 
        defaultDir=defdir, wildcard=wildcard, style=style)
    # If return is OK, that's the file
    chosen = None
    if dlg.ShowModal() == wx.ID_OK:
        paths = dlg.GetPaths()
        chosen = paths[0]
    # Important to kill dialog
    dlg.Destroy()
    return chosen 

