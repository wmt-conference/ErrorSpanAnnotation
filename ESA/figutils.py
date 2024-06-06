raise Exception("This code uses old loader, please refactor.")
COLORS = [
    "#bc272d",  # red
    "#3a5",  # green
    "#0000a2",  # blue
    "#e9c716",  # yellow
]


def matplotlib_default():
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=COLORS)
    mpl.rcParams["legend.fancybox"] = False
    mpl.rcParams["legend.edgecolor"] = "None"
    mpl.rcParams["legend.fontsize"] = 9
    mpl.rcParams["legend.borderpad"] = 0.1
    mpl.rcParams["legend.labelspacing"] = 0.2