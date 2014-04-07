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
#--------------------Results

    locid2idx = None
    locs = None
    studyid2prob = None
    studs = None
    study_prob = None

#--------------------QS
    def get_score(self, image_id):
        return self.db.scores.find_one({
                "image_id": str(image_id)
            })

        # should be called internally, when adding a new image
    def _add_score(self, image_ids, questions, countries):
        inserted_documents = []
        empty_score_dict = dict([(q['metric'], trueskill.get_score(trueskill.mu0, trueskill.std0)) for q in questions])
        parameters_dict = dict([(q['metric'], {'mus':[trueskill.mu0], 'stds':[trueskill.std0]}) for q in questions])
        for image_id in image_ids:
            document = {
                'image_id': str(image_id),
                'scores': dict([(country, empty_score_dict) for country in countries]),
                'parameters': dict([(country, parameters_dict) for country in countries])
            }
            inserted_documents.append(document)
        return Database.db.scores.insert(inserted_documents)

    # Should be called internally, when update the score of an image after a vote
    def _push_score(self, metric, score_doc, mu, std, old_mu, old_std, isDraw, country):
        score = trueskill.get_score(mu, std)
        inc = 0
        if isDraw:
            inc = 1

        self.db.scores.update({'_id': score_doc['_id']}, {
            '$set': { 'scores.' + country + '.' + metric: score },
        })

    # Remove redundant parameters!
    def update_scores(self, metric, winner_image_id, loser_image_id, isDraw, country):
        '''
            Updating scores consists of several tasks:
            1. Updating the scores for a given question
            2. Updating the trueskill parameters
            3. Incrementing the vote count
        '''
        # 1. Update the scores of the two locations (images)
        winner_score_doc = self.get_score(winner_image_id)
        loser_score_doc = self.get_score(loser_image_id)
        if winner_score_doc is None:
            print "Couldn't find a score document with image_id", winner_image_id
            return
        if loser_score_doc is None:
            print "Couldn't find a score document with image_id", loser_image_id
            return

        # get the last mu and standard deviation
        old_mu_winner = winner_score_doc['parameters'][country][metric]['mus'][-1]
        old_std_winner = winner_score_doc['parameters'][country][metric]['stds'][-1]
        old_mu_loser = loser_score_doc['parameters'][country][metric]['mus'][-1]
        old_std_loser = loser_score_doc['parameters'][country][metric]['stds'][-1]

        # update scores using the trueskill update equations
        (mu_winner, std_winner), (mu_loser, std_loser) = trueskill.update_rating((old_mu_winner, old_std_winner), (old_mu_loser, old_std_loser), isDraw)

        # 2. Push scores and Trueskill parameters of the images to the db
        self._push_score(metric, winner_score_doc, mu_winner, std_winner, old_mu_winner, old_std_winner, isDraw, country)
        self._push_score(metric, loser_score_doc, mu_loser, std_loser, old_mu_loser, old_std_loser, isDraw, country)

        # 3. Increment vote count for the question
        question_id = str(Database.db.questions.find_one({'metric': metric})['_id'])
        self.db.questions.update({'_id': ObjectId(question_id)}, { '$inc' : { 'num_votes': 1 }})

    @property
    def votes(self):
        return self.db.votes

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
