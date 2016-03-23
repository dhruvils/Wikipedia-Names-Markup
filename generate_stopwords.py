#!python
import os
import io
import pickle
import operator
import optparse
from collections import Counter, defaultdict

"""
read the command line options
"""
optparser = optparse.OptionParser()
optparser.add_option("-d", "--data", dest="data_path", default="data/articles", help="Filepath of data used to generate stopwords")
optparser.add_option("-l", "--language", dest="lang", default="en", help="language of the stopwords")
optparser.add_option("-n", "--num_words", dest="num_words", default=100, type="int", help="Number of stopwords to be generated")
(opts, _) = optparser.parse_args()

def get_all_files(directory):
    relativeFileList = []
    for dirpath, dirs, files in os.walk(directory):
        relativeFileList += [ (dirpath.replace(directory, '')) + ('' if dirpath == directory else '/') + filename for filename in files]
    return relativeFileList

"""
method to generate a count of all words in all the articles
in order to get a list of most frequent stopwords in the articles

An arbitrary count of top 5000 words are chosen as stopwords but should be
modified to reduce the number of stopwords
"""
def generate_stopwords(corpus_dir, lang):
	file_dir = corpus_dir +"/" +lang
	filelist = get_all_files(file_dir)
	wordcount = defaultdict(int)
	for filename in filelist:
		f = io.open(file_dir +'/' +filename, "r", encoding = "utf-16")
		temp = Counter(f.read().split())
		for key in temp:
			wordcount[key] += temp[key]

	sorted_wordcount = sorted(wordcount.items(), key = operator.itemgetter(1), reverse = True)
	return sorted_wordcount[:opts.num_words]


stopwords = generate_stopwords(opts.data_path, opts.lang)
pickle.dump(dict(stopwords), open(opts.lang + '.pickle', 'w'))

# words = pickle.load(open('en.pickle', 'r'))
# print words