# ##############################################################################
"""Plotting subsidence and groundwater model results.

Output:
Subsidence
1. Bar graphs of annual subsidence (cm) for each well nest during 1978-2020
(Shown in the main text and supplemental information)
2. Line graphs of annual subsidence (cm) for sensitivity analyses of each parameter
(Sskv, Sske, K, thickness) for one well nest (long run time so only calculating for
one well nest at a time) (Shown in supplemental information)
3. Line graphs of cumulative subsidence (cm) into the future depending on the
pumping scenario for each well nest during 1978-2060 (Shown in the main text and
supplemental information)
Groundwater
4. Groundwater model graphical results shown in the paper and supplemental
information. Simulated vs observed groundwater and inputs
5. Spatial maps that show the groundwater RMSE and t190 results for each well in
each well nest. Imports previously created Pastas models

Jenny Soonthornrangsan 2023
TU Delft
"""
# ##############################################################################

###############################################################################
# import statements
###############################################################################

import os
import pandas as pd
import datetime as dt
from sklearn.metrics import mean_squared_error
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from mycolorpy import colorlist as mcp
from matplotlib.ticker import (AutoMinorLocator)
from matplotlib.collections import PatchCollection
from matplotlib.patches import Wedge
from statistics import median


# %%###########################################################################
# Plotting settings
###############################################################################

plt.rc("font", size=12)  # controls default text size
plt.rc("axes", titlesize=5)  # fontsize of the title
plt.rc("axes", labelsize=6)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=6)  # fontsize of the x tick labels
plt.rc("ytick", labelsize=6)  # fontsize of the y tick labels
plt.rc("legend", fontsize=8)  # fontsize of the legend


# %%###########################################################################
# Plotting results
##############################################################################

def sub_bar(path, wellnestlist, all_results,
            sub_total, subv_total,
            annual_data, tmin=None, tmax=None, save=0,
            benchflag=0):
    """Plot annual subsidence results.

    Bar graphs of annual subsidence (cm) for each well nest during 1978-2020
    (Shown in the main text and supplemental information)

    path - str: path to save figures
    wellnestlist - list of wellnests that were simualted
    all_results - lists of lists: wellnestname, well name, head matrix with
    head series of each node
    sub_total - lists of lists: wellnestname, well_name, total cum sub
    subv_total - lists of lists: wellnestname, well_name, inelastic cum sub
    annual_data - lists of lists: wellnestname, well_name, total cum sub for
    all four clay at a wellnest location
    save - if 1, save; if 0, don't save
    benchflag: no benchmark - if 0, no plot, if 1, benchmark, plot
    Assume also that benchmark comparison starts at 0

    # ASSUMES FOUR WELLS IN WELLNEST
    """
    # saving rmse
    rmse = []

    # For each wellnest in list
    # num_well is the index, wellnest = name
    # Figures for each well nest
    for num_well, wellnest in enumerate(wellnestlist):

        if benchflag == 1:

            # Subsidence plotting
            # Getting benchmark time series
            loc = os.path.join(os.path.abspath("inputs"), "SurveyingLevels.xlsx")
            try:
                subdata = pd.read_excel(loc, sheet_name=wellnest + "_Leveling",
                                        index_col=3)
                subdata = pd.DataFrame(subdata)
                subdata.index = pd.to_datetime(subdata.index)

                # Getting rid of benchmarks outside time period
                subdata = subdata[(subdata.Year <= 2020)]

                # Benchmarks should start at 0 at the first year.
                bench = subdata.loc[:, subdata.columns.str.contains("Land")]
                bench = bench.fillna(0)

                if (bench.iloc[0] != 0).any():
                    bench.iloc[0] = 0

                # IMPORTANT INFO
                # For benchmark measurements, the first year is 0, the second year
                # is the compaction rate over that first year.
                # For implicit Calc, the first year has a compaction rate over that
                # year, so to shift benchmarks value to the previouse year to match
                # Index has the right years
                bench.index = bench.index.shift(-1, freq="D")
                bench["date"] = bench.index

                # Gets the last date of each year
                lastdate = bench.groupby(pd.DatetimeIndex(bench["date"]).year,
                                         as_index=False).agg(
                                             {"date": max}).reset_index(drop=True)
                bench = bench.loc[lastdate.date]

            except:

                bench = pd.DataFrame()

        # BAR PLOT preparation
        daterange = pd.date_range(dt.datetime(1978, 12, 31), periods=43,
                                  freq="Y").tolist()
        df = pd.DataFrame(daterange, columns=["date"])

        x = np.arange(43)
        width = .5

        # Figure plotting model results against measurements
        # Converts to cm to match measurements
        plt.figure(figsize=(6.75, 3.38), dpi=300)

        # Bar graph
        # annual data in cm
        plot_data = df.merge(annual_data[num_well][1]*100, left_on=df.date,
                             right_on=annual_data[num_well][1].index,
                             how="left")
        # Renaming for second merge
        plot_data = plot_data.rename(columns={"key_0": "key0"})

        # Filling na with 0
        plot_data = plot_data.fillna(0)

        plt.bar(x,
                -plot_data.AnnRates,
                label="Simulated", width=width,
                linewidth=.5, edgecolor="k")

        # Plotting benchmarks
        if benchflag == 1:

            if not bench.empty:
                # Measurements
                # Bar plot
                # Benchamrks already in cm
                plot_data = plot_data.merge(bench, left_on=plot_data.key0,
                                            right_on=bench.index,
                                            how="left")
                # Renaming for other merge
                plot_data = plot_data.rename(columns={"key_0": "key1"})

                # Filling na with 0
                plot_data = plot_data.fillna(0)

                plt.bar(x+width, -plot_data[
                    plot_data.columns[
                        plot_data.columns.str.contains("Land")].item()],
                        color="orange", linewidth=.5,
                        label="Observed", width=width, edgecolor="k")

            # Dropping NAs
            plot_data = plot_data.dropna()

            # Calculating RMSE
            rms = mean_squared_error(plot_data[
                plot_data.columns[
                    plot_data.columns.str.contains("Land")].item()],
                plot_data.AnnRates, squared=False)

            # Plotting settings
            plt.legend(loc="center right")
            plt.ylim((-2, 10))
            plt.ylabel("Annual Subsidence Rate (cm/yr)")
            plt.xlabel("Years")
            plt.annotate("RMSE: " + "{:.1f}".format(rms) + " cm/year",
                         xy=(1, 0), xycoords="axes fraction",
                         fontsize=10, horizontalalignment="right",
                         verticalalignment="bottom")

            # saving rmse
            rmse.append(rms)

            ax = plt.gca()
            plt.draw()
            plt.axhline(y=0, color="k", linestyle="-", linewidth=1)
            ax.set_xticklabels(ax.get_xticks(), rotation=45)
            plt.xticks(x+width, ["1978", "", "1980", "", "1982",
                                 "", "1984", "", "1986", "",
                                 "1988", "", "1990", "", "1992",
                                 "", "1994", "", "1996", "",
                                 "1998", "", "2000", "", "2002",
                                 "", "2004", "", "2006", "",
                                 "2008", "", "2010", "", "2012",
                                 "", "2014", "", "2016", "",
                                 "2018", "", "2020"])

            # If saving figure
            if np.logical_and(save == 1, benchflag == 1):

                fig_name = wellnest + "_BenchvsImplicit_AnnSubTotal.eps"
                full_figpath = os.path.join(path, fig_name)
                plt.savefig(full_figpath, format="eps")


def gwlocs_map(path, save=0):
    """Spatial mapping of groundwater well nest locations in BKK.

    path - path to save figures
    save - save or not save figures
    """
    # Importing spatial coordinates
    full_path = os.path.join(os.path.abspath("inputs"), "GroundwaterWellLocs.xls")
    gwwell_locs = pd.read_excel(full_path)

    # Locations of wellnests removing duplicates
    gwwell_locs = gwwell_locs.drop_duplicates("WellNest_Name", keep="first")

    # Unique well nests and locations only
    unique = []

    # Preallocation
    # Saving relevant xs, ys
    xs = []
    ys = []

    # Labels
    labels = []

    # list of wellnest names
    wellnestlist = ["LCBKK003",
                    "LCBKK005",
                    "LCBKK006",
                    "LCBKK007",
                    "LCBKK009",
                    "LCBKK011",
                    "LCBKK012",
                    "LCBKK013",
                    "LCBKK014",
                    "LCBKK015",
                    "LCBKK016",
                    "LCBKK018",
                    "LCBKK020",
                    "LCBKK021",
                    "LCBKK026",
                    "LCBKK027",
                    "LCBKK036",
                    "LCBKK038",
                    "LCBKK041",
                    "LCNBI003",
                    "LCNBI007",
                    "LCSPK007",
                    "LCSPK009"]

    # Getting rid of repeating wells and data points
    # zip joins x and y coordinates in pairs
    for x, y in zip(gwwell_locs.Long, gwwell_locs.Lat):

        # Check if x, y is unique
        if (x, y) not in unique:

            # Saves this location for plotting
            unique.append((x, y))

            # Label is well nest name
            label = gwwell_locs.loc[
                gwwell_locs.Long == x]["WellNest_Name"].tolist()

            # Specific well nest of interest
            if label[0] in wellnestlist:

                # Saving data
                xs.append(x)
                ys.append(y)
                labels.append(label[0])

            # If well nest irrelevant for this paper
            else:
                continue

    # Printing average subsidence rmse (cm/yr)
    # Initializing figure
    fig, ax = plt.subplots(figsize=(3.2, 2.2), dpi=300)
    datalim = None
    map = Basemap(llcrnrlon=100.3, llcrnrlat=13.4, urcrnrlon=100.8, urcrnrlat=14,
                  resolution="h", ellps="WGS84", lat_0=13.6, lon_0=100.4)
    draw_basemap(map, xs, ys, labels=labels, fig=fig, ax=ax,
                 datalim=datalim, mode="GW_WellNests", save=0,
                 figpath=path)

    # If saving figure
    if save == 1:

        fig_name1 = "Map_GWLocs.eps"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="eps")

        fig_name1 = "Map_GWLocs.png"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="png")


def sub_rmse_map(path, wellnestlist, all_results,
                 sub_total, subv_total,
                 annual_data, tmin=None, tmax=None, save=0):
    """Spatial mapping of simulated subsidence and observed.

    path - path to save figures
    wellnestlist - list of wellnests that were simualted
    all_results - lists of lists: wellnestname, well name, head matrix with
    head series of each node
    sub_total - lists of lists: wellnestname, well_name, total cum sub
    subv_total - lists of lists: wellnestname, well_name, inelastic cum sub
    annual_data - lists of lists: wellnestname, well_name, total cum sub for
    all four clay at a wellnest location
    save - if 1, save; if 0, don't save

    ASSUMES FOUR WELLS IN WELLNEST
    """
    # Importing spatial coordinates
    full_GWpath = os.path.join(os.path.abspath("inputs"),
                               "GroundwaterWellLocs.xls")
    gwwell_locs = pd.read_excel(full_GWpath)

    # Locations of wellnests; removing duplicates
    gwwell_locs = gwwell_locs.drop_duplicates("WellNest_Name", keep="first")

    # BAR PLOT preparation
    daterange = pd.date_range(dt.datetime(1978, 12, 31), periods=43,
                              freq="Y").tolist()
    df = pd.DataFrame(daterange, columns=["date"])

    # Saving relevant xs, ys, and cumsum
    xs = []
    ys = []
    cs_rmse = []
    cs_perc = []

    # For each wellnest in list
    # num_well is the index, wellnest = name
    # Figures for each well nest
    for num_well, wellnest in enumerate(wellnestlist):

        # Benchmark
        loc = os.path.join(os.path.abspath("inputs"), "SurveyingLevels.xlsx")
        subdata = pd.read_excel(loc, sheet_name=wellnest + "_Leveling",
                                index_col=3)
        subdata = pd.DataFrame(subdata)
        subdata.index = pd.to_datetime(subdata.index)

        # Getting rid of benchmarks outside time period
        subdata = subdata[(subdata.Year <= 2020)]

        # Benchmarks should start at 0 at the first year.
        bench = subdata.loc[:, subdata.columns.str.contains("Land")]
        bench = bench.fillna(0)

        if (bench.iloc[0] != 0).any():
            bench.iloc[0] = 0

        # IMPORTANT INFO
        # For benchmark measurements, the first year is 0, the second year is
        # the compaction rate over that first year.
        # For implicit Calc, the first year has a compaction rate over that
        # year, so to shift benchmarks value to the previouse year to match
        # Index has the right years
        bench.index = bench.index.shift(-1, freq="D")
        bench["date"] = bench.index

        # Gets the last date of each year
        lastdate = bench.groupby(pd.DatetimeIndex(bench["date"]).year,
                                 as_index=False).agg(
                                     {"date": max}).reset_index(drop=True)
        bench = bench.loc[lastdate.date]
        # preparation
        daterange = pd.date_range(dt.datetime(1978, 12, 31), periods=43,
                                  freq="Y").tolist()
        df = pd.DataFrame(daterange, columns=["date"])

        # annual data in cm
        plot_data = df.merge(annual_data[num_well][1]*100, left_on=df.date,
                             right_on=annual_data[num_well][1].index,
                             how="left")
        # Renaming for second merge
        plot_data = plot_data.rename(columns={"key_0": "key0"})

        # Filling na with 0
        plot_data = plot_data.fillna(0)

        # Benchamrks already in cm
        plot_data = plot_data.merge(bench, left_on=plot_data.key0,
                                    right_on=bench.index,
                                    how="left")
        # Renaming for other merge
        plot_data = plot_data.rename(columns={"key_0": "key1"})

        # Filling na with 0
        plot_data = plot_data.fillna(0)

        plot_data = plot_data.dropna()

        rms = mean_squared_error(plot_data[
                                 plot_data.columns[
                                     plot_data.columns.str.contains(
                                         "Land")].item()],
                                 plot_data.AnnRates, squared=False)

        cs_rmse.append(rms)
        cs_perc.append(rms/(plot_data[
            plot_data.columns[
                plot_data.columns.str.contains(
                    "Land")].item()].max() -
            plot_data[
                plot_data.columns[
                    plot_data.columns.str.contains(
                        "Land")].item()].min()))
        x_ = gwwell_locs.Long[gwwell_locs.WellNest_Name == wellnest].item()
        y_ = gwwell_locs.Lat[gwwell_locs.WellNest_Name == wellnest].item()
        xs.append(x_)
        ys.append(y_)

    # Printing average subsidence rmse (cm/yr)
    # Initializing figure
    fig, ax = plt.subplots(figsize=(3.2, 2.2), dpi=300)
    datalim = None
    map = Basemap(llcrnrlon=100.3, llcrnrlat=13.4, urcrnrlon=100.8, urcrnrlat=14,
                  resolution="h", ellps="WGS84", lat_0=13.6, lon_0=100.4)
    draw_basemap(map, xs, ys, cs_rmse, fig=fig, ax=ax,
                 datalim=datalim, mode="Sub_RMSE", save=0,
                 time_min=tmin, time_max=tmax, figpath=path)
    print("Avg: " + str("%.2f" % np.average(cs_rmse)) + " cm/yr")
    print("Max: " + str("%.2f" % max(cs_rmse)) + " cm/yr")

    # If saving figure
    if save == 1:

        fig_name1 = "Map_Sub_RMSE_" + tmin + "_" + tmax + "_50_2020.eps"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="eps")

        fig_name1 = "Map_Sub_RMSE_" + tmin + "_" + tmax + "_50_2020.png"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="png")

    # Printing average subsidence rmse relative to subsidence rate range (%)
    # Initializing figure
    fig, ax = plt.subplots(figsize=(3.2, 2.2), dpi=300)
    datalim = None
    map = Basemap(llcrnrlon=100.3, llcrnrlat=13.4, urcrnrlon=100.8, urcrnrlat=14,
                  resolution="h", ellps="WGS84", lat_0=13.6, lon_0=100.4)
    draw_basemap(map, xs, ys, np.multiply(cs_perc, 100), fig=fig, ax=ax,
                 datalim=datalim, mode="Sub_RMSE%", save=0,
                 time_min=tmin, time_max=tmax, figpath=path)

    # If saving figure
    if save == 1:

        fig_name1 = "Map_Sub_RMSE%_" + tmin + "_" + tmax + "_50_2020.eps"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="eps")

        fig_name1 = "Map_Sub_RMSE%_" + tmin + "_" + tmax + "_50_2020.png"
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="png")


def sub_sens_line(path, wellnestlist, all_results,
                  sub_total, subv_total,
                  annual_data, tmin=None, tmax=None, mode=None, num=None,
                  save=0):
    """Sensitivity analysis on subsidence based on either Sskv, Sske, K, thickness.

    path - path to save figures
    wellnestlist - list of wellnests that were simualted
    all_results - lists of lists: wellnestname, well name, head matrix with
    head series of each node
    sub_total - lists of lists: wellnestname, well_name, total cum sub
    subv_total - lists of lists: wellnestname, well_name, inelastic cum sub
    annual_data - lists of lists: wellnestname, well_name, total cum sub for
    all four clay at a wellnest location
    mode - which parameter is being adjusted for sensitivity (Sskv, Sske, K,
    thickness)
    num - number of parameter increases in sensitivity
    save - if 1, save; if 0, don't save

    ASSUMES FOUR WELLS IN WELLNEST
    """
    plt.figure(figsize=(6.75, 3.38), dpi=300)
    color1 = mcp.gen_color(cmap="rainbow", n=num)

    # Coeff for sensitivity percentage and plotting colors
    coeff = 50
    color_coeff = 1

    # Saving rates
    lastrates = []

    # For each sensitivity
    for i in range(num):

        # For each wellnest in list
        # num_well is the index, wellnest = name
        # Figures for each well nest
        for num_well, wellnest in enumerate(wellnestlist):

            plt.plot(annual_data[i][num_well][1].index,
                     annual_data[i][num_well][1].CumTotSum*-100,
                     label=str(coeff) + "%", linewidth=1,
                     color=color1[i])
            lastrate = (annual_data[i][num_well][1].CumTotSum[-1] -
                        annual_data[i][num_well][1].CumTotSum[-2])*-1000  # mm
            lastrates.append(lastrate)

        coeff += 10
        color_coeff -= .1

    plt.annotate("mm/yr",
                 xy=(370, 200),
                 xycoords="axes points",
                 color="k",
                 weight="bold")

    # Different positionings if elastic
    if mode == "Sske":

        plt.annotate("{:.1f}".format(lastrates[0]),
                     xy=(380, 180),
                     xycoords="axes points",
                     color=color1[0])

        plt.annotate("{:.1f}".format(lastrates[-1]),
                     xy=(380, 165),
                     xycoords="axes points",
                     color=color1[-1])
    else:
        plt.annotate("{:.1f}".format(lastrates[0]),
                     xy=(380, 165),
                     xycoords="axes points",
                     color=color1[0])

        plt.annotate("{:.1f}".format(lastrates[-1]),
                     xy=(380, 180),
                     xycoords="axes points",
                     color=color1[-1])

    # Plotting settings
    plt.legend()
    plt.ylabel("Cumulative Subsidence (cm)")
    plt.xlabel("Years")

    # Title and figure name changes based on mode
    # Inelastic specific storage
    if mode == "Sskv":

        plt.title("Inelastic Specific Storage\nSensitivity Analysis")

        fig_name = wellnest + "_CumSubTotal_SENS_" + \
            mode + ".eps"

    # Elastic specific storage
    elif mode == "Sske":

        plt.title("Elastic Specific Storage\nSensitivity Analysis")

        fig_name = wellnest + "_CumSubTotal_SENS_" + \
            mode + ".eps"

    # Vertical hydraulic conductivity
    elif mode == "K":

        plt.title("Vertical Hydraulic Conductivity\nSensitivity Analysis")

        fig_name = wellnest + "_CumSubTotal_SENS_" + \
            mode + ".eps"

    # Thickness
    elif mode == "thick":

        plt.title("Thickness Sensitivity Analysis")

        fig_name = wellnest + "_CumSubTotal_SENS_" + \
            mode + ".eps"

    # If saving figure
    if save == 1:

        full_figpath = os.path.join(path, fig_name)
        plt.savefig(full_figpath, dpi=300, format="eps")


def sub_forecast(path, wellnestlist, all_ann_subs, save=0):
    """Forecasts of subsidence based on five pumping scenarios.

    1. 500,000 m3/day
    2. 250,000 m3/day
    3. Delayed 250,000 m3/day
    4. 1,000,000 m3/day
    5. No pumping

    path - path to save figures
    wellnestlist - list of wellnests that were simualted
    all_ann_subs - lists of lists: wellnestname, dataframe with annual subsidence
    rates
    save - if 1, save; if 0, don't save

    ASSUMES FOUR WELLS IN WELLNEST
    """
    # Plotting settings
    plt.rc("font", size=5)  # controls default text size
    plt.rc("axes", titlesize=6)  # fontsize of the title
    plt.rc("axes", labelsize=6)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=6)  # fontsize of the x tick labels
    plt.rc("ytick", labelsize=6)  # fontsize of the y tick labels
    plt.rc("legend", fontsize=6)  # fontsize of the legend

    # Saving each scenario last annual rate
    ann_2060_500 = []
    ann_2060_250 = []
    ann_2060_d250 = []
    ann_2060_1000 = []
    ann_2060_0 = []

    # For each well nest
    for num_well, wellnest in enumerate(wellnestlist):

        # Figure plotting model results forecast for each scenario
        fig, ax = plt.subplots(figsize=(3.2, 2.2), dpi=300)

        # -1000 is to convert to mm and negative because subsidence is positive
        # while uplift is negative
        # 500,000 m3/day scenario
        plt.plot(all_ann_subs[0][num_well][1].index,
                 all_ann_subs[0][num_well][1].CumTotSum*-100,
                 label="500,000 m$^3$/day", linewidth=1.5,
                 color="hotpink")
        lastrate = (all_ann_subs[0][num_well][1].CumTotSum[-1] -
                    all_ann_subs[0][num_well][1].CumTotSum[-2])*-1000  # mm
        ann_2060_500.append(lastrate)
        ax.annotate("mm/yr",
                    xy=(180, 120),
                    xycoords="axes points",
                    color="k",
                    weight="bold")
        ax.annotate("{:.1f}".format(lastrate),
                    xy=(185, 105),
                    xycoords="axes points",
                    color="hotpink")

        # 250,000 m3/day scenario
        plt.plot(all_ann_subs[1][num_well][1].index,
                 all_ann_subs[1][num_well][1].CumTotSum*-100,
                 label="250,000 m$^3$/day", linewidth=1.5,
                 color="tab:orange")
        lastrate = (all_ann_subs[1][num_well][1].CumTotSum[-1] -
                    all_ann_subs[1][num_well][1].CumTotSum[-2])*-1000   # mm
        ann_2060_250.append(lastrate)
        ax.annotate("{:.1f}".format(lastrate),
                    xy=(185, 95),
                    xycoords="axes points",
                    color="tab:orange")

        # 500,000 -> 250,000 m3/day scenario
        plt.plot(all_ann_subs[3][num_well][1].index,
                 all_ann_subs[3][num_well][1].CumTotSum*-100,
                 label="Delayed\n250,000 m$^3$/day", linewidth=1.5,
                 color="tab:green")
        lastrate = (all_ann_subs[3][num_well][1].CumTotSum[-1] -
                    all_ann_subs[3][num_well][1].CumTotSum[-2])*-1000  # mm
        ann_2060_d250.append(lastrate)
        ax.annotate("{:.1f}".format(lastrate),
                    xy=(185, 100),
                    xycoords="axes points",
                    color="tab:green")

        # 1,000,000 m3/day scenario
        plt.plot(all_ann_subs[2][num_well][1].index,
                 all_ann_subs[2][num_well][1].CumTotSum*-100,
                 label="1,000,000 m$^3$/day", linewidth=1.5,
                 color="tab:red")
        lastrate = (all_ann_subs[2][num_well][1].CumTotSum[-1] -
                    all_ann_subs[2][num_well][1].CumTotSum[-2])*-1000  # mm
        ann_2060_1000.append(lastrate)
        ax.annotate("{:.1f}".format(lastrate),
                    xy=(185, 110),
                    xycoords="axes points",
                    color="tab:red")

        # No pumping scenario
        plt.plot(all_ann_subs[4][num_well][1].index,
                 all_ann_subs[4][num_well][1].CumTotSum*-100,
                 label="No Pumping", linewidth=1.5,
                 color="tab:purple")
        lastrate = (all_ann_subs[4][num_well][1].CumTotSum[-1] -
                    all_ann_subs[4][num_well][1].CumTotSum[-2])*-1000  # mm
        ann_2060_0.append(lastrate)
        ax.annotate("{:.1f}".format(lastrate),
                    xy=(185, 90),
                    xycoords="axes points",
                    color="tab:purple")

        # Observed pumping
        plt.plot(all_ann_subs[4][num_well][1].index[:44],
                 all_ann_subs[4][num_well][1].CumTotSum.iloc[:44]*-100,  # mm
                 color="black", linewidth=1.5,
                 label="Observed Pumping")
        plt.legend()

        # Plotting settings
        plt.ylabel("Cumulative Subsidence (cm)")
        plt.xlabel("Years")
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        plt.grid(True, linestyle=(0, (1, 10)), which="minor")
        plt.grid(True, linestyle="dashed", which="major")

        # Annotating specific points
        index_1990 = all_ann_subs[4][num_well][1].year == 1990
        index_2000 = all_ann_subs[4][num_well][1].year == 2000
        cum_value_1990 = all_ann_subs[4][num_well][1].CumTotSum[index_1990]*-100
        cum_value_2000 = all_ann_subs[4][num_well][1].CumTotSum[index_2000]*-100
        ann_value_1990 = all_ann_subs[4][num_well][1].AnnRates[index_1990]*-1000
        ann_value_2000 = all_ann_subs[4][num_well][1].AnnRates[index_2000]*-1000
        plt.scatter(cum_value_1990.index, cum_value_1990[0], color="cyan")
        plt.scatter(cum_value_2000.index, cum_value_2000[0], color="cyan")
        # annotation
        plt.text(cum_value_1990.index, cum_value_1990[0] - 4, "1990: " +
                 f"{ann_value_2000[0]:.1f}" + " mm/yr")
        # annotation
        plt.text(cum_value_2000.index, cum_value_2000[0] - 4, "2000: " +
                 f"{ann_value_1990[0]:.1f}" + " mm/yr")
        plt.show()

        # Saving figure
        if save == 1:
            fig_name = wellnest + "_CumSubForecast_ALLPUMP.eps"
            full_figpath = os.path.join(path, fig_name)
            plt.savefig(full_figpath, bbox_inches="tight",
                        format="eps")

    # Printing statistics
    print("\n500,000 scenario min, avg, max, med: " +
          f"{min(ann_2060_500):.4f}" + ", " +
          f"{np.average(ann_2060_500):.4f}" + ", " +
          f"{max(ann_2060_500):.4f}" + ", " +
          f"{median(ann_2060_500):.4f}")

    print("\n250,000 scenario min, avg, max, med: " +
          f"{min(ann_2060_250):.4f}" + ", " +
          f"{np.average(ann_2060_250):.4f}" + ", " +
          f"{max(ann_2060_250):.4f}" + ", " +
          f"{median(ann_2060_250):.4f}")

    print("\nDelayed250,000 scenario min, avg, max, med: " +
          f"{min(ann_2060_d250):.4f}" + ", " +
          f"{np.average(ann_2060_d250):.4f}" + ", " +
          f"{max(ann_2060_d250):.4f}" + ", " +
          f"{median(ann_2060_d250):.4f}")

    print("\n1,000,000 scenario min, avg, max, med: " +
          f"{min(ann_2060_1000):.4f}" + ", " +
          f"{np.average(ann_2060_1000):.4f}" + ", " +
          f"{max(ann_2060_1000):.4f}" + ", " +
          f"{median(ann_2060_1000):.4f}")

    print("\nNo pumping scenario min, avg, max, med: " +
          f"{min(ann_2060_0):.4f}" + ", " +
          f"{np.average(ann_2060_0):.4f}" + ", " +
          f"{max(ann_2060_0):.4f}" + ", " +
          f"{median(ann_2060_0):.4f}")


def draw_basemap(map, xs, ys, cs=None, fig=None, ax=None,
                 datalim=None, mode=None, save=0, aq=None, labels=None,
                 perc=None, time_min=None, time_max=None, figpath=None, crit=None):
    """Drawing basemap for BKK.

    mode - Mode can be RMSE_full (Pastas), step_full (Pastas t90)
    sub_RMSE (subsidence RMSE), sub_forecast (subsidence forecast)
    Map contains the basemap
    xs - x locations (longitude) in list
    ys - y locations (latitude) in list
    cs - data to plot in list
    labels - list of names for labelling purposes
    datalim - datalimits
    fig - figure object
    ax - axis object
    aq - specific aquifer
    perc - percentage of rmse for example to put into title
    time_min - time minimum as string
    time_max - time maximum as string
    fig_path - figure to save path
    """
    # Plotting map
    # Land as green and ocean as blue
    # Drawing coastline
    map.drawcoastlines(zorder=2, linewidth=1)
    map.drawmapboundary(fill_color="#c1d4ec")
    # Continents
    map.fillcontinents(color="#4d9c83")

    # Adding Thailand province boundaries
    map.readshapefile(os.path.join(os.path.abspath("inputs\\GIS"), "provinces"),
                      name="provinces", drawbounds=True, zorder=1, linewidth=.5)

    # Drawing rivers
    map.drawrivers(color="teal", linewidth=1)

    # draw parallels and meridians
    map.drawparallels(np.arange(12.5, 14, .5), labels=[1, 0, 0, 0],
                      fontsize=6)
    map.drawmeridians(np.arange(99.5, 101.5, .25), labels=[0, 0, 0, 1],
                      fontsize=6)

    # Drawing Pastas/subsidence datapoints
    x, y = map(xs, ys)

    # FOR WEDGES: 0 is at 3 pm, 90 is at noon
    # RMSE mode for all wells and all well nests
    # wells as wedges
    if mode == "RMSE_full":

        # Angle of wedges
        theta1 = 90
        theta2 = 180
        r = .018  # radius

        # Patches
        patches = []

        # All cs's
        cs_all = []

        # For each well
        for item in cs.items():

            # For each location
            for j in range(len(item[1].x)):

                # Creating wedge
                wedge = Wedge((item[1].x[j], item[1].y[j]),
                              r, theta1, theta2)
                patches.append(wedge)

            # Saving cs's
            cs_all.extend(item[1].cs)

            # Updating theta
            theta1 -= 90
            theta2 -= 90

        # Adding collection
        p = PatchCollection(patches, zorder=10,
                            edgecolor="k",
                            linewidth=.5)
        p.set_array(cs_all)  # Colorbar
        ax.add_collection(p)

        # Colorbar

        cb = fig.colorbar(p, ax=ax)
        cb.ax.tick_params(labelsize=6)
        cb.set_label("Normalized RMSE", fontsize=7)
        plt.set_cmap("coolwarm")
        cb.mappable.set_clim(vmin=datalim[0],
                             vmax=datalim[1])
        cb.solids.set_rasterized(False)

        # Legend objects
        class WedgeObject(object):
            pass

        class WedgeObjectHandler(object):

            def legend_artist(self, legend, orig_handle, fontsize, handlebox):
                x0, y0 = handlebox.xdescent, handlebox.ydescent
                width, height = handlebox.width, handlebox.height
                hw = x0+.45*width
                hh = y0+.5*height
                r2 = 5
                colors = ["#42BCFF", "#FF8300", "#D30808", "#009914"]
                lgd_patches = [Wedge((hw, hh), r2, 90, 180, color=colors[0],
                                     label="BK"),
                               Wedge((hw, hh), r2, 0, 90, color=colors[1],
                                     label="PD"),
                               Wedge((hw, hh), r2, 180, 270, color=colors[2],
                                     label="NB"),
                               Wedge((hw, hh), r2, 270, 360, color=colors[3],
                                     label="NL")]

                lgd_elements = PatchCollection(lgd_patches,
                                               match_original=True,
                                               edgecolor="k",
                                               linewidth=.5)

                handlebox.add_artist(lgd_elements)
                plt.legend()
                return lgd_elements

        plt.legend([WedgeObject()], ["BK PD\nNB NL"],
                   handler_map={WedgeObject: WedgeObjectHandler()},
                   fontsize=5)

        # Title
        avgRMSE = pd.concat([cs["NB"].cs, cs["NL"].cs, cs["PD"].cs,
                             cs["BK"].cs], ignore_index=True)
        print(str("%.2f" % np.average(cs["NB"].cs)) + "NB")
        print(str("%.2f" % np.average(cs["NL"].cs)) + "NL")
        print(str("%.2f" % np.average(cs["PD"].cs)) + "PD")
        print(str("%.2f" % np.average(cs["BK"].cs)) + "BK")
        print("NormRMSE: " + str("%.2f" % np.average(avgRMSE)) + "%")

    # t90 mode for all wells and all well nests
    # wells as wedges
    elif mode == "step_full":

        # Angle of wedges
        theta1 = 90
        theta2 = 180
        r = .018  # radius

        # Patches
        patches = []

        # All cs's
        cs_all = []

        # For each well
        for item in cs.items():

            # For each location
            for j in range(len(item[1].x)):

                # Creating wedge
                wedge = Wedge((item[1].x[j], item[1].y[j]),
                              r, theta1, theta2)
                patches.append(wedge)

            # Saving cs's
            cs_all.extend(item[1].cs)

            # Updating theta
            theta1 -= 90
            theta2 -= 90

        # Adding collection
        p = PatchCollection(patches, zorder=10,
                            edgecolor="k",
                            linewidth=.5)
        p.set_array(cs_all)  # Colorbar
        ax.add_collection(p)

        # Colorbar
        cb = fig.colorbar(p, ax=ax)
        cb.ax.tick_params(labelsize=6)
        cb.set_label("Years", fontsize=7)
        cb.mappable.set_clim(vmin=datalim[0],
                             vmax=datalim[1])
        plt.set_cmap("plasma")
        cb.solids.set_rasterized(False)

        class Wedge_obj(object):
            pass

        class WedgeHandler(object):

            def legend_artist(self, legend, orig_handle, fontsize, handlebox):
                x0, y0 = handlebox.xdescent, handlebox.ydescent
                width, height = handlebox.width, handlebox.height
                hw = x0+.45*width
                hh = y0+.5*height
                r2 = 5
                colors = ["#42BCFF", "#FF8300", "#D30808", "#009914"]
                lgd_patches = [Wedge((hw, hh), r2, 90, 180, color=colors[0],
                                     label="BK"),
                               Wedge((hw, hh), r2, 0, 90, color=colors[1],
                                     label="PD"),
                               Wedge((hw, hh), r2, 180, 270, color=colors[2],
                                     label="NB"),
                               Wedge((hw, hh), r2, 270, 360, color=colors[3],
                                     label="NL")]

                lgd_elements = PatchCollection(lgd_patches,
                                               match_original=True,
                                               edgecolor="k",
                                               linewidth=.5)

                handlebox.add_artist(lgd_elements)

                return lgd_elements

        plt.legend([Wedge_obj()], ["BK PD\nNB NL"],
                   handler_map={Wedge_obj: WedgeHandler()},
                   fontsize=5)

    elif mode == "Sub_RMSE":

        map.scatter(x, y, s=50,
                    c=np.multiply(cs, 1), zorder=3,
                    marker="o", edgecolor="k",
                    cmap="RdYlBu_r", linewidth=.75)
        plt.clim(datalim)
        cb = plt.colorbar()
        cb.ax.tick_params(labelsize=6)
        cb.set_label("RMSE (cm/year)", fontsize=7)
        # plt.title("RMSE between \nSimulated and Observed Subsidence",
        #           {"fontname": "Arial"}, fontsize=8)
        cb.solids.set_rasterized(False)
        plt.show()

    # RMSE of subsidence simulation as a % of the total observation
    elif mode == "Sub_RMSE%":

        map.scatter(x, y, s=50,
                    c=np.multiply(cs, 1), zorder=3,
                    marker="o", edgecolor="k",
                    cmap="RdYlBu_r", linewidth=.75)
        plt.clim(datalim)
        cb = plt.colorbar()
        cb.ax.tick_params(labelsize=6)
        cb.set_label("Normalized RMSE", fontsize=7)
        cb.solids.set_rasterized(False)
        print("NormRMSE: " + str("%1.f" % np.average(cs)) + "%")

        plt.show()

    # Plotting GW well locations
    elif mode == "GW_WellNests":

        map.scatter(x, y, s=15,
                    zorder=3,
                    marker="o", edgecolor="k",
                    linewidth=.75, color="mediumorchid")

        for i, txt in enumerate(labels):

            if txt in ["LCBKK038", "LCBKK007", "LCBKK003", "LCBKK041",
                       "LCBKK005", "LCBKK021"]:
                ax.annotate(txt[2:], (x[i], y[i]), xycoords="data",
                            fontsize=3.5, color="w",
                            xytext=(-8, 1.5), textcoords="offset points",
                            weight="bold")
            else:
                ax.annotate(txt[2:], (x[i], y[i]), xycoords="data",
                            fontsize=3.5, color="w",
                            xytext=(-8, 3.5), textcoords="offset points",
                            weight="bold")

        plt.show()

    # Forecasting subsidence for all wells
    elif mode == 'Sub_Forecast_Map':

        # Angle of wedges
        theta1 = 90
        theta2 = 162
        r = .018  # radius

        # All cs's
        cs_all = []

        # Patches
        patches = []

        # For each pumping scenario
        for item in cs.items():

            # For each location/well nest
            for j in range(len(item[1].x)):

                # Creating wedge
                wedge = Wedge((item[1].x[j], item[1].y[j]),
                              r, theta1, theta2)
                patches.append(wedge)

            cs_all.extend(item[1].cs)

            # Updating theta
            theta1 -= 72
            theta2 -= 72

        # Adding collection
        p = PatchCollection(patches, zorder=10,
                            edgecolor="k",
                            linewidth=.5, match_original=True)
        p.set_array(cs_all)  # Colorbar
        ax.add_collection(p)

        # Colorbar
        cb = fig.colorbar(p, ax=ax)
        cb.ax.tick_params(labelsize=6)
        cb.set_label("Cumulative Subsidence (cm)", fontsize=7)
        plt.set_cmap("coolwarm")
        cb.mappable.set_clim(vmin=datalim[0],
                             vmax=datalim[1])
        cb.solids.set_rasterized(False)

        # Legend objects
        class WedgeObject(object):
            pass

        class WedgeObjectHandler(object):

            def legend_artist(self, legend, orig_handle, fontsize, handlebox):
                x0, y0 = handlebox.xdescent, handlebox.ydescent
                width, height = handlebox.width, handlebox.height
                hw = x0+.45*width
                hh = y0+.5*height
                r2 = 5
                colors = ["hotpink", "tab:orange", "tab:green", "tab:red",
                          "tab:purple"]
                lgd_patches = [Wedge((hw, hh), r2, 90, 162, color=colors[0],
                                     label="500,000"),
                               Wedge((hw, hh), r2, 18, 90, color=colors[1],
                                     label="250,000"),
                               Wedge((hw, hh), r2, 162, 234, color=colors[-1],
                                     label="No Pumping"),
                               Wedge((hw, hh), r2, 234, 306, color=colors[2],
                                     label="Delayed 250,000"),
                               Wedge((hw, hh), r2, 306, 18, color=colors[-2],
                                     label="1,000,000")]

                lgd_elements = PatchCollection(lgd_patches,
                                               match_original=True,
                                               edgecolor="k",
                                               linewidth=.5)

                handlebox.add_artist(lgd_elements)
                plt.legend()
                return lgd_elements

        plt.legend([WedgeObject()],
                   ["        500,000    250,000\nNo Pumping          1,000,000\n" +
                    "         Delayed 250,000"],
                   handler_map={WedgeObject: WedgeObjectHandler()},
                   fontsize=4, loc='lower left')

        plt.show()

        return

    # Annotating water bodies
    plt.annotate("Gulf of Thailand", xy=(.44, .05),
                 xycoords="axes fraction", fontsize=5)

    plt.show()

    # Saaving graphs
    if save == 1:
        fig_name1 = aq + "_" + mode + "_" + time_min + "_" + time_max + "_maps.eps"
        full_figpath = os.path.join(figpath, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches="tight", format="eps")


def sub_forecast_map(path, wellnestlist, all_ann_subs,
                     tmin=None, tmax=None, save=0):
    """Plot subsidence forecast maps that are in main paper.

    all_results - lists of lists: wellnestname, well name, head matrix with
    head series of each node
    all_ann_subs - list of list of list of subsidence results for each well nest
    for each pumping scenario
    [0] 500,000
    [1] 250,000
    [2] 1,000,000
    [3] delayed 250,000
    [4] no pumping
    tmin - time min
    tmax - time max
    save - if 1, save; if 0, don't save

    Assumes four wells in well nest
    """
    # Importing spatial coordinates
    GWpath = 'C:\\Users\\jtsoonthornran\\Downloads\\GW\\'
    full_GWpath = os.path.join(GWpath, 'GroundwaterWellLocs.xls')
    gwwell_locs = pd.read_excel(full_GWpath)

    # Locations of wellnests; removing duplicates
    gwwell_locs = gwwell_locs.drop_duplicates('WellNest_Name', keep='first')

    # Preallocation
    # Empty dictionary
    d_dict = {}

    # For each pumping scenario
    # num_scenario is the pumping scenario index,scen_res = pumping scenario result
    for num_scenario, scen_res in enumerate(all_ann_subs):

        # Preallocation
        # Saving relevant xs, ys, and cumsum
        xs = []
        ys = []
        cs = []

        # For each well nest
        for i in range(len(scen_res)):

            # Get cumulative sum of highest year below tmax
            max_year = scen_res[i][1].year[
                scen_res[i][1].year < int(tmax)].max()

            # Saving difference in cum sum between a time period
            # Cumulative sub in cm
            cs.append((scen_res[i][1].CumTotSum[
                scen_res[i][1].year == max_year].item() -
                scen_res[i][1].CumTotSum[
                    scen_res[i][1].year == int(tmin)].item()) * -100)

            x_ = gwwell_locs.Long[
                gwwell_locs.WellNest_Name == scen_res[i][0]].item()
            y_ = gwwell_locs.Lat[
                gwwell_locs.WellNest_Name == scen_res[i][0]].item()
            xs.append(x_)
            ys.append(y_)

        # Creates a dictionary with location and cum sub
        d_dict[num_scenario] = pd.DataFrame({"x": xs, "y": ys, "cs": cs})

    # Initializing figure
    fig, ax = plt.subplots(figsize=(3.2, 2.2), dpi=300)
    datalim = [-5, 35]
    map = Basemap(llcrnrlon=100.3, llcrnrlat=13.4, urcrnrlon=100.8, urcrnrlat=14,
                  resolution='h', ellps='WGS84', lat_0=13.6, lon_0=100.4)
    draw_basemap(map, xs, ys, d_dict, fig=fig, ax=ax,
                 datalim=datalim, mode='Sub_Forecast_Map', save=0,
                 time_min=tmin, time_max=tmax, figpath=path)

    # If saving figure
    if save == 1:

        fig_name1 = 'Map_CumSub_' + tmin + '_' + tmax + '_ALLPump.eps'
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches='tight', format='eps')

        fig_name1 = 'Map_CumSub_' + tmin + '_' + tmax + '_ALLPump.png'
        full_figpath = os.path.join(path, fig_name1)
        plt.savefig(full_figpath, dpi=300, bbox_inches='tight', format='png')


###############################################################################
# Plotting settings
###############################################################################

plt.rc("font", size=10)  # controls default text size
plt.rc("axes", titlesize=10)  # fontsize of the title
plt.rc("axes", labelsize=6)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=6)  # fontsize of the x tick labels
plt.rc("ytick", labelsize=6)  # fontsize of the y tick labels
plt.rc("legend", fontsize=6)  # fontsize of the legend


def Pastas_results(models, Wellnest_name, well_names,
                   time_mins, time_maxs, figpath):
    """Plot Pastas graphs that are in main paper.

    Wellnest_name - Name of well nest as a string
    well_names - list of name of wells in well nest
    models - listPastas models that was previously created
    time_mins - list of time minimum as string
    time_maxs - list of time maximum as string
    figpath - string path to save figure
    """
    # For each well in well names, determine order
    # Which well to start with because want BK, PD, NL, NB order
    order = [well_names.index(x) for y in ['BK', 'PD', 'NL', 'NB']
             for x in well_names if y in x]

    # Creating figure
    fig = plt.figure(figsize=(3.3, 3.3), dpi=300)

    # Adding subfigures
    gs = fig.add_gridspec(ncols=1, nrows=len(order)+1,
                          width_ratios=[.25])

    # Axes
    axes = []

    # For each well/model
    for idx, i in enumerate(order):

        # Current well
        model = models[i]
        time_min = min(time_mins)
        time_max = max(time_maxs)
        well_name = well_names[i]

        # Setting colors
        if "BK" in well_name:
            color = "blue"
        elif "PD" in well_name:
            color = "orange"
        elif "NL" in well_name:
            color = "green"
        elif "NB" in well_name:
            color = "red"

        # Obs, simulation, residuals, stress time series
        # Observation time series
        o = model.observations(tmin=time_min, tmax=time_max)
        o_nu = model.oseries.series.drop(o.index)
        o_nu = o_nu[time_min: time_max]

        # Simulation time series
        sim = model.simulate(tmin=time_min, tmax=time_max,
                             warmup=365*30, return_warmup=False)

        # Setting y limits
        ylims = [(min([sim.min(), o[time_min:time_max].min()]),
                  max([sim.max(), o[time_min:time_max].max()]))]

        # Frame
        if idx > 0:
            ax1 = fig.add_subplot(gs[idx], sharex=axes[0])
        else:
            ax1 = fig.add_subplot(gs[idx])
        axes.append(ax1)

        # First subplot
        # observation plot
        o.plot(ax=ax1, linestyle="-", marker=".",
               color="k", label="Observed",
               x_compat=True, markersize=1, linewidth=.5)
        if not o_nu.empty:
            # plot parts of the oseries that are not used in grey
            o_nu.plot(ax=ax1, linestyle="-", marker=".", color="0.5",
                      label="", linewidth=.2,
                      x_compat=True, zorder=-1,
                      markersize=1)

        # add rsq to simulation
        rmse = model.stats.rmse(tmin=time_min, tmax=time_max)

        # Simulation plot
        sim.plot(ax=ax1, x_compat=True,
                 label=f"Simulated (RMSE = {rmse:.2} m)",
                 linewidth=1.5, color=color)

        # Plot 1 settings
        ax1.set_ylabel("Head\n(m)", labelpad=0)
        ax1.legend(loc=(0, 1), ncol=3, frameon=False, numpoints=3,
                   fontsize=5)
        ax1.set_ylim(ylims[0])
        ax1.tick_params(axis="both", which="major", pad=0)
        # ax1.set_title(well_name, fontsize=6)
        ax1.set(xlabel=None)
        ax1.xaxis.set_ticks_position('none')
        ax1.annotate(well_name,
                     xy=(-.1, 1), xycoords="axes fraction",
                     fontsize=6, horizontalalignment="center",
                     weight="bold",
                     bbox=dict(boxstyle="round", fc="0.8"),
                     verticalalignment="baseline")

        # Add a row for each stressmodel
        rmin = 0  # tmin of the response
        rmax = 0  # tmax of the response
        axb = None

        # plot the step response
        response = model._get_response(block_or_step="step",
                                       name="well", add_0=True) * 50

        rmax = max(rmax, response.index.max())

        # Inset graph settings
        left, bottom, width, height = [0.82, 0.3, 0.15, .4]
        axb = ax1.inset_axes([left, bottom, width, height])
        response.plot(ax=axb)
        title = "Step response"
        axb.tick_params(axis="both", which="major", pad=0)
        axb.set_xlabel("Days", fontsize=4, labelpad=-5)
        axb.set_ylabel("Head", fontsize=4, labelpad=-5)
        axb.xaxis.set_label_coords(.28, -.5)
        axb.yaxis.set_label_coords(-.48, .2)
        axb.set_title(title, fontsize=4, pad=0)
        axb.tick_params(labelsize=4)
        axb.set_xlim(rmin, rmax)

        # If last well
        if idx == len(order) - 1:

            ax0 = fig.add_subplot(gs[idx+1], sharex=ax1)
            # Stress time series
            stress = np.multiply(model.get_stress("well", tmin=time_min,
                                                  tmax=time_max),
                                 1 * 10**4)

            stress.plot(ax=ax0, linestyle="-", color="tab:purple",
                        label="Observed Pumping")

            # Plot 1 settings
            ax0.set_ylabel("Rate\n(m$^3$/day)", labelpad=0)
            ax0.set_xlabel("Year")
            ax0.legend(loc=(.1, 1), ncol=3, frameon=False,
                       fontsize=5)
            ax0.tick_params(axis="both", which="major", pad=0)
            ax0.set_ylim([2.5 * 10**5, 3 * 10**6])

            # xlim sets minorticks back after plots:
            ax0.minorticks_off()

            ax0.set_xlim(time_min, time_max)

            # Grids
            for ax in fig.axes:
                ax.grid(True)
            # No grids for inset graph
            axb.grid(False)

        if isinstance(fig, plt.Figure):
            fig.tight_layout(pad=0)  # Before making the table

        plt.subplots_adjust(right=0.95)

    # Fig name
    fig_name3 = Wellnest_name + "_GW_" + \
        time_min + "_" + time_max + "_PAPER.png"
    # Fig path
    full_figpath = os.path.join(figpath, fig_name3)
    # Save fig
    plt.savefig(full_figpath, dpi=300, bbox_inches="tight",
                format="png")

    # Fig name
    fig_name3 = Wellnest_name + "_GW_" + \
        time_min + "_" + time_max + "_PAPER.eps"
    # Fig path
    full_figpath = os.path.join(figpath, fig_name3)
    # Save fig
    plt.savefig(full_figpath, dpi=300, bbox_inches="tight",
                format="eps")