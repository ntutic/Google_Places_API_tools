import requests
from ast import literal_eval
from configuration import *
import pandas as pd
import numpy as np
import time
import math

def utm_to_dd(zone, easting, northing, northernHemisphere=True):
    if not northernHemisphere:
        northing = 10000000 - northing

    a = 6378137
    e = 0.081819191
    e1sq = 0.006739497
    k0 = 0.9996

    arc = northing / k0
    mu = arc / (a * (1 - math.pow(e, 2) / 4.0 - 3 * math.pow(e, 4) / 64.0 - 5 * math.pow(e, 6) / 256.0))

    ei = (1 - math.pow((1 - e * e), (1 / 2.0))) / (1 + math.pow((1 - e * e), (1 / 2.0)))

    ca = 3 * ei / 2 - 27 * math.pow(ei, 3) / 32.0

    cb = 21 * math.pow(ei, 2) / 16 - 55 * math.pow(ei, 4) / 32
    cc = 151 * math.pow(ei, 3) / 96
    cd = 1097 * math.pow(ei, 4) / 512
    phi1 = mu + ca * math.sin(2 * mu) + cb * math.sin(4 * mu) + cc * math.sin(6 * mu) + cd * math.sin(8 * mu)

    n0 = a / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (1 / 2.0))

    r0 = a * (1 - e * e) / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (3 / 2.0))
    fact1 = n0 * math.tan(phi1) / r0

    _a1 = 500000 - easting
    dd0 = _a1 / (n0 * k0)
    fact2 = dd0 * dd0 / 2

    t0 = math.pow(math.tan(phi1), 2)
    Q0 = e1sq * math.pow(math.cos(phi1), 2)
    fact3 = (5 + 3 * t0 + 10 * Q0 - 4 * Q0 * Q0 - 9 * e1sq) * math.pow(dd0, 4) / 24

    fact4 = (61 + 90 * t0 + 298 * Q0 + 45 * t0 * t0 - 252 * e1sq - 3 * Q0 * Q0) * math.pow(dd0, 6) / 720

    lof1 = _a1 / (n0 * k0)
    lof2 = (1 + 2 * t0 + Q0) * math.pow(dd0, 3) / 6.0
    lof3 = (5 - 2 * Q0 + 28 * t0 - 3 * math.pow(Q0, 2) + 8 * e1sq + 24 * math.pow(t0, 2)) * math.pow(dd0, 5) / 120
    _a2 = (lof1 - lof2 + lof3) / math.cos(phi1)
    _a3 = _a2 * 180 / math.pi

    latitude = 180 * (phi1 - fact1 * (fact2 + fact3 + fact4)) / math.pi

    if not northernHemisphere:
        latitude = -latitude

    longitude = ((zone > 0) and (6 * zone - 183.0) or 3.0) - _a3

    return (latitude, longitude)


class ApiQueries:
    def __init__(self):
        inputtype = "textquery" # Ou "phonenumber"
        self.photo_refs = []
        self.current = []
        self.search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/"+ format_response + "?key=" + key + "&inputtype=" + inputtype
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/" + format_response + "?key=" + key
        self.nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/" + format_response + "?key=" + key
        self.photos_url = "https://maps.googleapis.com/maps/api/place/photo?key=" + key

        self.db_places = pd.DataFrame([], columns=["lat", "lng", "place_id", "vicinity"])
        self.db_photos = pd.DataFrame([], columns=['ref', 'place_id', "author", "author_id", "place_name"])
        self.lst_counts = []
        self.lst_names = []
        self.lst_urls = []
        self.lst_phones = []
        self.lst_status = []
        

    def photos_radius(self, lat, long, radius):
        """
        
        """
        self.nearby_url = self.nearby_url.split("&radius=")[0] + "&radius=" + str(radius) + "&location=" + str(lat) + "," + str(long)
        self.limitter()
        self.post_nearby = requests.post(self.nearby_url)
        #print(self.nearby_url)
        while True:
            if self.post_nearby.json()["status"] == "OK":
                for place in self.post_nearby.json()["results"]:
                    lat = place['geometry']['location']['lat']
                    lng = place['geometry']['location']['lng']
                    place_id = place['place_id']
                    vicinity = place['vicinity']
                    self.db_places = self.db_places.append({"lat": lat, "lng": lng, "place_id": place_id, "vicinity": vicinity}, ignore_index=True)
                try:
                    self.limitter()
                    self.post_nearby = requests.post(self.nearby_url + "&pagetoken=" + self.post_nearby.json()['next_page_token'])
                    #print(self.nearby_url + "&pagetoken=" + self.post_nearby.json()['next_page_token'])
                    continue
                except KeyError:
                    break
            else:
                print("place_id invalide ")
                break


    def photos_details(self, place_id):
        self.limitter()
        self.post_details = requests.post(self.details_url  + "&place_id=" + place_id)
        photos = []
        if self.post_details.json()['status'] == "OK":
            try:
                self.lst_names += [self.post_details.json()['result']['name']]
            except KeyError:
                self.lst_names += ["NA"]
            try:
                self.lst_urls += [self.post_details.json()['result']['url']]
            except KeyError:
                self.lst_urls += ["NA"]  
            try:
                self.lst_phones += [self.post_details.json()['result']['international_phone_number']]
            except KeyError:
                self.lst_phones += ["NA"]  
            try:
                self.lst_status += [self.post_details.json()['result']['business_status']]
            except KeyError:
                self.lst_status += ['NA']
            try:
                self.photos = self.post_details.json()['result']['photos']
                self.lst_counts += [len(self.photos)]
                
                for photo in self.photos:
                    ref = photo['photo_reference']
                    auth_id = int(photo['html_attributions'][0].split("contrib/")[1].split('">')[0])
                    auth = photo['html_attributions'][0].split(">")[1].split("<")[0]
                    self.db_photos = self.db_photos.append({"ref": ref, "author_id": auth_id, "author": auth, "place_id": place_id, "place_name": self.lst_names[-1]}, ignore_index=True)
                    pass
            except KeyError:
                self.lst_counts += [0]


    

    def save_image(self, ref, maxheight=400):
        import exifread
        with open('image.jpg', 'rb') as fh:
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
            dateTaken = tags["EXIF DateTimeOriginal"]
            print(dateTaken)


    def limitter(self, max_=100, sec=1):
        """
        Respect des limites de requêtes, pour Google Place API, 100 requêtes/sec. 
        current: Liste des temps des requêtes dans la limite
        """
        
        t_ = time.time()
        self.current = [t for t in self.current if t > t_ - sec] + [t_]
        if len(self.current) >= max_:
            time.sleep(sec - (t_ - self.current[0]))
            del self.current[0]

        


