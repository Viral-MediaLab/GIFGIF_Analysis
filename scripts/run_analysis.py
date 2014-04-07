'''
Module used to calculate scores for each image and emotion pair given votes.

Current version calculates scores given only votes with IPs. 

Usage: python run_analysis.py
'''

from time import time
import sys, os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))
import pymongo
from db import Database

countries = ['A1', 'A2', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AP', 'AR', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BG', 'BH', 'BI', 'BM', 'BN', 'BO', 'BR', 'BS', 'BY', 'BZ', 'CA', 'CH', 'CI', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CY', 'CZ', 'DE', 'DK', 'DO', 'DZ', 'EC', 'EE', 'EG', 'ES', 'ET', 'EU', 'FI', 'FO', 'FR', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GP', 'GR', 'GT', 'HK', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KR', 'KW', 'KZ', 'LB', 'LI', 'LK', 'LT', 'LU', 'LV', 'MA', 'MC', 'MD', 'ME', 'MG', 'MK', 'ML', 'MM', 'MN', 'MO', 'MQ', 'MT', 'MU', 'MV', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NG', 'NI', 'NL', 'NO', 'NP', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PH', 'PK', 'PL', 'PR', 'PS', 'PT', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SC', 'SD', 'SE', 'SG', 'SI', 'SK', 'SN', 'SR', 'SV', 'SY', 'TH', 'TN', 'TR', 'TT', 'TW', 'TZ', 'UA', 'UG', 'US', 'UY', 'UZ', 'VE', 'VG', 'VI', 'VN', 'VU', 'YT', 'ZA', 'ZM', 'ZW']

'''
The old version of the db doesn't create a qs entry when a study is created.
Because of this, selecting a random pair of images doesn't work correctly
'''
# Yield successive n-sized chunks from l.
def chunks(l, n):
  print len(l)
  for i in xrange(0, len(l), n):
    yield l[i:i+n]

# Reset scores for all images
def insert_scores():
  Database.db.drop_collection(Database.db.scores)
  # drop index for fast insertion
  Database.db.scores.drop_indexes()
  Database.db.scores.ensure_index("_id")

  questions = list(Database.db.questions.find())  # Need to cast into list to not run into end of cursor
  print len(questions), 'questions found in the db'

  images = Database.db.gifs.find()
  image_ids = [str(e['_id']) for e in images]

  chunk_size = 100
  for image_id_chunk in chunks(image_ids, chunk_size):
    result = Database._add_score(image_id_chunk, questions, countries)
    print 'Processing %s images with %s questions' % (chunk_size, len(questions))

  print 'Finished processing', len(image_ids), 'inserts'

# Process all votes and calculate Trueskill parameters + score
def process_past_votes():
  print 'Processing past votes'
  Database.db.scores.ensure_index([('image_id', pymongo.ASCENDING)]) # is this necessary?

  votes = Database.votes.find({'ip': {'$exists': True}})
  print votes.count(), 'un-calculated votes found in the DB'
  total_vote_count = 0
  used_vote_count = 0
  start_time = time()
  for vote in votes:
    total_vote_count += 1
    if total_vote_count % 1000 == 0:
      print "Processed %s votes in %s" % (total_vote_count, time() - start_time)
      print "Used %s votes" % used_vote_count
      start_time = time()

    try:
      metric = str(vote['metric'])
      question_id = str(Database.db.questions.find_one({'metric': metric})['_id'])
      country = vote['country']
      used_vote_count += 1
  
      if vote['choice'] in ['left', 'equal']:
        winner_file_id = vote['left']
        loser_file_id = vote['right']
        winner_image_id = str(Database.db.gifs.find_one({'file_id': winner_file_id})['_id'])
        loser_image_id = str(Database.db.gifs.find_one({'file_id': loser_file_id})['_id'])
      else:
        winner_file_id = vote['right']
        loser_file_id = vote['left']
        winner_image_id = str(Database.db.gifs.find_one({'file_id': winner_file_id})['_id'])
        loser_image_id = str(Database.db.gifs.find_one({'file_id': loser_file_id})['_id'])
      isDraw = vote['choice'] == 'both' or vote['choice'] == 'neither'
  
      update_scores_start = time()
  
      vote_id = vote['_id']
      Database.update_scores(metric, winner_image_id, loser_image_id, isDraw, country)

    except Exception as e:
      print "Error", e

  print 'Done processing votes!'

insert_scores()
process_past_votes()
