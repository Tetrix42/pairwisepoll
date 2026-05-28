import random
import numpy as np
import openskill
from openskill.models import PlackettLuce



# Import openskill.py and plotting libraries.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

def plot_black(result, location):
	visualization_data = np.arange(-25, 75, 0.01)
	plt.style.use("dark_background")
	fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
	fig.patch.set_facecolor("#1E1E1E")
	ax.set_facecolor("#2E2E2E")


	# DataFrame Code
	df = pd.DataFrame([_.__dict__ for _ in result])
	df["ordinal"] = [_.ordinal() for _ in result]
	df


	df.apply(
		lambda row: ax.plot(
			visualization_data,
			norm.pdf(visualization_data, row["mu"], row["sigma"]),
			label=f"μ: {row['mu']:.2f}, σ: {row['sigma']:.2f}",
			linewidth=2,
		),
		axis=1,
	)


	ax.set_title("Normal Distributions", fontsize=20, color="white", fontweight="bold")
	ax.set_xlabel("X", fontsize=14, color="white")
	ax.set_ylabel("Probability Density", fontsize=14, color="white")
	ax.tick_params(colors="white", which="both")
	ax.grid(True, linestyle="--", alpha=0.3)

	legend = ax.legend(title="Parameters", title_fontsize=14, fontsize=12)
	legend.get_frame().set_facecolor("#3E3E3E")
	legend.get_frame().set_edgecolor("white")
	plt.setp(legend.get_texts(), color="white")
	plt.setp(legend.get_title(), color="white")
	#plt.tight_layout()
	plt.savefig(location)
	plt.close()






def plot(result, location):
	visualization_data = np.arange(-25, 75, 0.01)
#	plt.style.use("dark_background")
	fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
#	fig.patch.set_facecolor("#1E1E1E")
#	ax.set_facecolor("#2E2E2E")


	# DataFrame Code
	df = pd.DataFrame([_.__dict__ for _ in result])
	df["ordinal"] = [_.ordinal() for _ in result]
	df


	df.apply(
		lambda row: ax.plot(
			visualization_data,
			norm.pdf(visualization_data, row["mu"], row["sigma"]),
			label=f"μ: {row['mu']:.2f}, σ: {row['sigma']:.2f}",
			linewidth=2,
		),
		axis=1,
	)


	ax.set_title("Normal Distributions", fontsize=20, fontweight="bold")
	ax.set_xlabel("X", fontsize=14)
	ax.set_ylabel("Probability Density", fontsize=14 )
	ax.tick_params(which="both")
	ax.grid(True, linestyle="--", alpha=0.3)

	legend = ax.legend(title="Parameters", title_fontsize=14, fontsize=12)
#	legend.get_frame().set_facecolor("#3E3E3E")
#	legend.get_frame().set_edgecolor("white")
#	plt.setp(legend.get_texts(), color="white")
#	plt.setp(legend.get_title(), color="white")
	#plt.tight_layout()
	plt.savefig(location)
	plt.close()




def calc_skill_obj(obj):
    #print("calc elo")
    teams = {}
    rows = obj

    #print(rows)
    #random.shuffle(rows)

    #import matplotlib.pyplot as plt

    model = openskill.models.PlackettLuce()
    for row in rows:
        if(len(row) < 4):
            continue
        na = row[0]
        nb = row[3]
        pa = row[1]
        pb = row[2]
        if na not in teams:
            teams[na] = model.rating(name=na)
            #xy[na] = {'x' : [], 'y' : []}
        if nb not in teams:
            teams[nb] = model.rating(name=nb)
            #xy[nb] = {'x' : [], 'y' : []}

        ta = teams[na]
        tb = teams[nb]
        #print(ta, tb)

        [ta2, tb2] = model.rate([[ta], [tb]], scores=[pa, pb])
        print(ta2, tb2)
    rank = []
    for n in teams:
        print(n, teams[n].ordinal(), teams[n])
        rank.append(teams[n])

    rank.sort()
    rank.reverse()

    return rank


