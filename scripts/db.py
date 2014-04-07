import os
import pymongo
import random
import sys
from uuid import uuid4
from bson.objectid import ObjectId
from pymongo import ASCENDING
import math
from random import choice
from random import randint
from trueskill import trueskill
import numpy.random as rnd
# FIXME: We can't get away with silencing all errors in these methods.
# They've made too many bugs hard to find. Let's add a real error logging system.

class database(object):
    def get_score(self, image_id):
        return self.db.scores.find_one({
                "image_id": str(image_id)
            })

    def get_country_score(self, image_id):
        return self.db.country_scores.find_one({
                "image_id": str(image_id)
            })

    # should be called internally, when adding a new image
    def _add_score(self, image_ids, questions, countries):
        score_documents = []
        country_score_documents = []
        empty_dict = dict([(q['metric'], 0) for q in questions])
        empty_scores_dict = dict([(q['metric'], trueskill.get_score(trueskill.mu0, trueskill.std0)) for q in questions])
        empty_parameters_dict = dict([(q['metric'], {'mu': trueskill.mu0, 'std': trueskill.std0}) for q in questions])

        for image_id in image_ids:
            document = {
                'total_vote_count': 0,
                'vote_counts': empty_dict,
                'neither_counts': empty_dict,
                'image_id': str(image_id),
                'scores': empty_scores_dict,
                'parameters': empty_parameters_dict
            }
            country_document = {
                'total_vote_count': 0,
                'vote_counts': dict([(country, empty_dict) for country in countries]),
                'neither_counts': dict([(country, empty_dict) for country in countries]),
                'image_id': str(image_id),
                'scores': dict([(country, empty_scores_dict) for country in countries]),
                'parameters': dict([(country, empty_parameters_dict) for country in countries])
            }
            score_documents.append(document)
            country_score_documents.append(country_document)

        Database.db.scores.insert(score_documents)
        Database.db.country_scores.insert(country_score_documents)
        return

    # Should be called internally, when update the score of an image after a vote
    def _push_score(self, metric, score_doc, mu, std, old_mu, old_std, isDraw):
        score = trueskill.get_score(mu, std)
        neither_inc = 0
        if isDraw: neither_inc = 1

        self.db.scores.update({'_id': score_doc['_id']}, {
            '$inc': {
                'total_vote_count': 1,
                'vote_counts.' + metric: 1,
                'neither_count.' + metric: neither_inc,
            },
            '$set': { 
                'scores.' + metric: score,
                'parameters.' + metric + '.mu': mu,
                'parameters.' + metric + '.std': std
            },
        })

    def _push_country_score(self, metric, score_doc, mu, std, old_mu, old_std, isDraw, country):
        score = trueskill.get_score(mu, std)
        neither_inc = 0
        if isDraw: neither_inc = 1

        self.db.country_scores.update({'_id': score_doc['_id']}, {
            '$inc': {
                'total_vote_count': 1,
                'vote_counts.' + country + '.' + metric: 1,
                'country_vote_count.' + country: 1,
                'neither_count.' + country: neither_inc
            },
            '$set': { 
                'scores.' + country + '.' + metric: score,
                'parameters.' + country + '.' + metric + '.mu': mu,
                'parameters.' + country + '.' + metric + '.std': std
            },
        })

    # Remove redundant parameters!
    def update_scores(self, metric, winner_image_id, loser_image_id, isDraw, country):
        '''
        Updating scores consists of several tasks:
            1. Updating the scores, true skill parameters, neither, and vote counts for a given emotion with and without country disaggregation
            2. Updating the global scores and vote counts
        '''

        # 1. Update the scores of the two locations (images)
        winner_score_doc = self.get_score(winner_image_id)
        loser_score_doc = self.get_score(loser_image_id)


        if winner_score_doc is None:
            print "Couldn't find a score document with image_id:", winner_image_id
            return
        if loser_score_doc is None:
            print "Couldn't find a score document with image_id:", loser_image_id
            return

        # get the last mu and standard deviation
        old_mu_winner = winner_score_doc['parameters'][metric]['mu']
        old_std_winner = winner_score_doc['parameters'][metric]['std']
        old_mu_loser = loser_score_doc['parameters'][metric]['mu']
        old_std_loser = loser_score_doc['parameters'][metric]['std']

        # update scores using the trueskill update equations
        (mu_winner, std_winner), (mu_loser, std_loser) = trueskill.update_rating((old_mu_winner, old_std_winner), (old_mu_loser, old_std_loser), isDraw)

        # 2. Push scores and Trueskill parameters of the images to the db
        self._push_score(metric, winner_score_doc, mu_winner, std_winner, old_mu_winner, old_std_winner, isDraw)

        if country:
            winner_country_score_doc = self.get_country_score(winner_image_id)
            loser_country_score_doc = self.get_country_score(loser_image_id)

            # get the last mu and standard deviation
            old_mu_winner_c = winner_country_score_doc['parameters'][country][metric]['mu']
            old_std_winner_c = winner_country_score_doc['parameters'][country][metric]['std']
            old_mu_loser_c = loser_country_score_doc['parameters'][country][metric]['mu']
            old_std_loser_c = loser_country_score_doc['parameters'][country][metric]['std']

            (mu_winner_c, std_winner_c), (mu_loser_c, std_loser_c) = trueskill.update_rating((old_mu_winner_c, old_std_winner_c), (old_mu_loser_c, old_std_loser_c), isDraw)

            self._push_country_score(metric, loser_country_score_doc, mu_loser_c, std_loser_c, old_mu_loser_c, old_std_loser_c, isDraw, country)

        # 3. Increment vote count for the question
        question_id = str(Database.db.questions.find_one({'metric': metric})['_id'])
        self.db.questions.update({'_id': ObjectId(question_id)}, { '$inc' : { 'num_votes': 1 }})

    @property
    def db(self):
        if not hasattr(self, '_db'):
            dbName = 'gifgif'
            self._db = self.conn[dbName]
        return self._db

    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self._conn = pymongo.Connection('localhost:27017')
        return self._conn

# a singleton object
Database = database()
