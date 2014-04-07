import json
import pymongo
import math
from datetime import datetime


# json_data = open('../local/geo_scores_formatted.json', default=json_util.default)
# geo_scores = json.load(json_data)
# json_data.close()



# OMG THIS CODE IS UGLY AND BRUTE FORCE!!! UGHHU OMG OMG OMG OMG

connection = pymongo.Connection(host='127.0.0.1', port=3001)
try:
	db = connection.meteor
except:
	print "Can't seem to find the meteor database"


outputJSON = []


c_scores = db.geo_scores
c_geo_scores_normal = db.geo_scores_normal

scores = c_scores.find()

count = 0

index = 0
indexes = {}





for gif in scores:
	for country in gif['scores']:
		indexes[country] = index
		index += 1 
	break

scores = c_scores.find()
index = 0
emotionIndexes = {}
for gif in scores:
	for country in gif['scores']:
		for emotion in gif['scores'][country]:
			print emotion
			emotionIndexes[emotion] = index
			index += 1 
		break
	break

print emotionIndexes
print indexes
# print indexes



scoresOut = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 
counts = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 

scores = c_scores.find()
for gif in scores:
	# print thing['image_id']
	# print gif['scores']
	for country1 in gif['scores']:
		for country2 in gif['scores']:
			for emotion in gif['scores'][country1]:
				emotionScore1 = gif['scores'][country1][emotion]
				emotionScore2 = gif['scores'][country2][emotion]
				# print emotion1-emotion2
				index1 = indexes[country1]
				index2 = indexes[country2]
				emotionIndex = emotionIndexes[emotion]
				# print index2
				if emotionScore1 != 25:
					if emotionScore2 != 25:
						scoresOut[emotionIndex][index1][index2] += math.fabs(emotionScore1-emotionScore2)
						counts[emotionIndex][index1][index2] += 1
	# break

# print scoresOut 
# print counts


normalOutput = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 

maxPerEmotion = []

for x in range(17):
	thisMax = 0
	for y in range(21):
		for z in range(21):
			if counts[x][y][z] != 0:
				normalized = scoresOut[x][y][z]/counts[x][y][z]
				normalOutput[x][y][z] = normalized
				if normalized > thisMax:
					thisMax = normalized
	maxPerEmotion.append(thisMax)

# print maxPerEmotion

for x in range(17):
	for y in range(21):
		for z in range(21):
			if counts[x][y][z] != 0:
				normalizednormalized = normalOutput[x][y][z]/maxPerEmotion[x]
				normalOutput[x][y][z] = normalizednormalized
		sampleOut = {'emotionIndex': x, 'country': y, 'results': normalOutput[x][y]}
		outputJSON.append(sampleOut)

# print normalOutput


c_geo_scores_normal.insert(outputJSON)
