# Parse application log to count queries
# usage: python log-parse.py
import operator
from collections import Counter

numQueries = 0
linesProcessed = 0
totalQueryTime = 0
query_list = dict()

with open ("resources/wbc-login.in", "r") as f:
    for line in f:
		linesProcessed = linesProcessed + 1
		if ("QUERY" in line):
			timeIndex = line.rfind(',')
			queryTime = line[(timeIndex+1):]
			formatted = line[20:timeIndex]
			typeIndex = formatted.rfind(',')
			query = formatted[:typeIndex].rstrip()
			print '{0}\ntime:{1}'.format(query, queryTime)
			numQueries = numQueries + 1
			totalQueryTime = int(totalQueryTime) + int(queryTime)
			if query in query_list:
				numExecs = int(query_list[query][0]) + 1
				totalExecTime = int(query_list[query][1]) + int(queryTime)
				query_list[query] = [numExecs, totalExecTime]
			else:
				query_list[query] = [1, queryTime]
	
c = Counter(query_list)
print '--------------------------'
print '----- Top 10 Queries -----'
print '--------------------------'
for item in c.most_common(10):
	print '{0}\n{1} executions\n{2} msec in query\n{3} avg exec time\n'.format(item[0], item[1][0], item[1][1], round((float(item[1][1])/float(item[1][0])),2))

print 'Distinct queries: {0}\nTotal queries: {1}\nTotal query time: {2} msec\nLines Processed: {3}'.format(len(query_list), numQueries, totalQueryTime, linesProcessed)

# Validate calculations
numExecsInList = sum(int(query[0]) for query in query_list.values())
totalTimeInList = sum(int(query[1]) for query in query_list.values())

#print '{0} execs {1} total time'.format(numExecsInList, totalTimeInList)
if((numQueries != numExecsInList) or (totalQueryTime != totalTimeInList)):
	print '[WARNING! numQueries is not equal to the number of values]'
