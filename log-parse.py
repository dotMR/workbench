# Parse application log to count queries
# usage: python log-parse.py arg (file name to read without .in)
import operator
from collections import Counter
import sys

#initialLoadFile = "resources/" + sys.argv[1] + "-initial.in"
#refreshFile = "resources/" + sys.argv[1] + "-refresh.in"

fileToLoad = "resources/" + sys.argv[1] + ".in"

def processLogLine(line, startIndex):
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
				timeIndex = line.rfind(',')
				queryTime = line[(timeIndex+1):].rstrip()
				formatted = line[38:timeIndex]
				typeIndex = formatted.rfind(',')
				query = formatted[:typeIndex].rstrip()
				numSoapQueries = numSoapQueries + 1
				if query in soap_list:
					numExecs = int(soap_list[query][0]) + 1
					totalExecTime = int(soap_list[query][1]) + int(queryTime)
					soap_list[query] = [numExecs, totalExecTime]
				else:
					soap_list[query] = [1, queryTime]
			elif ("QUERY" in line):
				timeIndex = line.rfind(',')
				queryTime = line[(timeIndex+1):].rstrip()
				formatted = line[38:timeIndex]
				typeIndex = formatted.rfind(',')
				query = formatted[:typeIndex].rstrip()
				numQueries = numQueries + 1
				totalQueryTime = int(totalQueryTime) + int(queryTime)
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
				endDelimiterIndex = line.rfind('[')
				cached_query = line[53:endDelimiterIndex]
				cached_query.strip()
				if cached_query in cache_list:
					numExecs = int(cache_list[cached_query][0]) + 1
					cache_list[cached_query] = [numExecs]
				else:
					cache_list[cached_query] = [1]
			elif("Cache miss." in line):
				memcachedMisses = memcachedMisses + 1
				endDelimiterIndex = line.rfind('[')
				miss = line[54:endDelimiterIndex]
				miss.strip()
				if miss in miss_list:
					numExecs = int(miss_list[miss][0]) + 1
					miss_list[miss] = [numExecs]
				else:
					miss_list[miss] = [1]
			elif("Cache eviction" in line):
				cacheFlushes = cacheFlushes + 1
				endDelimiterIndex = line.rfind('[')
				flush = line[58:endDelimiterIndex]
				flush.strip()
				if flush in flush_list:
					numExecs = int(flush_list[flush][0]) + 1
					flush_list[flush] = [numExecs]
				else:
					flush_list[flush] = [1]

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

# parseLog(initialLoadFile)
# parseLog(refreshFile)
parseLog(fileToLoad)	
