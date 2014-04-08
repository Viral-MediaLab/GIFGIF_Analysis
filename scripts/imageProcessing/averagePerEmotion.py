'''
Place the average color per emotion on a color wheel. 
Take the top N global from each metric, sum their average colors. and put on wheel.

'''

import Image, ImageDraw
import pymongo
from bson.objectid import ObjectId

metrics = ['amusement','anger','contempt','contentment','disgust','embarrassment','excitement','fear','guilt','happiness','pleasure','pride','relief','sadness','satisfaction','shame','surprise']

def returnDominant(infile, numcolors=1):
    image = Image.open(infile)
    result = image.convert('P', palette=Image.ADAPTIVE, colors=numcolors)
    result.putalpha(0)
    colors = result.getcolors()
    return colors


# Setup Pymongo connection
connection = pymongo.Connection(host='127.0.0.1', port=27017)
db = connection.gifgif
c_scores = db.scores
c_gifs = db.gifs
#

#Calculate metric average colors
numColorsPerImage = 1
numTopImages = 3
gifPath = '../../gifs/'

averageColors = {}
for metric in metrics:
	topScores = c_scores.find().sort('scores.'+metric,-1).limit(numTopImages)
	for item in topScores:
		image_id = item['image_id']
		image_file_id = c_gifs.find_one({'_id':ObjectId(image_id)})['file_id']
		gifURI = gifPath + image_file_id + '_still.gif'
		mainColors = returnDominant(gifURI,numColorsPerImage)
		for color in mainColors:
			print color[1]
	break

		# When averageing colors, we may need to use Lab colorspace: http://en.wikipedia.org/wiki/Lab_color_space
		# As recommeded here: http://stackoverflow.com/questions/398224/how-to-mix-colors-naturally-with-c

#



