'''
Given the scores of each gif, segmented by country, build a similarity matrix that shows the similarity 
between country A and country B (perhaps, on a normalized scale of 0.0 - 1.0).
The matrix will be of size N by N, where N is the number of countries we have available. The matrix can be 
reduced to be upper triangular.


Similarity is calculated by:
- For each gif, find all the countries that have voted a sufficient number of times on it. 
	- Of those counties that have voted enough, calculate the differences in resultant scores per emotion
	- append difference to an array given those two countries and emotion.
- Once the arrays have been built for every gif, reduce the value in each country by country array from an array to the average value of that array.
- This average value will be the average difference in scores for all sufficiently voted gifs.


- Should we also be calculating the deviation from the global result? 
- If so, it would require us to query the mongodb each time. Unless we first make a dict
'''



import json
import pymongo
import math
import time

metrics = ['amusement','anger','contempt','contentment','disgust','embarrassment','excitement','fear','guilt','happiness','pleasure','pride','relief','sadness','satisfaction','shame','surprise']
metricIndexes = {'amusement': 0,'anger': 1,'contempt': 2,'contentment': 3,'disgust': 4,'embarrassment': 5,'excitement': 6,'fear': 7,'guilt': 8,'happiness': 9,'pleasure': 10,'pride': 11,'relief': 12,'sadness': 13,'satisfaction': 14,'shame': 15,'surprise': 16}
countryIndexes = {'AP':0,'EU':1,'AD':2,'AE':3,'AF':4,'AG':5,'AI':6,'AL':7,'AM':8,'AN':9,'AO':10,'AQ':11,'AR':12,'AS':13,'AT':14,'AU':15,'AW':16,'AZ':17,'BA':18,'BB':19,'BD':20,'BE':21,'BF':22,'BG':23,'BH':24,'BI':25,'BJ':26,'BM':27,'BN':28,'BO':29,'BR':30,'BS':31,'BT':32,'BV':33,'BW':34,'BY':35,'BZ':36,'CA':37,'CC':38,'CD':39,'CF':40,'CG':41,'CH':42,'CI':43,'CK':44,'CL':45,'CM':46,'CN':47,'CO':48,'CR':49,'CU':50,'CV':51,'CX':52,'CY':53,'CZ':54,'DE':55,'DJ':56,'DK':57,'DM':58,'DO':59,'DZ':60,'EC':61,'EE':62,'EG':63,'EH':64,'ER':65,'ES':66,'ET':67,'FI':68,'FJ':69,'FK':70,'FM':71,'FO':72,'FR':73,'FX':74,'GA':75,'GB':76,'GD':77,'GE':78,'GF':79,'GH':80,'GI':81,'GL':82,'GM':83,'GN':84,'GP':85,'GQ':86,'GR':87,'GS':88,'GT':89,'GU':90,'GW':91,'GY':92,'HK':93,'HM':94,'HN':95,'HR':96,'HT':97,'HU':98,'ID':99,'IE':100,'IL':101,'IN':102,'IO':103,'IQ':104,'IR':105,'IS':106,'IT':107,'JM':108,'JO':109,'JP':110,'KE':111,'KG':112,'KH':113,'KI':114,'KM':115,'KN':116,'KP':117,'KR':118,'KW':119,'KY':120,'KZ':121,'LA':122,'LB':123,'LC':124,'LI':125,'LK':126,'LR':127,'LS':128,'LT':129,'LU':130,'LV':131,'LY':132,'MA':133,'MC':134,'MD':135,'MG':136,'MH':137,'MK':138,'ML':139,'MM':140,'MN':141,'MO':142,'MP':143,'MQ':144,'MR':145,'MS':146,'MT':147,'MU':148,'MV':149,'MW':150,'MX':151,'MY':152,'MZ':153,'NA':154,'NC':155,'NE':156,'NF':157,'NG':158,'NI':159,'NL':160,'NO':161,'NP':162,'NR':163,'NU':164,'NZ':165,'OM':166,'PA':167,'PE':168,'PF':169,'PG':170,'PH':171,'PK':172,'PL':173,'PM':174,'PN':175,'PR':176,'PS':177,'PT':178,'PW':179,'PY':180,'QA':181,'RE':182,'RO':183,'RU':184,'RW':185,'SA':186,'SB':187,'SC':188,'SD':189,'SE':190,'SG':191,'SH':192,'SI':193,'SJ':194,'SK':195,'SL':196,'SM':197,'SN':198,'SO':199,'SR':200,'ST':201,'SV':202,'SY':203,'SZ':204,'TC':205,'TD':206,'TF':207,'TG':208,'TH':209,'TJ':210,'TK':211,'TM':212,'TN':213,'TO':214,'TL':215,'TR':216,'TT':217,'TV':218,'TW':219,'TZ':220,'UA':221,'UG':222,'UM':223,'US':224,'UY':225,'UZ':226,'VA':227,'VC':228,'VE':229,'VG':230,'VI':231,'VN':232,'VU':233,'WF':234,'WS':235,'YE':236,'YT':237,'RS':238,'ZA':239,'ZM':240,'ME':241,'ZW':242,'A1':243,'A2':244,'O1':245,'AX':246,'GG':247,'IM':248,'JE':249,'BL':250,'MF':251}
minVotes = 5 #Number of votes that must have been cast for a specific gif for a specific emotion in order to consider it's data
# How do we defend the choice of X votes as min?
similarity = [[[[] for x in xrange(252)] for x in xrange(252)] for x in range(17)] # Create 17 55x55 2D-matricies. Each initialized with an empty array.


# Get all Scores
connection = pymongo.Connection(host='127.0.0.1', port=27017)
try:
	db = connection.gifgif
except:
	print "Can't seem to find the meteor database"
c_country_scores = db.country_scores
country_scores = c_country_scores.find()


# Iterate Through Each Gif Score
count=0
totalGifs = 6079

startTime = time.time()

for score in country_scores:
	image_id = score['image_id'] # mongo ID num of the gif
	total_vote_count = score['total_vote_count'] # Single number, total votes over all countries and emotions
	vote_counts = score['vote_counts'] #Object with country codes as Keys, and then a list of emotion keys with vote values
	scores = score['scores'] #Object with country codes as Keys, and then a list of emotion keys with score values
	neither_count = score['neither_count'] # Object list with countries as keys and neither count as value
	neither_counts = score['neither_counts'] # Object list with countries as keys list of emotions with neither count for that country and emotion as value
	country_vote_count = score['country_vote_count'] # Object list with countries as keys and vote count as value
	for emotion in metrics:
		# Find countries that have enough votes, add them to a list
		sufficentVotesCountries = []
		for country in vote_counts:
			if vote_counts[country][emotion] >= minVotes:
				sufficentVotesCountries.append(country)
		# For each country in that list, get the scores, and compare their difference.
		if len(sufficentVotesCountries) > 1:
			for country1 in sufficentVotesCountries:
				for country2 in sufficentVotesCountries:
					if country1 != country2:
						difference = math.fabs(scores[country1][emotion] - scores[country2][emotion])
						similarity[metricIndexes[emotion]][countryIndexes[country1]][countryIndexes[country2]].append(difference)
						# print emotion + " " + str(difference) + " " + country1 + " " + country2
				# print " ----- " 
	# print similarity
	count += 1
	if count % 100 == 0:
		# print similarity
		# break
		lapTime = time.time()
		print "Finished " + str(count)
		print "Remaining Time: " + str((lapTime-startTime)/count*(totalGifs-count)/60) + " minutes"
		print "-------------------------"



# For each resulting array in similarity, compress it to a single number.
for x in range(0,17):
	for y in range(0,252):
		for z in range(0,252):
			if len(similarity[x][y][z]) >0:
				similarity[x][y][z] = sum(similarity[x][y][z])/len(similarity[x][y][z])
			else:
				similarity[x][y][z] = -1

# print similarity



# Normalize Per emotion
for x in range(0,17):
	maxVal = 0 
	for y in range(0,252):
		for z in range(0,252):
			if similarity[x][y][z] > maxVal:
				maxVal = similarity[x][y][z]
	print maxVal
	for y in range(0,252):
		for z in range(0,252):
			if similarity[x][y][z] != -1:
				similarity[x][y][z] = similarity[x][y][z]/maxVal


print similarity


# ------------------------------------------------------------------------------------
# Old version below. Was run when we were only using 21 countries and such. For the Ethan project...
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

# json_data = open('../local/geo_scores_formatted.json', default=json_util.default)
# geo_scores = json.load(json_data)
# json_data.close()



# OMG THIS CODE IS UGLY AND BRUTE FORCE!!! UGHHU OMG OMG OMG OMG




# outputJSON = []



# c_geo_scores_normal = db.geo_scores_normal

# scores = c_scores.find()

# count = 0

# index = 0
# indexes = {}





# for gif in scores:
# 	for country in gif['scores']:
# 		indexes[country] = index
# 		index += 1 
# 	break

# scores = c_scores.find()
# index = 0
# emotionIndexes = {}
# for gif in scores:
# 	for country in gif['scores']:
# 		for emotion in gif['scores'][country]:
# 			print emotion
# 			emotionIndexes[emotion] = index
# 			index += 1 
# 		break
# 	break

# print emotionIndexes
# print indexes
# # print indexes



# scoresOut = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 
# counts = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 

# scores = c_scores.find()
# for gif in scores:
# 	# print thing['image_id']
# 	# print gif['scores']
# 	for country1 in gif['scores']:
# 		for country2 in gif['scores']:
# 			for emotion in gif['scores'][country1]:
# 				emotionScore1 = gif['scores'][country1][emotion]
# 				emotionScore2 = gif['scores'][country2][emotion]
# 				# print emotion1-emotion2
# 				index1 = indexes[country1]
# 				index2 = indexes[country2]
# 				emotionIndex = emotionIndexes[emotion]
# 				# print index2
# 				if emotionScore1 != 25:
# 					if emotionScore2 != 25:
# 						scoresOut[emotionIndex][index1][index2] += math.fabs(emotionScore1-emotionScore2)
# 						counts[emotionIndex][index1][index2] += 1
# 	# break

# # print scoresOut 
# # print counts


# normalOutput = [[[0 for x in xrange(21)] for x in xrange(21)] for x in range(17)] 

# maxPerEmotion = []

# for x in range(17):
# 	thisMax = 0
# 	for y in range(21):
# 		for z in range(21):
# 			if counts[x][y][z] != 0:
# 				normalized = scoresOut[x][y][z]/counts[x][y][z]
# 				normalOutput[x][y][z] = normalized
# 				if normalized > thisMax:
# 					thisMax = normalized
# 	maxPerEmotion.append(thisMax)

# # print maxPerEmotion

# for x in range(17):
# 	for y in range(21):
# 		for z in range(21):
# 			if counts[x][y][z] != 0:
# 				normalizednormalized = normalOutput[x][y][z]/maxPerEmotion[x]
# 				normalOutput[x][y][z] = normalizednormalized
# 		sampleOut = {'emotionIndex': x, 'country': y, 'results': normalOutput[x][y]}
# 		outputJSON.append(sampleOut)

# # print normalOutput


# c_geo_scores_normal.insert(outputJSON)
