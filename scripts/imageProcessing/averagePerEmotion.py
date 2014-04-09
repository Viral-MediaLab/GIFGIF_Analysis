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

def rgb2lab ( inputColor ) :
   num = 0
   RGB = [0, 0, 0]
   for value in inputColor :
       value = float(value) / 255
       if value > 0.04045 :
           value = ( ( value + 0.055 ) / 1.055 ) ** 2.4
       else :
           value = value / 12.92
       RGB[num] = value * 100
       num = num + 1
   XYZ = [0, 0, 0,]
   X = RGB [0] * 0.4124 + RGB [1] * 0.3576 + RGB [2] * 0.1805
   Y = RGB [0] * 0.2126 + RGB [1] * 0.7152 + RGB [2] * 0.0722
   Z = RGB [0] * 0.0193 + RGB [1] * 0.1192 + RGB [2] * 0.9505
   XYZ[ 0 ] = round( X, 4 )
   XYZ[ 1 ] = round( Y, 4 )
   XYZ[ 2 ] = round( Z, 4 )
   XYZ[ 0 ] = float( XYZ[ 0 ] ) / 95.047         # ref_X =  95.047   Observer= 2°, Illuminant= D65
   XYZ[ 1 ] = float( XYZ[ 1 ] ) / 100.0          # ref_Y = 100.000
   XYZ[ 2 ] = float( XYZ[ 2 ] ) / 108.883        # ref_Z = 108.883
   num = 0
   for value in XYZ :
       if value > 0.008856 :
           value = value ** ( 0.3333333333333333 )
       else :
           value = ( 7.787 * value ) + ( 16 / 116 )
       XYZ[num] = value
       num = num + 1
   Lab = [0, 0, 0]
   L = ( 116 * XYZ[ 1 ] ) - 16
   a = 500 * ( XYZ[ 0 ] - XYZ[ 1 ] )
   b = 200 * ( XYZ[ 1 ] - XYZ[ 2 ] )
   Lab [ 0 ] = round( L, 4 )
   Lab [ 1 ] = round( a, 4 )
   Lab [ 2 ] = round( b, 4 )
   return (Lab[0],Lab[1],Lab[2])


def lab2rgb((L,a,b)):
	var_Y = (L + 16 ) / 116
	var_X = a / 500 + var_Y
	var_Z = var_Y - b / 200
	if ( var_Y**3 > 0.008856 ):
		var_Y = var_Y**3
	else:
		var_Y = ( var_Y - 16 / 116 ) / 7.787
	if ( var_X**3 > 0.008856 ):
		var_X = var_X**3
	else:                      
		var_X = ( var_X - 16 / 116 ) / 7.787
	if ( var_Z**3 > 0.008856 ): 
		var_Z = var_Z**3
	else:                      
		var_Z = ( var_Z - 16 / 116 ) / 7.787
	ref_X =  95.047
	ref_Y = 100.000
	ref_Z = 108.883
	X = ref_X * var_X  
	Y = ref_Y * var_Y  
	Z = ref_Z * var_Z 
	var_X = X / 100        
	var_Y = Y / 100        
	var_Z = Z / 100        
	var_R = var_X *  3.2406 + var_Y * -1.5372 + var_Z * -0.4986
	var_G = var_X * -0.9689 + var_Y *  1.8758 + var_Z *  0.0415
	var_B = var_X *  0.0557 + var_Y * -0.2040 + var_Z *  1.0570
	if ( var_R > 0.0031308 ):
		var_R = 1.055 * ( var_R ** ( 1 / 2.4 ) ) - 0.055
	else:                     
		var_R = 12.92 * var_R
	if ( var_G > 0.0031308 ): 
		var_G = 1.055 * ( var_G ** ( 1 / 2.4 ) ) - 0.055
	else:                     
		var_G = 12.92 * var_G
	if ( var_B > 0.0031308 ): 
		var_B = 1.055 * ( var_B ** ( 1 / 2.4 ) ) - 0.055
	else:                     
		var_B = 12.92 * var_B
	R = var_R * 255
	G = var_G * 255
	B = var_B * 255
	return (R,G,B)



# Setup Pymongo connection
connection = pymongo.Connection(host='127.0.0.1', port=27017)
db = connection.gifgif
c_scores = db.scores
c_gifs = db.gifs
#

#Calculate metric average colors
numColorsPerImage = 1
numTopImages = 50
gifPath = '../../gifs/'

averageColors = {}
for metric in metrics:
	print metric
	topScores = c_scores.find().sort('scores.'+metric,-1).limit(numTopImages)
	allColors = [0,0,0]
	numColors = 0
	for item in topScores:
		image_id = item['image_id']
		image_file_id = c_gifs.find_one({'_id':ObjectId(image_id)})['file_id']
		gifURI = gifPath + image_file_id + '_still.gif'
		mainColors = returnDominant(gifURI,numColorsPerImage)
		for color in mainColors:
			rgbCol = (color[1][0],color[1][1],color[1][2])
			labColor = rgb2lab(rgbCol)# Add colors to some data structure
			# print color[1]
			numColors += 1
			allColors[0] += labColor[0]
			allColors[1] += labColor[1]
			allColors[2] += labColor[2]
			# allColors.append(labColor)
		# Average colors
	averageLab = (allColors[0]/numColors,allColors[1]/numColors,allColors[2]/numColors)
	averageRGB = lab2rgb(averageLab)
	averageColors[metric] = averageRGB


print averageColors

swatchsize = 20
numcolors = 17
pal = Image.new('RGB', (swatchsize*numcolors, swatchsize))
draw = ImageDraw.Draw(pal)

posx = 0
for metric in averageColors:
	col = averageColors[metric]
	col = (int(col[0]),int(col[1]),int(col[2]))
	draw.rectangle([posx, 0, posx+swatchsize, swatchsize], fill=col)
	posx = posx + swatchsize

del draw
pal.save('averageOutput.png', "PNG")

			# When averageing colors, we may need to use Lab colorspace: http://en.wikipedia.org/wiki/Lab_color_space
			# As recommeded here: http://stackoverflow.com/questions/398224/how-to-mix-colors-naturally-with-c

#



