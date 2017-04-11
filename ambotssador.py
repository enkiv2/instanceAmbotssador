#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, time
import codecs
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

import traceback

try:
	import cPickle as pickle
except:
	import pickle

from random import Random
random=Random()

from mastodon import Mastodon

boostedToots=[]
if os.path.exists("boostedToots.pickle"):
	boostedToots=pickle.load(open("boostedToots.pickle", "r"))
else:
	pickle.dump(boostedToots, open("boostedToots.pickle", "w"))

if(len(sys.argv)<=6):
	print("Usage: ambotssador client_key_1 user_key_1 api_base_url_1 client_key_2 user_key_2 api_base_url_2 [ ... client_key_n user_key_n api_base_url_n] [cycle_length]")
	sys.exit(1)

print("Connecting...")
mastodon=[]
endpointCount=len(sys.argv)/3
for i in range(0, endpointCount):
	mastodon.append(Mastodon(client_id=sys.argv[1+(3*i)], access_token=sys.argv[2+(3*i)], api_base_url=sys.argv[3+(3*i)]))
print("Connected to "+str(endpointCount)+" nodes")

rate=15*60*60 # boost every fifteen minutes by default
if(len(sys.argv)>endpointCount*3+1):
	rate=int(sys.argv[endpointCount*3+1])

maxRank=[0]*endpointCount

iterations=0
while True:
	try:
		start=time.time()
		tl=[]
		for i in range(0, endpointCount):
			try:
				tl.append(mastodon[i].timeline_local(limit=1000))
			except:
				tl.append([])

		tlS=[{}]*endpointCount
		count=0
		favFreq=0
		for i in range(0, endpointCount):
			tootInfo={}
			for toot in tl[i]:
				favs=toot["favourites_count"]
				tootId=toot["url"]
				tootInfo[tootId]=toot
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
				if(maxRank[i]-rank>5):
					done=True
				tootId=random.choice(tlS[i][rank])
				startCount=count
				if not (tootId in boostedToots):
					other=random.choice(range(0, endpointCount))
					if other != i:
						try:
							msgbase="\n(Boosting from "+sys.argv[3+(3*i)]+": "+tootId+", with "+str(rank)+" favorites)"
							user_components=tootId.split("/")
							username="@".join([user_components[3], user_components[2]])
							orig=username+" "+tootInfo[tootId]["content"].replace("<p>", "\n").replace("</p>", "\n")
							print(orig)
							if(len(orig)>500-len(msgbase)):
								orig=orig[:500-len(msgbase)-4]+"..."
							print(orig+msgbase)
							mastodon[other].toot(orig+msgbase)
							time.sleep(60)
							done=True
						except Exception as e:
							print("Error posting to "+sys.argv[3+(other*3)]+":")
							print(e)
							traceback.print_exc()
							retrySuccess=False
							for retries in range(0, 3):
								if(retrySuccess):
									break
								try:
									print("Reconnecting to "+sys.argv[3+(other*3)])
									mastodon[other]=Mastodon(
										client_id=sys.argv[1+(3*other)],
										access_token=sys.argv[2+(3*other)],
										api_base_url=sys.argv[3+(3*other)])
									print("Reconnected")
									time.sleep(1+retries*10)
									print("Retrying post")
									msgbase="\n(Boosting from "+sys.argv[3+(3*i)]+": "+tootId+", with "+str(rank)+" favorites)"
									user_components=tootId.split("/")
									username="@".join([user_components[3], user_components[2]])
									orig=username+" "+tootInfo[tootId]["content"].replace("<p>", "\n").replace("</p>", "\n")
									print(orig)
									if(len(orig)>500-len(msgbase)):
										orig=orig[:500-len(msgbase)-4]+"..."
									print(orig+msgbase)
									mastodon[other].toot(orig+msgbase)
									time.sleep(60)
									retrySuccess=True
									done=True
								except Exception as f:
									print(f)
									traceback.print_exc()
									time.sleep(1+retries*10)
							if not retrySuccess:
								print("Failed; removing from list")
								mastodon=mastodon[:other]+mastodon[other+1:]
								tl=tl[:other]+tl[other+1:]
								tlS=tlS[:other]+tlS[other+1:]
								sys.argv=sys.argv[:3*other+1]+sys.argv[3*other+4:]
								endpointCount-=1
								break
							
					favFreq=rank; count+=1
					boostedToots.append(tootId)
					boostedToots=list(set(boostedToots))
					pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
					time.sleep(60)
				if(count>startCount):
					print("Boosted "+str(count-startCount)+" toots from node "+sys.argv[3+(i*3)]+" -- fav freq="+str(rank))

		if(count>0):
			pickle.dump(boostedToots, open("boostedToots.pickle", "w"))
			print("Boosted "+str(count)+" toots -- fav freq "+str(favFreq))
		iterations+=1
		end=time.time()
		delta=end-start
		if(delta<rate):
			time.sleep(rate-delta)
	except Exception as e:
		print(e)
		traceback.print_exc()
		print("Reconnecting in 60s")
		# If we have an error in getting timeline, wait 60 seconds & then reconnect to all instances
		time.sleep(60)
		print("Reconnecting")
		mastodon=[]
		for i in range(0, endpointCount):
			mastodon.append(Mastodon(client_id=sys.argv[1+(3*i)], access_token=sys.argv[2+(3*i)], api_base_url=sys.argv[3+(3*i)]))
		print("Reconnected")


