from matplotlib.pylab import plt
import numpy as np

def makechart(data, savefile=None, show=True):
	num_datasets = len(data)
	colors = 'rgbycmkw'
	opacity= 1.0
	bwidth = 0.50
	
	plt.subplots()
	
	for ix, d in enumerate(data):
		plt.bar(np.arange(len(data[d])) + (ix * (bwidth/num_datasets)), 
							list(data[d].values()), 
							bwidth, alpha = opacity, color = colors[ix], label=d, align='center')
							
	plt.xlabel = 'Runner'
	plt.ylabel = 'Total'
	plt.title = 'Runs by Year'
	plt.xticks(np.arange(len(data['Ian'])), list(data['Ian'].keys()))
	plt.legend()
	
	plt.tight_layout()
	if show:
		plt.show()

	if savefile:
		plt.savefig(savefile)
	
	plt.close()

if __name__ == '__main__':
	data = {
		'Ian': {'2019': 2, '2018': 50, '2017': 32, '2016': 27, '2015': 25, '2014': 30, '2013': 32, '2012': 38, '2011': 16},
		'Caroline': {'2019': 2, '2018': 37},
		'Other': {'2019': 1, '2018': 5},	
		'4th': {'2019': 1, '2018': 15},	
	#	'5th': {'2019': 1, '2018': 23}		
	}
	
	makechart(data)
