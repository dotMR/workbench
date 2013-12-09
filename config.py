# 'global' variables for use in log-parse.py
numQueries = 0
linesProcessed = 0
totalQueryTime = 0
memcachedHits = 0
memcachedMisses = 0
memcachedEvictions = 0
numSoapQueries = 0

soap_list = dict()
query_list = dict()
time_in_query_list = dict()
cache_list = dict()
miss_list = dict()
evict_list = dict()
