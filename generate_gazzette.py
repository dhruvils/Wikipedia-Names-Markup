#!python
import io
import os
import chardet
import optparse

"""
read the command line options
"""
optparser = optparse.OptionParser()
optparser.add_option("-b", "--backlinks", dest="backlinks_path", default="data/backlinks", help="Filepath of the backlinks")
optparser.add_option("-l", "--language", dest="lang", default="en", help="language")
(opts, _) = optparser.parse_args()

def get_all_files(directory):
    relativeFileList = []
    for dirpath, dirs, files in os.walk(directory):
        relativeFileList += [ (dirpath.replace(directory, '')) + ('' if dirpath == directory else '/') + filename for filename in files]
    return relativeFileList

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
	
	return set(backlink_full)

def write_gazzette(backlinks):
	f = open("gazzette.txt", "w")
	for backlink in backlinks:
		to_write = "PERS %s\n" %(backlink)
		f.write(to_write.encode("utf-16"))
	f.close()

backlinks_path = opts.backlinks_path
# backlinks_path = "/scratch-local/users/dhruvils/Part3-NamesMarkup/data/backlinks"
backlink_full = get_all_backlinks(backlinks_path[:12500], opts.lang)
write_gazzette(backlink_full)