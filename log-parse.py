# Parse application log to monitor app behavior (query times, cache usage, etc)
# usage: python log-parse.py arg (file name to read without .in)
import operator
from collections import Counter
import sys
import config

fileToLoad = "resources/" + sys.argv[1] + ".in"

def processPerfLogLine(line, startIndex):
	# ex: 17:12:18 11/05/2013  INFO  PerfLogger select * from wbc.MWP_USER where guid = ?,QUERY,654
	timeIndex = line.rfind(',')
	execTime = line[(timeIndex+1):].rstrip()
	# 654
	
	nameAndType = line[38:timeIndex]
	typeIndex = nameAndType.rfind(',')
	# select * from wbc.MWP_USER where guid = ?,QUERY	
	
	action = nameAndType[:typeIndex].rstrip()
	# select * from wbc.MWP_USER where guid = ?
	
	return (action, execTime)
	
def processMemcachedLine(line, startIndex):
	# 17:12:18 11/05/2013  INFO  MemcachedCache Cache hit. Get by key 9e222457a1af4e10aa82345396ddee0a from cache memcached value 'ImageAsset [imagePath=null, extension=jpeg, size=6286, individualId=null, getId()=9e222457a1af4e10aa82345396ddee0a]'
	endDelimiterIndex = line.rfind('[')
	action = line[startIndex:endDelimiterIndex]
	action.strip()
	# Get by key 9e222457a1af4e10aa82345396ddee0a from cache memcached value 'ImageAsset
	return action

def updateRunningTotalDictionary(item, dictionary):
	if item in dictionary:
		numExecs = int(dictionary[item][0]) + 1
		dictionary[item] = [numExecs]
	else:
		dictionary[item] = [1]

def printResults(filename):
	q = Counter(config.query_list)
	print '----------------------------------------------------'
	print '-- Input File: {0}'.format(filename)
	print '----------------------------------------------------'
	print '----- Top 10 Queries (num executions) -----'
	print '--------------------------'
	for item in q.most_common(10):
		print '{0}\n{1} executions\n{2} msec in query\n{3} avg exec time\n'.format(item[0], item[1][0], item[1][1], round((float(item[1][1])/float(item[1][0])),2))

	t = Counter(config.time_in_query_list)
	print '----------------------------------------------------'
	print '----- Top 10 Queries (exec time) -----'
	print '----------------------------------------------------'
	for item in t.most_common(10):
		print '{0}\n{1} msec in query\n'.format(item[0], item[1])
		
	s = Counter(config.soap_list)
	print '----------------------------------------------------'
	print '----- Top 10 SOAP requests (exec time) -----'
	print '----------------------------------------------------'
	for item in s.most_common(10):
		print '{0}\n{1} executions\n{2} msec in query\n{3} avg exec time\n'.format(item[0], item[1][0], item[1][1], round((float(item[1][1])/float(item[1][0])),2))

	c = Counter(config.cache_list)
	print '---------------------------------'
	print '-----   Top 10 Cache Hits   -----'
	print '---------------------------------'
	for item in c.most_common(10):
		print '{0}\n{1} executions\n'.format(item[0], item[1][0])
		
	m = Counter(config.miss_list)
	if(m):
		print '-------------------------------'
		print '-----   Cache Misses   -----'
		print '-------------------------------'
		for item in m.most_common(20):
			print '{0}\n{1} executions\n'.format(item[0], item[1][0])
		
	f = Counter(config.evict_list)
	if(f):
		print '-------------------------------'
		print '-----   Cache Evictions   -----'
		print '-------------------------------'
		for item in f.most_common(20):
			print '{0}\n{1} executions\n'.format(item[0], item[1][0])

	print 'Cache Flushes: {6}\nCache Misses: {0}\nCache Hits: {1}\nDistinct queries: {2}\nTotal queries: {3}\nTotal query time: {4} msec\nSoap Queries: {7}\nLines Processed: {5}\n'.format(config.memcachedMisses, config.memcachedHits, len(config.query_list), config.numQueries, config.totalQueryTime, config.linesProcessed, config.memcachedEvictions, config.numSoapQueries)
	
def parseLog(filename):
	with open (filename, "r") as f:
	    for line in f:
			config.linesProcessed = config.linesProcessed + 1
			if ("SOAP" in line):
				config.numSoapQueries = config.numSoapQueries + 1
				query, execTime = processPerfLogLine(line, 38)				
				if query in config.soap_list:
					numExecs = int(config.soap_list[query][0]) + 1
					totalExecTime = int(config.soap_list[query][1]) + int(queryTime)
					config.soap_list[query] = [numExecs, totalExecTime]
				else:
					config.soap_list[query] = [1, queryTime]
			elif ("QUERY" in line):
				config.numQueries = config.numQueries + 1				
				query, queryTime = processPerfLogLine(line, 38)
				config.totalQueryTime = config.totalQueryTime + int(queryTime)
				if query in config.query_list:
					numExecs = int(config.query_list[query][0]) + 1
					totalExecTime = int(config.query_list[query][1]) + int(queryTime)
					config.query_list[query] = [numExecs, totalExecTime]
					config.time_in_query_list[query] = int(totalExecTime)
				else:
					config.query_list[query] = [1, queryTime]
					config.time_in_query_list[query] = int(queryTime)					
			elif("Cache hit." in line):
				config.memcachedHits = config.memcachedHits + 1				
				cached_query = processMemcachedLine(line, 53)
				updateRunningTotalDictionary(cached_query, config.cache_list)
			elif("Cache miss." in line):
				config.memcachedMisses = config.memcachedMisses + 1
				miss = processMemcachedLine(line, 54)
				updateRunningTotalDictionary(miss, config.miss_list)
			elif("Cache eviction" in line):
				config.memcachedEvictions = config.memcachedEvictions + 1
				eviction = processMemcachedLine(line, 58)
				updateRunningTotalDictionary(eviction, config.evict_list)

	printResults(filename)

	# Validate calculations
	numExecsInList = sum(int(query[0]) for query in config.query_list.values())
	totalTimeInList = sum(int(query[1]) for query in config.query_list.values())
	# numCacheHitsInList = sum(int(cache[0] for cache in config.cache_list.values()))

	#print '{0} execs {1} total time'.format(numExecsInList, totalTimeInList)
	if((config.numQueries != numExecsInList) or (config.totalQueryTime != totalTimeInList)):
		print '[WARNING! inconsistency in num of queries or cache hits]'

parseLog(fileToLoad)	
