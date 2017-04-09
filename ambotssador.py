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
if(len(sys.argv)>endpointCount*3+1):
	rate=int(sys.argv[endpointCount*3+1])

maxRank=[0]*endpointCount

iterations=0
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
		if(fk[0]>maxRank[i]):
			maxRank[i]=fk[0]
		elif(iterations%10 == 0): # decay threshhold
			maxRank[i]-=1
		for rank in fk:
			if(rank==0): # don't bother boosting anything with zero favs
				break
			if(done):
				break
			if(maxRank[i]-rank>2):
				break
			for tootId in tlS[i][rank]:
				startCount=count
				if not (tootId in boostedToots):
					for other in range(0, endpointCount):
						if other != i:
							try:
								mastodon[other].status_reblog(tootId)
								boostedToots.append(tootId)
								favFreq=rank; done=True; count+=1
								pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
								time.sleep(5)
							except:
								pass
				print("Boosted "+str(count-startCount)+" toots from node "+sys.argv[3+(i*3)]+" -- fav freq="+str(rank))

	pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
	print("Boosted "+str(count)+" toots -- fav freq "+str(favFreq))
	iterations+=1
	end=time.time()
	delta=end-start
	if(delta<rate):
		time.sleep(rate-delta)


