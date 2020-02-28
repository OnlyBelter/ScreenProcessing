# Methods for plotting and analyzing screen data tables generated by process_experiments.py
# source: https://github.com/mhorlbeck/ScreenProcessing

from __future__ import print_function, division
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import numpy as np
import scipy as sp


plotDirectory = None  # set to a directory to save figures
imageExtension = 'png'
plotWithPylab = True  # call plt.show when figures are done
figureScale = 1

# Matplotlib settings
almost_black = '#111111'
dark2 = ['#1b9e77',
         '#d95f02',
         '#7570b3',
         '#e7298a',
         '#66a61e',
         '#e6ab02',
         '#a6761d',
         '#666666']
blue_yellow = matplotlib.colors.LinearSegmentedColormap.from_list('BuYl',[(0,'#ffff00'),(.49,'#000000'),(.51,'#000000'),(1,'#0000ff')])
blue_yellow.set_bad('#999999', 1)
yellow_blue = matplotlib.colors.LinearSegmentedColormap.from_list('YlBu',[(0,'#0000ff'),(.49,'#000000'),(.51,'#000000'),(1,'#ffff00')])
yellow_blue.set_bad('#999999', 1)

plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'Verdana','Bitstream Vera Sans']
plt.rcParams['font.size'] = 8
plt.rcParams['font.weight'] = 'regular'
plt.rcParams['text.color'] = almost_black

axisLineWidth = .5
plt.rcParams['axes.linewidth'] = axisLineWidth
plt.rcParams['lines.linewidth'] = 1.5

plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.edgecolor'] = almost_black
plt.rcParams['axes.labelcolor'] = almost_black
# plt.rcParams['axes.color_cycle'] = dark2_all

plt.rcParams['patch.edgecolor'] = 'none'
plt.rcParams['patch.linewidth'] = .25
# plt.rcParams['patch.facecolor'] = dark2_all[0]

plt.rcParams['savefig.dpi']=1000
plt.rcParams['savefig.format'] = 'svg'

plt.rcParams['legend.frameon'] = False
plt.rcParams['legend.handletextpad'] = .25
plt.rcParams['legend.fontsize'] = 8
plt.rcParams['legend.numpoints'] = 1
plt.rcParams['legend.scatterpoints'] = 1

plt.rcParams['ytick.direction'] = 'out'
plt.rcParams['ytick.color'] = almost_black
plt.rcParams['ytick.major.width'] = axisLineWidth
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['xtick.color'] = almost_black
plt.rcParams['xtick.major.width'] = axisLineWidth


def loadData(experimentName, collapsedToTranscripts = True,
             premergedCounts = False):
    dataDict = {'library': pd.read_csv(experimentName + '_librarytable.txt', sep='\t', header=0, index_col=0),
                'counts': pd.read_csv(experimentName + '_mergedcountstable.txt', sep='\t',
                                      header=range(2), index_col=range(1)),
                'phenotypes': pd.read_csv(experimentName + '_phenotypetable.txt', sep='\t',
                                          header=range(2), index_col=range(1))}
    
    if premergedCounts:
        dataDict['premerged counts'] = pd.read_csv(experimentName + '_rawcountstable.txt', sep='\t',
                                                   header=range(3), index_col=range(1))
    
    if collapsedToTranscripts:
        dataDict['transcript scores'] = pd.read_csv(experimentName + '_genetable.txt', sep='\t',
                                                    header=range(3), index_col=range(2))
        dataDict['gene scores'] = pd.read_csv(experimentName + '_genetable_collapsed.txt', sep='\t',
                                              header=range(3), index_col=range(1))
    else:
        dataDict['gene scores'] = pd.read_csv(experimentName + '_genetable.txt',
                                              sep='\t', header=range(3), index_col=range(1))
    
    return dataDict


def countsHistogram(data, condition=None, replicate=None):
    """
    read counts-level plotting functions
    :param data:
    :param condition:
    :param replicate:
    :return:
    """
    if not checkOptions(data, 'counts', (condition, replicate)):
        return
        
    fig, axis = plt.subplots(figsize=(3.5*figureScale, 2.5*figureScale))
    cleanAxes(axis)
    
    axis.semilogy()
    # logarithmetics after plus 1
    logCounts = np.log2(data['counts'].loc[:, (condition, replicate)].fillna(0) + 1)
    
    axis.hist(logCounts,
              bins=int(len(data['counts']) ** .3),  # set bin as 30% of the number of data
              histtype='step', color=almost_black, lw=1)
        
    ymax = axis.get_ylim()[1]
    axis.plot([np.median(logCounts)]*2, (0.8, ymax), color='#BFBFBF', lw=.5, alpha=.5)
    axis.text(np.median(logCounts)*.98, ymax * .90, 'median reads = {0:.0f}'.format(np.median(data['counts'].loc[:, (condition, replicate)].fillna(0))),
              horizontalalignment='right', verticalalignment='top', fontsize=6)
    
    axis.set_ylim((0.9, ymax)) 
    
    axis.set_xlabel('{0} {1} sgRNA read counts (log2)'.format(condition, replicate))
    axis.set_ylabel('Number of sgRNAs')
    
    plt.tight_layout()
    return displayFigure(fig, 'counts_hist')


def countsScatter(data, condition_x=None, replicate_x=None,
                  condition_y=None, replicate_y=None,
                  showAll=True, showNegatives=True, showGenes = [],
                  colorByPhenotype_condition=None, colorByPhenotype_replicate=None):
    """

    :param data:
    :param condition_x:
    :param replicate_x:
    :param condition_y:
    :param replicate_y:
    :param showAll: True/False
    :param showNegatives: True/False
    :param showGenes:
    :param colorByPhenotype_condition: gamma/tau/rho
    :param colorByPhenotype_replicate: replicate1/replicate2, same as replicate_x and replicate_y
    :return:
    """
                            
    if not checkOptions(data, 'counts', (condition_x, replicate_x)):
        return
    if not checkOptions(data, 'counts', (condition_y, replicate_y)):
        return
    if (colorByPhenotype_condition is not None) and (colorByPhenotype_replicate is not None) \
            and (not checkOptions(data, 'phenotypes', (colorByPhenotype_condition, colorByPhenotype_replicate))):
        return
        
    fig, axis = plt.subplots(figsize=(3*figureScale, 3*figureScale))
    cleanAxes(axis)
    
    if showAll:
        if (colorByPhenotype_condition is None) or (colorByPhenotype_replicate is None):
            axis.scatter(np.log2(data['counts'].loc[:, (condition_x, replicate_x)] + 1),
                         np.log2(data['counts'].loc[:, (condition_y, replicate_y)] + 1),
                         s=1.5, c=almost_black, label='all sgRNAs', rasterized=True)
        else:
            result = axis.scatter(np.log2(data['counts'].loc[:, (condition_x, replicate_x)] + 1),
                                  np.log2(data['counts'].loc[:, (condition_y, replicate_y)] + 1),
                                  c=data['phenotypes'].loc[:, (colorByPhenotype_condition, colorByPhenotype_replicate)],
                                  s=1.5, cmap=yellow_blue, label='all sgRNAs', rasterized=True)
            plt.colorbar(result)
    
    if showNegatives:
        axis.scatter(np.log2(data['counts'].loc[data['library']['gene'] == 'negative_control',
                                                (condition_x, replicate_x)] + 1),
                     np.log2(data['counts'].loc[data['library']['gene'] == 'negative_control',
                                                (condition_y, replicate_y)] + 1),
                     s=1.5, c='#BFBFBF', label='non-targeting sgRNAs', rasterized=True)
            
    if showGenes and len(showGenes) != 0:
        if isinstance(showGenes, str):
            showGenes = [showGenes]
            
        geneSet = set(data['library']['gene'])
        for i, gene in enumerate(showGenes):
            if gene not in geneSet:
                print('{0} not in dataset'.format(gene))
            else:
                axis.scatter(np.log2(data['counts'].loc[data['library']['gene'] == gene, (condition_x, replicate_x)] + 1), 
                    np.log2(data['counts'].loc[data['library']['gene'] == gene, (condition_y, replicate_y)] + 1), 
                    s=3, c=dark2[i], label=gene)
                    
    plt.legend(loc='best', fontsize=6, handletextpad=0.005)
    
    axis.set_xlim((-0.2, max(axis.get_xlim()[1], axis.get_ylim()[1])))
    axis.set_ylim((-0.2, max(axis.get_xlim()[1], axis.get_ylim()[1])))
    
    axis.set_xlabel('{0} {1} sgRNA read counts (log2)'.format(condition_x, replicate_x), fontsize=8)
    axis.set_ylabel('{0} {1} sgRNA read counts (log2)'.format(condition_y, replicate_y), fontsize=8)
    
    plt.tight_layout()
    return displayFigure(fig, 'counts_scatter')


def premergedCountsScatterMatrix(data, condition=None, replicate=None):
    if not checkOptions(data, 'counts', (condition, replicate)):
        return

    if 'premerged counts' not in data:
        print('Data must be loaded with premergedCounts = True')
        return
    # dataTable is a dataFrame
    dataTable = data['premerged counts'].loc[:, (condition, replicate)]
    dataColumns = dataTable.columns
    if len(dataColumns) == 1:
        print('Only one counts file for {0}, {1}; no scatter matrix will be generated'.format(condition, replicate))
        return

    fig, axes = plt.subplots(len(dataColumns), len(dataColumns), figsize=(len(dataColumns)*2.5,len(dataColumns)*2.5))

    for i, (name1, col1) in enumerate(dataTable.items()):
        name1 = '{0:.30}'.format(os.path.split(name1)[-1])
        for j, (name2, col2) in enumerate(dataTable.items()):
            name2 = '{0:.30}'.format(os.path.split(name2)[-1])
            if i < j:
                cleanAxes(axes[i,j], top=False, bottom=False, left=False, right=False)
                axes[i, j].xaxis.set_tick_params(top='off', bottom='off', labelbottom='off')
                axes[i, j].yaxis.set_tick_params(left='off', right='off', labelleft='off')
                
            elif i == j:
                axes[i, j].hist(np.log2(col2.dropna() + 1), bins=int(len(col2) ** .3), histtype='step', color=almost_black, lw=1)
            
                axes[i, j].set_xlabel(name2, fontsize=6)
                axes[i, j].set_ylabel('# sgRNAs', fontsize=6)

                axes[i, j].xaxis.set_tick_params(labelsize=6)
                axes[i, j].yaxis.set_tick_params(labelsize=6)
            else:
                axes[i, j].scatter(np.log2(col2.dropna() + 1),np.log2(col1.dropna() + 1), s=2, c=almost_black, rasterized=True)

                axes[i, j].set_xlabel(name2, fontsize=6)
                axes[i, j].set_ylabel(name1, fontsize=6)

                axes[i, j].xaxis.set_tick_params(labelsize=6)
                axes[i, j].yaxis.set_tick_params(labelsize=6)

    plt.tight_layout(pad=.05)
    return displayFigure(fig, 'premerged_counts_scatter')


# not yet implemented: counts vs phenotype
def phenotypeHistogram(data, phenotype=None, replicate=None):
    """
    phenotype-level plotting functions
    :param data:
    :param phenotype:
    :param replicate:
    :return:
    """
    if not checkOptions(data, 'phenotypes', (phenotype, replicate)):
        return
        
    fig, axis = plt.subplots(figsize=(3.5*figureScale,2.5*figureScale))
    cleanAxes(axis)
    
    axis.semilogy()
    
    axis.hist([data['phenotypes'].loc[:, (phenotype, replicate)].dropna(), 
               data['phenotypes'].loc[data['library']['gene'] == 'negative_control', (phenotype, replicate)].dropna()],
              bins=int(len(data['phenotypes']) ** .3),
              histtype='step', color=[almost_black, '#BFBFBF'], label=['all sgRNAs', 'non-targeting sgRNAs'], lw=1)
        
    plt.legend(fontsize=6, loc='upper left')
    
    axis.set_ylim((0.9, axis.get_ylim()[1])) 
    
    axis.set_xlabel('{0} {1} sgRNA phenotypes'.format(phenotype, replicate))
    axis.set_ylabel('Number of sgRNAs')
    
    plt.tight_layout()
    return displayFigure(fig, 'phenotype_hist')


def phenotypeScatter(data, phenotype_x = None, replicate_x = None,
                     phenotype_y = None, replicate_y = None,
                     showAll = True, showNegatives = True,
                     showGenes = [], showGeneSets = {}):
                            
    if not checkOptions(data, 'phenotypes', (phenotype_x,replicate_x)):
        return
    if not checkOptions(data, 'phenotypes', (phenotype_y,replicate_y)):
        return
        
    fig, axis = plt.subplots(figsize=(3*figureScale,3*figureScale))
    cleanAxes(axis)
    
    if showAll:
        axis.scatter(data['phenotypes'].loc[:, (phenotype_x, replicate_x)], 
            data['phenotypes'].loc[:, (phenotype_y, replicate_y)], 
            s=1.5, c=almost_black, label='all sgRNAs',
            rasterized=True)
    
    if showNegatives:
        axis.scatter(data['phenotypes'].loc[data['library']['gene'] == 'negative_control', (phenotype_x, replicate_x)], 
            data['phenotypes'].loc[data['library']['gene'] == 'negative_control', (phenotype_y, replicate_y)], 
            s=1.5, c='#BFBFBF', label='non-targeting sgRNAs',
            rasterized=True)
            
    i = 0
    if showGenes and len(showGenes) != 0:
        if isinstance(showGenes, str):
            showGenes = [showGenes]
            
        geneSet = set(data['library']['gene'])
        for i, gene in enumerate(showGenes):
            if gene not in geneSet:
                print('{0} not in dataset'.format(gene))
            else:
                axis.scatter(data['phenotypes'].loc[data['library']['gene'] == gene, (phenotype_x, replicate_x)], 
                    data['phenotypes'].loc[data['library']['gene'] == gene, (phenotype_y, replicate_y)], 
                    s=3, c=dark2[i], label=gene, rasterized=True)
                    
    if showGeneSets and len(showGeneSets) != 0:
        if not isinstance(showGeneSets, dict) or not \
            (isinstance(showGeneSets[showGeneSets.keys()[0]], set) or
             isinstance(showGeneSets[showGeneSets.keys()[0]], list)):
            print('Gene sets must be a dictionary of {set_name: [gene list/set]} pairs')
            
        else:
            for j, gs in enumerate(showGeneSets):
                sgsTargetingSet = data['library']['gene'].apply(lambda gene: gene in showGeneSets[gs])
                axis.scatter(data['phenotypes'].loc[sgsTargetingSet, (phenotype_x, replicate_x)], 
                    data['phenotypes'].loc[sgsTargetingSet, (phenotype_y, replicate_y)], 
                    s=3, c=dark2[i+j], label=gs, rasterized=True)
                    
    plotGrid(axis)
                    
    plt.legend(loc='best', fontsize=6, handletextpad=0.005)
    
    axis.set_xlabel('sgRNA {0} {1}'.format(phenotype_x, replicate_x), fontsize=8)
    axis.set_ylabel('sgRNA {0} {1}'.format(phenotype_y, replicate_y), fontsize=8)
    
    plt.tight_layout()
    return displayFigure(fig, 'phenotype_scatter')


def sgRNAsPassingFilterHist(data, phenotype, replicate, transcripts=False):
    if not checkOptions(data, 'phenotypes', (phenotype, replicate)):
        return
        
    fig, axis = plt.subplots(figsize=(3.5*figureScale, 2.5*figureScale))
    cleanAxes(axis)
    
    axis.semilogy()
    
    if transcripts:
        sgRNAsPerGene = data['phenotypes'].loc[data['library']['gene'] != 'negative_control',
                                               (phenotype, replicate)].groupby([data['library']['gene'],
                                                                                data['library']['transcripts']]).count()
    else:
        sgRNAsPerGene = data['phenotypes'].loc[data['library']['gene'] != 'negative_control',
                                               (phenotype, replicate)].groupby(data['library']['gene']).count()
    
    axis.hist(sgRNAsPerGene, bins=np.arange(min(sgRNAsPerGene), max(sgRNAsPerGene) + 1, 1),
              histtype='step', color=almost_black, lw=1)
    
    axis.set_ylim((0.9, axis.get_ylim()[1])) 
    
    axis.set_xlabel('{0} {1} sgRNAs passing filter per {2}'.format(phenotype, replicate, 'transcript' if transcripts else 'gene'))
    axis.set_ylabel('Number of sgRNAs')
    
    plt.tight_layout()
    return displayFigure(fig, 'sgRNAs_passing_filter_hist')
    

def volcanoPlot(data, phenotype=None, replicate=None, transcripts=False, showPseudo=True,
                effectSizeLabel=None, pvalueLabel=None, hitThreshold=7,
                labelHits = False, showGeneSets = {}, labelGeneSets = True):
    """
    gene-level plotting functions
    :param data:
    :param phenotype:
    :param replicate:
    :param transcripts:
    :param showPseudo:
    :param effectSizeLabel:
    :param pvalueLabel:
    :param hitThreshold:
    :param labelHits:
    :param showGeneSets:
    :param labelGeneSets:
    :return:
    """
    if not checkOptions(data, 'genes', (phenotype, replicate)):
        return

    if transcripts:
        table = data['transcript scores'][(phenotype, replicate)].copy()
        isPseudo = table.apply(lambda row: row.name[0][:6] == 'pseudo', axis=1)
    else:
        table = data['gene scores'][(phenotype, replicate)].copy()
        isPseudo = table.apply(lambda row: row.name[:6] == 'pseudo', axis=1)

    if effectSizeLabel is None:
        effectSizeLabel = getEffectSizeLabel(table)
        
        if effectSizeLabel is None:
            return
            
    if pvalueLabel is None:
        pvalueLabel = getPvalueLabel(table)
        
        if pvalueLabel is None:
            return

    discScore = lambda z, p: p * np.abs(z)

    pseudogeneScores = table[isPseudo]
    pseudoStd = np.std(pseudogeneScores[effectSizeLabel])
    table.loc[:, 'thresh'] = discScore(table[effectSizeLabel]/pseudoStd, -1*np.log10(table[pvalueLabel])) >= hitThreshold

    yGenes = -1*np.log10(table[pvalueLabel])
    xGenes = table[effectSizeLabel]

    fig, axis = plt.subplots(1, 1, figsize=(4*figureScale, 3.5*figureScale))
    cleanAxes(axis)

    axis.scatter(table.loc[isPseudo.ne(True)].loc[table['thresh'], effectSizeLabel],
                 -1*np.log10(table.loc[isPseudo.ne(True)].loc[table['thresh'], pvalueLabel].values),
                 s=4,
                 c='#7570b3',
                 label='Gene hit',
                 rasterized=True)

    axis.scatter(table.loc[isPseudo.ne(True)].loc[table['thresh'].ne(True), effectSizeLabel], -1*np.log10(table.loc[isPseudo.ne(True)].loc[table['thresh'].ne(True),pvalueLabel].values),
                 s=4,
                 c='#999999',
                 label = 'Gene non-hit', 
                 rasterized=True)
                 
    if labelHits:
        for gene, row in table.loc[isPseudo.ne(True)].loc[table['thresh']].iterrows():
            if transcripts:
                gene = ', '.join(gene)
                
            axis.text(row[effectSizeLabel], -1*np.log10(row[pvalueLabel]), gene, fontsize=6,
                      horizontalalignment='left' if row[effectSizeLabel] > 0 else 'right',
                      verticalalignment='center')

    if showPseudo:
        axis.scatter(table.loc[isPseudo.ne(False)].loc[table['thresh'],effectSizeLabel], -1*np.log10(table.loc[isPseudo.ne(False)].loc[table['thresh'],pvalueLabel].values),
                     s=4,
                     c='#d95f02', 
                     label='Negative control gene hit',
                     rasterized=True)

        axis.scatter(table.loc[isPseudo.ne(False)].loc[table['thresh'].ne(True),effectSizeLabel], -1*np.log10(table.loc[isPseudo.ne(False)].loc[table['thresh'].ne(True),pvalueLabel].values),
                     s=4,
                     c='#dadaeb', 
                     label='Negative control gene',
                     rasterized=True)

    if showGeneSets and len(showGeneSets) != 0:
        if not isinstance(showGeneSets, dict) or not \
               (isinstance(showGeneSets[showGeneSets.keys()[0]], set) or isinstance(showGeneSets[showGeneSets.keys()[0]], list)):
            print('Gene sets must be a dictionary of {set_name: [gene list/set]} pairs')
            
        else:
            for i, gs in enumerate(showGeneSets):
                sgsTargetingSet = data['library']['gene'].apply(lambda gene: gene in showGeneSets[gs])
                axis.scatter(table.loc[showGeneSets[gs], effectSizeLabel],
                             -1*np.log10(table.loc[showGeneSets[gs], pvalueLabel]), s=6, c=dark2[i], label=gs)
                    
                if labelGeneSets:
                    for gene, row in table.loc[showGeneSets[gs]].iterrows():
                        if transcripts:
                            gene = ', '.join(gene)
                
                        axis.text(row[effectSizeLabel], -1*np.log10(row[pvalueLabel]), gene, fontsize=6,
                                  horizontalalignment='left' if row[effectSizeLabel] > 0 else 'right', verticalalignment='center')

    plotGrid(axis, vert_origin=True, horiz_origin=False, unity=False)

    ymax = np.ceil(max(yGenes)) * 1.02
    xmin = min(xGenes) * 1.05
    xmax = max(xGenes) * 1.05
    
    axis.plot(np.linspace(xmin, xmax, 1000), np.abs(hitThreshold/np.linspace(xmin/pseudoStd,xmax/pseudoStd,1000)),'k--', lw=.5)

    axis.set_xlim((xmin, xmax))
    axis.set_ylim((0, ymax))

    axis.set_xlabel('{3} {0} {1} ({2})'.format(phenotype, replicate, effectSizeLabel, 'gene' if not transcripts else 'transcript'),fontsize=8)
    axis.set_ylabel('-log10 {0}'.format(pvalueLabel, fontsize=8))
    
    plt.legend(loc='best', fontsize=6, handletextpad=0.005)

    plt.tight_layout()
    return displayFigure(fig, 'volcano_plot')


def checkOptions(data, graphType, optionTuple):
    """
    utility functions, check if optionTuple is in the columns of data[graphType]
    :param data: a dict, each element is a dataFrame
    :param graphType: a string, counts or phenotypes or genes
    :param optionTuple: current sample_name and replicate, i.e. ('T0', 'Rep1')
    :return: True/False
    """
    if optionTuple[0] is None or optionTuple[1] is None:
        listOptions(data, graphType)
        return False
        
    if graphType == 'counts':
        colTups = set([colname[:2] for colname in data['counts'].columns.tolist()])
    elif graphType == 'phenotypes':
        colTups = set([colname[:2] for colname in data['phenotypes'].columns.tolist()])
    elif graphType == 'genes':
        colTups = set([colname[:2] for colname in data['gene scores'].columns.tolist()])
    else:
        print('Graph type not recognized')
        return False

    if optionTuple in colTups:
        return True
    else:
        print('{0} {1} not recognized'.format(optionTuple[0], optionTuple[1]))
        listOptions(data, graphType)
        return False


def listOptions(data, graphType):
    if graphType == 'counts':
        print('Condition and Replicate options are:')
        print('\n'.join(['{0:15}\t{1}'.format(colname[0], colname[1]) for colname, col in data['counts'].items()]))
        
    elif graphType == 'phenotypes':
        print('Phenotype and Replicate options are:')
        print('\n'.join(['{0:15}\t{1}'.format(colname[0], colname[1]) for colname, col in data['phenotypes'].items()]))
        
    elif graphType == 'genes':
        colTups = sorted(list(set([colname[:2] for colname, col in data['gene scores'].items()])))  # type: List[Any] # type: List[Any]
        print('Phenotype and Replicate options are:')
        print('\n'.join(['{0:15}\t{1}'.format(colname[0], colname[1]) for colname in colTups]))
        
    else:
        print('Graph type not recognized')


def getEffectSizeLabel(table):
    effectColLabels = [colname for colname, col in table.items() if colname[:7] == 'average']
    
    if len(effectColLabels) == 0:
        print('No gene effect size data columns found')
        return None
        
    elif len(effectColLabels) > 1:
        print('Multiple effect size data columns found, please specifiy one: ' + ', '.join(effectColLabels))
        return None
        
    else:
        return effectColLabels[0]


def getPvalueLabel(table):
    pvalColLabels = [colname for colname, col in table.items() if colname == 'Mann-Whitney p-value']

    if len(pvalColLabels) == 0:
        print('No p-value data columns found')
        return None

    elif len(pvalColLabels) > 1:
        print('Multiple p-value data columns found, please specifiy one: ' + ', '.join(effectColLabels))  # todo, what's this?
        return None

    else:
        return pvalColLabels[0]


def displayFigure(fig, savetitle=''):
    if plotWithPylab:
        plt.show(fig)
        
    if plotDirectory is not None:
        figNums = [int(fileName.split('_fig_')[0]) for fileName in os.listdir(plotDirectory)
                   if len(fileName.split('_fig_')) >= 2]
        if len(figNums) == 0:
            nextFigNum = 0
        else:
            nextFigNum = max(figNums) + 1

        fullTitle = os.path.join(plotDirectory, '{0:03d}_fig_{1}.{2}'.format(nextFigNum, savetitle, imageExtension))
        print(fullTitle)
        fig.savefig(fullTitle, dpi=1000)
        plt.close(fig) 
        
        return fullTitle
        
    if plotDirectory is None and not plotWithPylab:
        print('Must be in pylab and/or set a plot directory to display figures')
        
        plt.close(fig) 


def changeDisplayFigureSettings(newDirectory=None, newImageExtension='png',
                                newPlotWithPylab=True, newFigureScale=1):
    global plotDirectory
    plotDirectory = newDirectory
    
    global imageExtension
    imageExtension = newImageExtension
    
    global plotWithPylab
    plotWithPylab = newPlotWithPylab
    
    global figureScale
    figureScale = newFigureScale


def plotGrid(axis, vert_origin = True, horiz_origin=True, unity=True):
    ylim = axis.get_ylim()
    xlim = axis.get_xlim()
    if vert_origin:
        axis.plot((0,0), ylim, color='#BFBFBF', lw=.5, alpha=.5) 
    if horiz_origin:
        axis.plot(xlim,(0,0), color='#BFBFBF', lw=.5, alpha=.5) 
    if unity:
        xmin = min(xlim[0], ylim[0])
        xmax = max(xlim[1], ylim[1])
        axis.plot((xmin, xmax), (xmin, xmax), color='#BFBFBF', lw=.5, alpha=.5)
        
    axis.set_ylim(ylim)
    axis.set_xlim(xlim)


# adapted from http://nbviewer.ipython.org/github/cs109/content/blob/master/lec_03_statistical_graphs.ipynb
def cleanAxes(axis, top=False, right=False, bottom=True, left=True):
    axis.spines['top'].set_visible(top)
    axis.spines['right'].set_visible(right)
    axis.spines['left'].set_visible(left)
    axis.spines['bottom'].set_visible(bottom)

    # turn off all ticks
    axis.yaxis.set_ticks_position('none')
    axis.xaxis.set_ticks_position('none')

    # now re-enable visibles
    if top:
        axis.xaxis.tick_top()
    if bottom:
        axis.xaxis.tick_bottom()
    if left:
        axis.yaxis.tick_left()
    if right:
        axis.yaxis.tick_right()
