#!/usr/bin/env python
# 2/14/18 RTK
# 3/18/18 RTK update
# 8/17/19 RTK; V0.22; Clean up code some (pylint; DEBUG)
#
# Default settings collection, constants for Azure In-house PCR Analysis tool
#

import wx

settings = {
    'MAIN_WIN_SIZE'     : (1550, 980),
    'MAIN_WIN_POS'      : (10, 10),
    'MAIN_SPLIT_LR_POS' : 900,
    'MAIN_SPLIT_LTB_POS' : 500,
    'MAIN_SPLIT_RTB_POS' : 420,
    'CHANNEL_WIN_SIZE'  : (200, 280),
    'THRESH_WIN_SIZE'   : (450, 280),
    'PGRID_ROW_SIZE'    : 38,
    'PGRID_COL_SIZE'    : 45,
    'COLOR_WIN_PLOT'    : '#c0d0f0',
    'COLOR_WIN_CURVE'   : '#a090d0',
    'COLOR_WIN_PLATE'   : '#80a0c0',
    'COLOR_WIN_REPORT'  : '#c0c0f0',
    'PREFS_FNAME'       : 'azipa_prefs.json',
    'DEF_FILE_PATH'     : '.',
    'COLOR_GRID_WELL_ON'    : '#ffff60',
    'COLOR_GRID_WELL_OFF'   : '#bbbb60',
    'COLOR_GRID_WELL_NONE'  : '#999999',
    'COLOR_GRID_TXT_ON'     : '#000000',
    'COLOR_GRID_TXT_OFF'    : '#555555',
    'COLOR_CHANNEL_1' : '#ccaa00',
    'COLOR_CHANNEL_2' : '#dd8822',
    'COLOR_CHANNEL_3' : '#ff2255',
    'COLOR_CHANNEL_4' : '#cc55cc',
    'COLOR_CHANNEL_5' : '#5588ff',
    'COLOR_CHANNEL_6' : '#55ffff',
    'DEF_THRESH_FRAC' : 0.1,
}

# User-settable filter words; Can't change these
uset_filtwords = ['MAIN_', '_SIZE']


# GUI layout (sizer) border size
SIZER_BORDER = 5

# Sizer flags to put border all sides but top
SIZER_FLAG_NTOP = wx.LEFT|wx.BOTTOM|wx.RIGHT

# Minimum plot X (number),Y (fraction of range) max-min delta
PLOT_XDELTA_MIN = 2
PLOT_YDELTA_MIN = 0.02


# Choice menu lists ' ... first (non-real) list item
CM_PLATE_CHANNEL = ['Channel']
CM_PLATE_COLORBY = ['ColorBy']
CM_PLATE_SELECT = ["Idle (Select)", "Select", "All", "None"]
CM_PLOT_DATA = ["Base Corrected", "Raw", "1st derivative", "2nd derivative"]
CM_REPORT_DATA = ["Wells", "Channels", "Thresholds"]


# Misc constants
FILE_DEF_WCARD =    "All files (*.*)|*.*"

FILE_CSV_WCARD =    "CSV data (*.csv)|*.csv|"  \
                    "All files (*.*)|*.*"

FILE_JSON_WCARD =   "CSV data (*.json)|*.json|"  \
                    "All files (*.*)|*.*"



if __name__ == "__main__":
    print("Collection of settings (default); N={0}".format(len(settings)))
    for k in sorted(settings.keys()):
        print("\t", k, "=", settings[k])
