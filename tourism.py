import requests
from ast import literal_eval
from configuration import *
import pandas as pd
import numpy as np
import time
import math
from google_api import *

api = ApiQueries()

# Find place_id values
if False:
    pts = pd.read_csv('data/points_sherbrooke.csv')
    for row in pts[0:].iterrows():
        x = row[1]['left']
        y = row[1]['top']
        lat, lng = utm_to_dd(19, x, y)
        api.photos_radius(lat, lng, 354)
        print(len(api.db_places))
        if row[0] % 100 == 0:
            api.db_places.to_csv('data/db_place_id_2.csv', index_col='place_id')
    api.db_places = api.db_places.drop_duplicates(subset=['place_id'])
    api.db_places.to_csv('data/db_place_id_2.csv', index_col='place_id')

# Find all pictures per place_id
if False:
    api.db_places = pd.read_csv('data/db_place_id.csv', index_col='place_id')

    cnt = 0
    cnt_tot = len(api.db_places)
    for row in api.db_places.iterrows():
        api.photos_details(row[0])
        print('Photos: ' + str(len(api.photos)) + " - at " + str(cnt) + " / " + str(cnt_tot) + " - " + api.lst_names[-1])
        cnt += 1
    pass
    api.db_photos.to_csv('data/db_photos.csv', index='ref')
    api.db_places2 = pd.DataFrame([], columns=['place_name','photo_count', 'phone', 'status', 'url'])
    api.db_places2['place_name'] = api.lst_names
    api.db_places2['photo_count'] = api.lst_counts
    api.db_places2['phone'] = api.lst_phones
    api.db_places2['status'] = api.lst_status
    api.db_places2['url'] = api.lst_urls
    api.db_places2.to_csv('data/db_places2.csv', index='place_id')
    pass


# Fix data hole (1)
if False:    
    api.db_places = pd.read_csv('data/db_place_id.csv', index_col='place_id')
    counts = pd.read_csv('data/counts.csv').values[:,1]
    phones = pd.read_csv('data/phones.csv').values[:,1]
    status = pd.read_csv('data/status.csv').values[:,1]
    names = pd.read_csv('data/names.csv').values[:,1]
    urls = pd.read_csv('data/urls.csv').values[:,1]

    counts_ = np.append(np.append(counts[:3359], [0]), counts[3359:])
    phones_ = np.append(np.append(phones[:3359], ["NA"]), phones[3359:])
    status_ = np.append(np.append(status[:3359], ["NA"]), status[3359:])
    names_ = np.append(np.append(names[:3359], ["NA"]), names[3359:])
    urls_ = np.append(np.append(urls[:3359], ["NA"]), urls[3359:])

    api.db_places['photo_count'] = counts_
    api.db_places['phone'] = phones_
    api.db_places['business'] = status_
    api.db_places['account'] = names_
    api.db_places['url'] = urls_
    
    api.db_places.to_csv("data/db_places.csv", index="place_id")



# Count photos per photo_id, with and without place_id owner
if False:
    api.db_photos = pd.read_csv('data/db_photos.csv', index_col='ref')
    api.db_places = pd.read_csv('data/db_places.csv', index_col='place_id')
    api.db_places['photo_count_all'] = 0
    api.db_places['photo_count_filtered'] = 0

    count = 0
    for id_, photo in api.db_photos.iterrows():
        count += 1
        place = api.db_places.loc[photo['place_id']].copy()
        place.loc['photo_count_all'] += 1
        
        if photo['author'] != api.db_places.loc[photo['place_id']]['account']:
            place.loc['photo_count_filtered'] += 1
 
        api.db_places.loc[photo['place_id']] = place
        if not count % 100:
            print(count)
           
    api.db_places.to_csv("data/db_places.csv", index="place_id")

