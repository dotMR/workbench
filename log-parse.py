# Parse application log to monitor app behavior (query times, cache usage, etc)
# usage: python log-parse.py arg (file name to read without .in)
import operator
from collections import Counter
import sys

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

def parseLog(filename):
	numQueries = 0
	linesProcessed = 0
	totalQueryTime = 0
	memcachedHits = 0
	memcachedMisses = 0
	cacheFlushes = 0
	numSoapQueries = 0

	soap_list = dict()
	query_list = dict()
	cache_list = dict()
	time_in_query_list = dict()
	miss_list = dict()
	flush_list = dict()
	
	with open (filename, "r") as f:
	    for line in f:
			linesProcessed = linesProcessed + 1
			if ("SOAP" in line):
				numSoapQueries = numSoapQueries + 1
				query, execTime = processPerfLogLine(line, 38)				
				if query in soap_list:
					numExecs = int(soap_list[query][0]) + 1
					totalExecTime = int(soap_list[query][1]) + int(queryTime)
					soap_list[query] = [numExecs, totalExecTime]
				else:
					soap_list[query] = [1, queryTime]
			elif ("QUERY" in line):
				numQueries = numQueries + 1				
				query, queryTime = processPerfLogLine(line, 38)
				totalQueryTime = totalQueryTime + int(queryTime)
				if query in query_list:
					numExecs = int(query_list[query][0]) + 1
					totalExecTime = int(query_list[query][1]) + int(queryTime)
					query_list[query] = [numExecs, totalExecTime]
					time_in_query_list[query] = int(totalExecTime)
				else:
					query_list[query] = [1, queryTime]
					time_in_query_list[query] = int(queryTime)					
			elif("Cache hit." in line):
				memcachedHits = memcachedHits + 1				
				cached_query = processMemcachedLine(line, 53)
				updateRunningTotalDictionary(cached_query, cache_list)
			elif("Cache miss." in line):
				memcachedMisses = memcachedMisses + 1
				miss = processMemcachedLine(line, 54)
				updateRunningTotalDictionary(miss, miss_list)
			elif("Cache eviction" in line):
				cacheFlushes = cacheFlushes + 1
				flush = processMemcachedLine(line, 58)
				updateRunningTotalDictionary(flush, flush_list)

	q = Counter(query_list)
	print '----------------------------------------------------'
	print '-- Input File: {0}'.format(filename)
	print '----------------------------------------------------'
	print '----- Top 10 Queries (num executions) -----'
	print '--------------------------'
	for item in q.most_common(10):
		print '{0}\n{1} executions\n{2} msec in query\n{3} avg exec time\n'.format(item[0], item[1][0], item[1][1], round((float(item[1][1])/float(item[1][0])),2))

	t = Counter(time_in_query_list)
	print '----------------------------------------------------'
	print '----- Top 10 Queries (exec time) -----'
	print '----------------------------------------------------'
	for item in t.most_common(10):
		print '{0}\n{1} msec in query\n'.format(item[0], item[1])
		
	s = Counter(soap_list)
	print '----------------------------------------------------'
	print '----- Top 10 SOAP requests (exec time) -----'
	print '----------------------------------------------------'
	for item in s.most_common(10):
		print '{0}\n{1} executions\n{2} msec in query\n{3} avg exec time\n'.format(item[0], item[1][0], item[1][1], round((float(item[1][1])/float(item[1][0])),2))

	c = Counter(cache_list)
	print '---------------------------------'
	print '-----   Top 10 Cache Hits   -----'
	print '---------------------------------'
	for item in c.most_common(10):
		print '{0}\n{1} executions\n'.format(item[0], item[1][0])
		
	m = Counter(miss_list)
	if(m):
		print '-------------------------------'
		print '-----   Cache Misses   -----'
		print '-------------------------------'
		for item in m.most_common(20):
			print '{0}\n{1} executions\n'.format(item[0], item[1][0])
		
	f = Counter(flush_list)
	if(f):
		print '-------------------------------'
		print '-----   Cache Evictions   -----'
		print '-------------------------------'
		for item in f.most_common(20):
			print '{0}\n{1} executions\n'.format(item[0], item[1][0])

	print 'Cache Flushes: {6}\nCache Misses: {0}\nCache Hits: {1}\nDistinct queries: {2}\nTotal queries: {3}\nTotal query time: {4} msec\nLines Processed: {5}\n'.format(memcachedMisses, memcachedHits, len(query_list), numQueries, totalQueryTime, linesProcessed, cacheFlushes)

	# Validate calculations
	numExecsInList = sum(int(query[0]) for query in query_list.values())
	totalTimeInList = sum(int(query[1]) for query in query_list.values())
	# numCacheHitsInList = sum(int(cache[0] for cache in cache_list.values()))

	#print '{0} execs {1} total time'.format(numExecsInList, totalTimeInList)
	if((numQueries != numExecsInList) or (totalQueryTime != totalTimeInList)):
		print '[WARNING! inconsistency in num of queries or cache hits]'

parseLog(fileToLoad)	
