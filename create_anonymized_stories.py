import tarfile, os, hashlib, pickle, argparse
from collections import namedtuple

questions_data_file = './questions_data.pkl'
QuestionData = namedtuple('QuestionData', 'hashed_url question_hash dataset entity_mapping')

############# map_qd #############

def map_questions_data(questions_path):
	data = {}
	questions_file = tarfile.open(questions_path)

	for i, file in enumerate(questions_file.getmembers()):
		qd = create_question_data(questions_file, file)
		if not qd: continue
		hashed_url = qd.hashed_url
		if not hashed_url in data: data[hashed_url] = {}
		data[hashed_url][qd.question_hash] = qd._asdict()
		if i%5000 == 0 and i!=0:
			print("found "+str(i)+" questions")

	write_pickle(questions_data_file, data)
	print("successfully wrote questions data.")

def create_question_data(questions_file, file):
	if not file.path.endswith('.question'): return
	splited_path = file.path.split('/')
	dataset = splited_path[3]
	question_hash = splited_path[4].split('.')[0]
	entity_mapping, hashed_url = find_entities_and_url(questions_file, file)
	if not entity_mapping:
		print("couldn't find mapping for question hash " + question_hash)
		return
	return QuestionData(hashed_url, question_hash, dataset, entity_mapping)
	
def find_entities_and_url(questions_file, filename):
	f = questions_file.extractfile(filename)
	lines = [line.strip() for line in f.readlines()]
	hashed_url = hashhex(lines[0].strip())
	mapping = {}
	for line in reversed(lines):
		try:
			key, value = line.decode().split(':', 1)
			mapping[key] = value
		except:
			break
	return mapping, hashed_url

############# anonymize #############

dm_single_close_quote = u'\u2019'
dm_double_close_quote = u'\u201d'
END_TOKENS = ['.', '!', '?', '...', "'", "`", '"', dm_single_close_quote, dm_double_close_quote, ")"] # acceptable ways to end a sentence

StoryData = namedtuple('StoryData', 'hashed_url, article, abstract, entity_mapping, questions, dataset')

def anonymize(stories_path, out_dir):
	questions_data = read_pickle(questions_data_file)
	data = {'training': [], 'validation': [], 'test': []}

	stories_file = tarfile.open(stories_path)
	i = 0
	for file_path in stories_file.getmembers():
		sd = create_story_data(stories_file, file_path, questions_data)
		if not sd: continue
		data[sd.dataset].append(sd._asdict())
		if i%1000 == 0 and i!=0:
			print("anonymized "+str(i)+" articles")
		i+=1

	anonymized_files = {'training': out_dir+'/anonymized_training.pkl', 'validation': out_dir+'/anonymized_validation.pkl', 'test': out_dir+'/anonymized_test.pkl' }
	for dataset, stories in data.items():
		write_pickle(anonymized_files[dataset], stories)
		print("successfully wrote anonymized " + dataset + " dataset.")

	os.remove(questions_data_file)

def create_story_data(stories_file, file_path, questions_data):
	if not file_path.name.endswith('story'): return
	hashed_url = file_path.name.split('/')[3].split('.')[0]
	if hashed_url not in questions_data:
		print("counldn't find questions for " + hashed_url)
		return
	qd = questions_data[hashed_url]
	questions = list(qd.keys())

	entity_mapping = qd[questions[0]]['entity_mapping']
	dataset = qd[questions[0]]['dataset']

	f = stories_file.extractfile(file_path)
	content = f.read().decode()
	original_article, original_abstract = get_art_abs(content)
	article = anonymize_story(original_article, entity_mapping)
	abstract = anonymize_story(original_abstract, entity_mapping)
	return StoryData(hashed_url, article, abstract, entity_mapping, questions, dataset)

def get_art_abs(story):
	lines = story.split('\n')

	lines = [line.lower() for line in lines]

	lines = [fix_missing_period(line) for line in lines]

	article_lines = []
	highlights = []
	next_is_highlight = False
	for idx,line in enumerate(lines):
		if line == "":
			continue # empty line
		elif line.startswith("@highlight"):
			next_is_highlight = True
		elif next_is_highlight:
			highlights.append(line)
		else:
			article_lines.append(line)

	article = ' '.join(article_lines)

	abstract = ' '.join(highlights)

	return article, abstract

def fix_missing_period(line):
  if "@highlight" in line: return line
  if line=="": return line
  if line[-1] in END_TOKENS: return line
  # print line[-1]
  return line + " ."

def anonymize_story(text, mapping):
	for e_number, e_name in mapping.items():
		text = text.replace(' '+e_name.lower()+' ', ' '+e_number+' ') #TODO, should tokenize here
		text = text.replace(' '+e_name.lower()+'\'', ' '+e_number+'\'')
	return text

def write_pickle(file, data):
	with open(file, 'wb') as f:
		pickle.dump(data, f)

def read_pickle(file):
	with open(file, 'rb') as f:
		data = pickle.loads(f.read())
	return data

def hashhex(s):
	h = hashlib.sha1()
	h.update(s)
	return h.hexdigest()

def main():
	parser = argparse.ArgumentParser(description='Map Question Data/Create Anonymized datasets')
	parser.add_argument('--mode', choices=['map_qd', 'anonymize'], required=True)
	parser.add_argument('--questions_path')
	parser.add_argument('--stories_path')
	parser.add_argument('--out_dir')
	args = parser.parse_args()
	if args.mode == 'map_qd':
		if not args.questions_path: print('--questions_path is required. Exiting.'); return
		map_questions_data(args.questions_path)
	elif args.mode == 'anonymize':
		if not args.stories_path: print('--stories_path is required. Exiting.'); return
		if not args.out_dir: print('--out_dir is required. Exiting.'); return
		anonymize(args.stories_path, args.out_dir)

if __name__ == '__main__':
  main()
