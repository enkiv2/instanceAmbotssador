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
	print("Usage: ambotssador client_key_1 user_key_1 api_base_url_1 client_key_2 user_key_2 api_base_url_2 [ ... client_key_n user_key_n api_base_url_n] [cycle_length]")
	sys.exit(1)

mastodon=[]
endpointCount=len(sys.argv)/3
for i in range(0, endpointCount):
	mastodon.append(Mastodon(sys.argv[1+(3*i)], access_token=sys.argv[2+(3*i)], api_base_url=sys.argv[3+(3*i)]))

rate=15*60*60 # boost every fifteen minutes by default
if(len(sys.argv)>endpointCount*3):
	rate=int(sys.argv[endpointCount*3+1])

while True:
	start=time.time()
	tl=[]
	for i in range(0, endpointCount):
		tl.append(mastodon[i].timeline_local(limit=1000))

	tlS=[{}]*endpointCount
	count=0
	favFreq=0
	for i in range(0, endpointCount):
		for toot in tl[i]:
			favs=toot["favourites_count"]
			tootId=toot["id"]
			if favs in tlS[i]:
				tlS[i][favs].append(tootId)
			else:
				tlS[i][favs]=[tootId]
		fk=tlS[i].keys()
		fk.sort()
		fk.reverse()
		done=False
		for rank in fk:
			if(rank==0): # don't bother boosting anything with zero favs
				break
			if(done):
				break
			for tootId in fk[rank]:
				startCount=count
				if not (tootId in boostedToots):
					for other in range(0, endpointCount):
						if other != i:
							mastodon[other].status_reblog(tootId)
							boostedToots.append(tootId)
							favFreq=rank; done=True; count+=1
				print("Boosted "+str(count-startCount)+" toots from node "+sys.argv[3+(i*3)]+" -- fav freq="+str(rank))

	boostedToots2=pickle.load(open("boostedToots.pickle", "r"))
	boostedToots2.extend(boostedToots)
	boostedToots=list(set(boostedToots2))
	pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
	print("Boosted "+str(count)+" toots -- fav freq "+str(favFreq))
	end=time.time()
	delta=end-start
	if(delta<rate):
		time.sleep(rate-delta)


