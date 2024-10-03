import matplotlib.pyplot as plt
import matplotlib as mpl

plt.rcParams.update({
    "text.usetex": True,
    # "font.family": "Helvetica",
    # "font.serif": "Helvetica",
    # "font.sans-serif": "Helvetica",
})

COLORS = [
    "#833",
    "#b55",
    "#55b",
    "#383",
]

COLORS_GRAY = [
    "#999",
    "#444",
    "#bbb",
]

mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=COLORS) 