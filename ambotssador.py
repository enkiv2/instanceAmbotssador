#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, time
import codecs
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

try:
	import cPickle as pickle
except:
	import pickle


from mastodon import Mastodon

boostedToots=[]
if os.path.exists("boostedToots.pickle"):
	boostedToots=pickle.load(open("boostedToots.pickle", "r"))
else:
	pickle.dump(boostedToots, open("boostedToots.pickle", "w"))

if(len(sys.argv)<=6):
	print("Usage: ambotssador client_key_1 user_key_1 api_base_url_1 client_key_2 user_key_2 api_base_url_2 [cycle_length]")
	sys.exit(1)

mastodon=[]
for i in [0, 1]:
	mastodon.append(Mastodon(sys.argv[1+(3*i)], access_token=sys.argv[2+(3*i)], api_base_url=sys.argv[3+(3*i)]))

rate=15*60*60 # boost every fifteen minutes by default
if(len(sys.argv)>7):
	rate=int(sys.argv[7])

while True:
	start=time.time()
	tl=[]
	for i in [0, 1]:
		tl.append(mastodon[i].timeline_local(limit=1000))

	tlS=[{}, {}]
	count=0
	favFreq=0
	for i in [0, 1]:
		if i==0:
			other=1
		else:
			other=0
		for toot in tl[i]:
			favs=toot["favourites_count"]
			tootId=toot["id"]
			if favs in tlS[i]:
				tlS[i][favs].append(tootId)
			else:
				tlS[i][favs]=[tootId]
		fk=tlS[i].keys()
		fk.sort()
		done=False
		for rank in fk:
			if(fk[rank]==0): # don't bother boosting anything with zero favs
				break
			if(done):
				break
			for tootId in fk[rank]:
				if not (tootId in boostedToots):
					mastodon[other].status_reblog(tootId)
					boostedToots.append(tootId)
					favFreq=rank; done=True; count+=1

	boostedToots2=pickle.load(open("boostedToots.pickle", "r"))
	boostedToots2.extend(boostedToots)
	boostedToots=list(set(boostedToots2))
	pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
	print("Boosted "+str(count)+" toots -- fav freq "+str(favFreq))
	end=time.time()
	delta=end-start
	if(delta<rate):
		time.sleep(rate-delta)


