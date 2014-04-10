'''
Find pearson correlation between pairs of emotions, then show as a matrix of scatterplots.

TODO: 
Implement and display Hierarchical Clustering
Remove empty row
'''

import pymongo
import numpy as np
import scipy as sc
from math import fabs
from scipy.stats import pearsonr
from itertools import combinations
import pylab as P

from db import Database

PLOT_DIR = "../plots/"

def main():
    metrics = [q['metric'] for q in Database.db.questions.find()]
    emotion_vectors = dict([(metric, []) for metric in metrics])
    emotion_matrix = [[] for metric in metrics]

    for score_doc in Database.db.scores.find():
        for metric in metrics:
            metric_index = metrics.index(metric)
            score = score_doc['scores'][metric]
            emotion_vectors[metric].append(score)
            emotion_matrix[metric_index].append(score)

    correlations = []
    correlations_dict = {}
    for e1, e2 in combinations(metrics, 2):
        coeff, pval = pearsonr(emotion_vectors[e1], emotion_vectors[e2])
        correlations.append(coeff)
        correlations_dict[coeff] = (e1, e2)

    print min(correlations), max(correlations), np.mean(correlations)
    print correlations_dict[min(correlations)]
    print correlations_dict[max(correlations)]


    R = np.corrcoef(emotion_matrix)

    max_domain = max(fabs(min(correlations)), fabs(max(correlations)))
    # For colormaps see: http://wiki.scipy.org/Cookbook/Matplotlib/Show_colormaps

    # Generate the Plot

    P.pcolor(R, cmap='RdBu')
    P..tick_top()
    P.gca().invert_yaxis()
    P.colorbar()
    P.clim(min(correlations), max(correlations))
    P.xticks(np.arange(0.5, 17.5), [m.capitalize() for m in metrics], rotation=90)
    P.yticks(np.arange(0.5, 17.5), [m.capitalize() for m in metrics])
    P.title('Correlation of Emotions')
    P.savefig(PLOT_DIR + 'correlation_of_emotions.svg', format='svg', bbox_inches='tight')

if __name__ == '__main__':
    main()