#! python

import os
import optparse

"""
read the command line options
"""
optparser = optparse.OptionParser()
optparser.add_option("-t", "--test", dest="test", default="test", help="Test directory")
optparser.add_option("-p", "--prop-file", dest="properties", help="Name of the properties file to train classifier")
(opts, _) = optparser.parse_args()

def get_all_files(directory):
	relativeFileList = []
	for dirpath, dirs, files in os.walk(directory):
		relativeFileList += [ (dirpath.replace(directory, '')) + ('' if dirpath == directory else '/') + filename for filename in files]
	return relativeFileList

def train_classifier():
	command = "(java -cp stanford-ner/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -prop %s)" %(opts.properties)
	os.system(command)

def run_classifier(directory):
	filelist = get_all_files(directory)

	for filename in filelist:
		command = "(java -cp stanford-ner/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier ner-model.ser.gz -inputEncoding utf-16 -testFile %s > output-gaz/classified_%s)" %(opts.test + "/" + filename, filename)
		os.system(command)

train_classifier()
run_classifier(opts.test)