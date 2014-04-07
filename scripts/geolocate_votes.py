'''
Geolocate votes from IP to country code. Modifies original votes document to include country code.

Uses GeoIP database and utility script (GeoIP.dat and geoip.py in same directory.)

Run: python geolocate_votes.py
'''

import geoip
import pymongo
from db import Database

def geolocate():
    votes = Database.db.votes.find({'ip': {'$exists': True}})
    count = 0
    for vote in votes:
        count += 1
        if (count % 10000) == 0: print 'Votes processed:', count
        vote_id = vote['_id']
        ip = vote['ip']
        country_code = geoip.country(ip)
        Database.db.votes.update({'_id': vote_id}, {
            '$set': {'country': country_code}
        })

if __name__ == '__main__':
    geolocate()
