#!python
import io
import os
import chardet
import pickle
import optparse

"""
read the command line options
"""
optparser = optparse.OptionParser()
optparser.add_option("-a", "--articles", dest="articles_path", default="data/articles", help="Filepath of the articles")
optparser.add_option("-b", "--backlinks", dest="backlinks_path", default="data/backlinks", help="Filepath of the backlinks")
optparser.add_option("-l", "--language", dest="lang", default="en", help="language")
optparser.add_option("-s", "--string-edit-distance", dest="edit_dist", default=0.75, type="float", help="String edit distance to match two words (between 0 and 1)")
optparser.add_option("-w", "--stopwords", dest="stopword_file", help="Path to the stopwords pickle file")
(opts, _) = optparser.parse_args()

def get_all_files(directory):
	relativeFileList = []
	for dirpath, dirs, files in os.walk(directory):
		relativeFileList += [ (dirpath.replace(directory, '')) + ('' if dirpath == directory else '/') + filename for filename in files]
	return relativeFileList

"""
Please note, this function has been copied from: http://rosettacode.org/wiki/Levenshtein_distance#Python

Used to find the string edit distance between two strings
"""
def levenshteinDistance(str1, str2):
	m = len(str1)
	n = len(str2)
	lensum = float(m + n)
	d = []           
	for i in range(m+1):
		d.append([i])        
	del d[0][0]    
	for j in range(n+1):
		d[0].append(j)       
	for j in range(1,n+1):
		for i in range(1,m+1):
			if str1[i-1] == str2[j-1]:
				d[i].insert(j,d[i-1][j-1])           
			else:
				minimum = min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+2)         
				d[i].insert(j, minimum)
	ldist = d[-1][-1]
	ratio = (lensum - ldist)/lensum
	return {'distance':ldist, 'ratio':ratio}

"""
gather all backlinks from a folder into a single set

@param: backlinks_dirpath
	the directory containing all the files for the backlinks
@param: lang
	the language of the specified backlink folder
"""
def get_all_backlinks(backlinks_dirpath, lang):
	files = get_all_files(backlinks_dirpath +"/" +lang)
	backlink_list = []
	backlink_full = []
	count = 0

	for filename in files:
		filepath = backlinks_dirpath +"/%s/%s" %(lang, filename)
		r = chardet.detect(open(filepath).read())
		charenc = r['encoding']
		f = io.open(filepath, "r", encoding = charenc, errors = "ignore")
		backlinks = f.read()
		f.close()

		for names in backlinks.split("\n"):
			backlink_full.append(names)
			backlink_list.extend(names.split())

		# TODO remove this if you need to get the backlinks for all files
		# This limits the filecount to 12500, using the full set is very time consuming
		count += 1
		if count > 12500:
			break
	
	return (set(backlink_full), set(backlink_list))

"""
method used to mark individual words in a file as either a PERS or O (other)

Note:
	the directory path is currently mapped to my directory and will need to be
	changed in order to be used by someone else

@param article_file:
	the name of the file that needs to be marked
@param backlink_full:
	a list of backlinks containing the whole backlink (for the purpose of the first pass)
@param backlink_list:
	a list of backlink words split by spaces (for the purpose of the second pass)
@param lang:
	the language of the article
@param stopwords:
	the list of stopwords that need to be removed from consideration
"""
def markup_file(article_file, backlink_full, backlink_list, lang, stopwords):
	article_dirpath = opts.articles_path + "/%s/%s" %(lang, article_file)
	f = io.open(article_dirpath, "r", encoding = "utf-16")
	article = f.read()
	f.close()

	markup_list = []
	for words in article.split():
		markup_list.append(tuple([words, "O"]))

	markup_list = pass1(markup_list, backlink_full)
	markup_list = pass2(markup_list, backlink_list, stopwords)

	output_filepath = "data/output/%s/marked_%s" %(lang, article_file)
	d = os.path.dirname(output_filepath)

	if not os.path.exists(d):
		os.makedirs(d)

	output = open(output_filepath, "w")
	for word, mark in markup_list:
		outputstr = "\t%s\n" %(mark)
		output.write(word.encode("utf-16") +outputstr.encode("utf-16"))

	output.close()
	return True

"""
match individual words in the backlinks to the current article
do not match stopwords

@param markup_list:
	a list of tuples containing the word and its corresponding type
@param backlink_list:
	a list of backlink names used for markup
@param stopwords:
	list of stopwords that should not be marked as PERS
"""
def pass2(markup_list, backlink_list, stopwords):
	i = 0
	matched_set = set()
	unmatched_set = set()
	while i < len(markup_list):
		if not markup_list[i][1] == "PERS":
			word = markup_list[i][0]
			if word not in stopwords:
				if word in matched_set:
					markup_list[i] = tuple([word, "PERS"])
				else:
					marked = False
					if word not in unmatched_set:
						for name in backlink_list:
							if levenshteinDistance(word, name)['ratio'] > opts.edit_dist:
								markup_list[i] = tuple([word, "PERS"])
								matched_set.add(word)
								marked = True
								break
						if not marked:
							unmatched_set.add(word)
		i += 1
	return markup_list

"""
match entire backlink to the words in the document
mark individual words in the backlink as PERS iff
the whole backlink matches some portion of the document

@param markup_list:
	a list of tuples containing the word and its corresponding type
@param backlink_list:
	a list of backlink names used for markup
"""
def pass1(markup_list, backlink_list):
	i = 0
	while i < len(markup_list):
		marked = False
		for backlink in backlink_list:
			length = len(backlink.split())
			if i + length < len(markup_list):
				phrase = " ".join([w for w,m in markup_list[i:i+length]])
				if phrase == backlink:
					marked = True
					for word in phrase.split():
						markup_list[i] = tuple([word, "PERS"])
						i += 1

					break
		if not marked:
			i += 1

	return markup_list

file_count = 0
backlinks_path = opts.backlinks_path
(backlink_full, backlink_set) = get_all_backlinks(backlinks_path, opts.lang)

words = pickle.load(open(opts.stopword_file, 'r')) if not opts.stopword_file == "" else []

for filename in get_all_files(opts.articles_path + "/" + opts.lang):
	file_exists = markup_file(filename, backlink_full, backlink_set, opts.lang, words)
	if file_exists:
		file_count += 1
		if (file_count > 12500):
			break