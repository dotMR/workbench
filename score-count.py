# Calculate point sum and num missing for text-based answer set
# (used for validating junit test cases)
#
# input: score-to-count.in
# string list of params used in junit test-case
#
# usage: python score-count.py
from __future__ import division

with open ("resources/score-to-count.in", "r") as myfile:
    data=myfile.read().replace('\n', '')

numMissing = 0
denominator = 0
numProcessed = 0
totalScore = 0
scoreToAdd = 0
data = data.replace(" ","")
for w in data.split(','):
	numProcessed = numProcessed + 1
	denominator = denominator + 1
	scoreToAdd = 0
	if ((("_DONT_KNOW" in w) or ("_MISSING" in w) or ("null" in w))):
		numMissing = numMissing + 1

	if (("0pt" in w) or ("SCORE_ZERO" in w)):
		scoreToAdd = 0
	elif "_SCORE_ONE" in w:
		scoreToAdd = 1
	elif "_ZEROpoint5" in w:
		scoreToAdd = 0.5
	elif "_1pt" in w:
		scoreToAdd = 1
	elif "_0point1" in w:
		scoreToAdd = 0.1
	elif "_0point25" in w:
		scoreToAdd = 0.25
	elif "_0point2" in w:
		scoreToAdd = 0.2
	elif "_0point33" in w:
		scoreToAdd = 0.33
	elif "_0point3" in w:
		scoreToAdd = 0.3
	elif "_0point4" in w:
		scoreToAdd = 0.4
	elif "_0point5" in w:
		scoreToAdd = 0.5
	elif "_0point66" in w:
		scoreToAdd = 0.66
	elif "_0point6" in w:
		scoreToAdd = 0.6
	elif "_0point75" in w:
		scoreToAdd = 0.75
	elif "_0point7" in w:
		scoreToAdd = 0.7
	elif "_0point8" in w:
		scoreToAdd = 0.8
	elif "_0point9" in w:
		scoreToAdd = 0.9
	elif ((("_DONT_KNOW" in w) or ("_MISSING" in w) or ("null" in w))):
		scoreToAdd = 0
		denominator = denominator - 1
		print 'not counting {}'.format(w)
	else:
		print 'no case found for {}'.format(w)
	totalScore = totalScore + scoreToAdd

numAnswered = numProcessed - numMissing

print 'Missing: {0} of {1}\nTotal Points: {2}'.format(numMissing, numProcessed, totalScore)
print 'dividing by {0} responses'.format(denominator)
if numMissing > 13:
	print 'Score: n/a'
else:
	print 'Score {0}'.format(round((totalScore/denominator)*100))