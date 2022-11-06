import re
import TER
import stanza
import string
import argparse
import sacrebleu
import TER_modified
from bs4 import BeautifulSoup
import numpy as np


def const_finder(texttoks, consttoks):
    t_len = len(texttoks)
    c_len = len(consttoks)
    if t_len < c_len:
        return None
    matches = []
    for temp_idx in range(t_len - c_len + 1):
        if texttoks[temp_idx: temp_idx + c_len] == consttoks:
            matches.append(temp_idx)
    if len(matches) == 0:
        return None
    else:
        return matches


def read_reference_data_wmt(lt, ls, lc):
	with open(lt, encoding="utf-8") as inp:
		linest = inp.readlines()
	with open(ls, encoding="utf-8") as inp:
		liness = inp.readlines()
	with open(lc, encoding="utf-8") as inp:
		linesc = inp.readlines()

	refs = {}
	sources = []
	outputs = []
	for idx in range(len(liness)):
		linet = linest[idx]
		lines = liness[idx]

		source_tokens = lines.split()
		target_tokens = linet.split()

		source = " " + " ".join(source_tokens) + " "
		target = " " + " ".join(target_tokens) + " "
		sources.append(source)
		outputs.append(target)

		terms = []
		terms_l = []

		linec = linesc[idx]
		spans = linec.split('|||')[:-1]
		assert len(spans) % 2 == 0
		spans = [x.strip() for x in spans]
		src_terms = spans[::2]
		tgt_terms = spans[1::2]

		for src_term, tgt_term in zip(src_terms, tgt_terms):
			src_term = src_term
			tgt_term = tgt_term
			src_match = const_finder(source_tokens, src_term.split())
			if src_match is None:
				print(f"{idx}\n{source}\n{linec.strip()}")
			src_ids = [src_match[0]]
			for i in range(1, len(src_term.split())):
				src_ids.append(src_ids[0] + i)
			src_ids = ','.join([str(x) for x in src_ids])

			tgt_match = const_finder(target_tokens, tgt_term.split())
			if tgt_match is None:
				print(' '.join(tgt_term.split()))
				print(' '.join(target_tokens))
			tgt_ids = [tgt_match[0]]
			for i in range(1, len(tgt_term.split())):
				tgt_ids.append(tgt_ids[0] + i)
			tgt_ids = ','.join([str(x) for x in tgt_ids])

			terms.append(f"{src_term} ||| {src_ids} --> {tgt_term} ||| {tgt_ids}")
			if SUPPORTED:
				doc_f = l2_stanza(tgt_term)
				tgt_lemma = ' ' + ' '.join([w.lemma for w in doc_f.sentences[0].words]) + ' '
				terms_l.append(f"{src_term} ||| {src_ids} --> {tgt_lemma} ||| {tgt_ids}")

		refs[str(idx)] = (source, target, terms, terms_l)

	return sources, outputs, refs

def read_outputs_wmt(f):
	with open(f) as inp:
		lines = inp.readlines()
	outputs = []
	ids = []
	for idx, line in enumerate(lines):
		ids.append(str(idx))
		outputs.append(' ' + ' '.join(line.split()) + ' ')
	return ids, outputs



def compare_EXACT(hyp, ref):
	_, _, terms, _ = ref
	count_correct = 0
	count_wrong = 0
	count_correct_l = 0
	count_wrong_l = 0

	starts = []
	for t in terms:
		orig_t = t
		t = t.split(' --> ')
		t = t[1].split(' ||| ')
		desired_list = []
		for item in t[0].split("|"):
			desired_list.append("(?= " + item + " )")
		desireds = "|".join(desired_list)

		flag = False
		for desired in desireds.split("|"):
			desired_starts = [m.start() for m in re.finditer(desired, hyp)]
			for desired_start in desired_starts:
				if desired_start not in starts:
					starts.append(desired_start)
					flag = True
					break
		if not flag:
			print("{}\n{}\n\n".format(orig_t.strip(), hyp.strip()))
			count_wrong += 1
		else:
			count_correct += 1

	for t in terms:
		t = t.split(' --> ')
		t = t[1].split(' ||| ')
		tgt_c_tok = t[0].strip().split()
		success = True
		for tt in tgt_c_tok:
			if f' {tt} ' not in hyp:
				success = False
				break
		if success:
			count_correct_l += 1
		else:
			count_wrong_l += 1

	return count_correct, count_wrong, count_correct_l, count_wrong_l

def compare_TER_w(hyp, ref, lc):
	source, reference, terms, _ = ref
	ter = 0
	term_ids = []
	for t in terms:
		t = t.split(' --> ')
		t = t[1].split(' ||| ')
		term_ids.extend(t[1].split(','))
	ter += TER_modified.ter(hyp.split(), reference.split(), lc, term_ids)
					
	return ter

def compare_exact_window_overlap(hyp, ref, window):
	source, reference, terms, terms_l = ref
	accuracy = 0.0
	matched = 0

	hyp_tokens = hyp.strip().split()
	if not hyp_tokens:
		return 0.0
	reference_tokens = reference.strip().split()
	desireds = {}
	for t in terms:
		t = t.split(' --> ')
		t = t[1].split(' ||| ')
		desired  = " " + t[0].strip() + " "
		desiredindxs = [(int)(item)for item in t[1].split(",")]
		if desired in desireds:
			desireds[desired].append(desiredindxs)
		else:
			desireds[desired] = [desiredindxs]
	for desired in desireds:
		fts = [m.start() for m in re.finditer(f"(?={desired})", hyp)]
		accs = {}
		for j, listfs in enumerate(desireds[desired]):
			ref_words = []
			for win in range(min(listfs) - 1, -1, -1):
				if reference_tokens[win] not in string.punctuation:
					ref_words.append(reference_tokens[win])
					if len(ref_words) == window:
						break
			ref_wordsr = []
			for win in range(max(listfs) + 1, len(reference_tokens), 1):
				if reference_tokens[win] not in string.punctuation:
					ref_wordsr.append(reference_tokens[win])
					if len(ref_wordsr) == window:
						break
			ref_words.extend(ref_wordsr)
			for k, ft in enumerate(fts):
				cntfts = hyp.count(" ", 0, ft)
				listft = [item for item in range(cntfts, cntfts + len(desired.strip().split()))]
				hyp_words = []
				for win in range(min(listft) - 1, -1, -1):
					if hyp_tokens[win] not in string.punctuation:
						hyp_words.append(hyp_tokens[win])
						if len(hyp_words) == window:
							break
				hyp_wordsr = []
				for win in range(max(listft) + 1, len(hyp_tokens), 1):
					if hyp_tokens[win] not in string.punctuation:
						hyp_wordsr.append(hyp_tokens[win])
						if len(hyp_wordsr) == window:
							break
				hyp_words.extend(hyp_wordsr)
				cnt = 0
				for ref_word in ref_words:
					if ref_word in hyp_words:
						cnt += 1
						hyp_words.remove(ref_word)
				accs[f"{j}-{k}"] = cnt / len(ref_words) if len(ref_words) != 0 else + 0
		accs = dict(sorted(accs.items(), key=lambda item: item[1], reverse=True))
		mapped_ref = []
		mapped_hyp = []
		for acc in accs:
			if acc.split("-")[0] not in mapped_ref and acc.split("-")[1] not in mapped_hyp:
				mapped_ref.append(acc.split("-")[0])
				mapped_hyp.append(acc.split("-")[1])
				matched += 1
				accuracy += accs[acc]

	if SUPPORTED and terms_l:
		doc_f = l2_stanza(hyp)
		hyp = ' ' + ' '.join([w.lemma for w in doc_f.sentences[0].words]) + ' '
		doc_f = l2_stanza(reference)
		reference = ' ' + ' '.join([w.lemma for w in doc_f.sentences[0].words]) + ' '
		hyp_tokens = hyp.strip().split()
		reference_tokens = reference.strip().split()
		desireds = {}
		for t in terms_l:
			t = t.split(' --> ')
			t = t[1].split(' ||| ')
			desired  = " " + t[0].strip() + " "
			desiredindxs = [(int)(item)for item in t[1].split(",")]
			if desired in desireds:
				desireds[desired].append(desiredindxs)
			else:
				desireds[desired] = [desiredindxs]
		for desired in desireds:
			fts = [m.start() for m in re.finditer(f"(?={desired})", hyp)]
			accs = {}
			for j, listfs in enumerate(desireds[desired]):
				ref_words = []
				for win in range(min(listfs) - 1, -1, -1):
					if reference_tokens[win] not in string.punctuation:
						ref_words.append(reference_tokens[win])
						if len(ref_words) == window:
							break
				ref_wordsr = []
				for win in range(max(listfs) + 1, len(reference_tokens), 1):
					if reference_tokens[win] not in string.punctuation:
						ref_wordsr.append(reference_tokens[win])
						if len(ref_wordsr) == window:
							break
				ref_words.extend(ref_wordsr)
				for k, ft in enumerate(fts):
					cntfts = hyp.count(" ", 0, ft)
					listft = [item for item in range(cntfts, cntfts + len(desired.strip().split()))]
					hyp_words = []
					for win in range(min(listft) - 1, -1, -1):
						if hyp_tokens[win] not in string.punctuation:
							hyp_words.append(hyp_tokens[win])
							if len(hyp_words) == window:
								break
					hyp_wordsr = []
					for win in range(max(listft) + 1, len(hyp_tokens), 1):
						if hyp_tokens[win] not in string.punctuation:
							hyp_wordsr.append(hyp_tokens[win])
							if len(hyp_wordsr) == window:
								break
					hyp_words.extend(hyp_wordsr)
					cnt = 0
					for ref_word in ref_words:
						if ref_word in hyp_words:
							cnt += 1
							hyp_words.remove(ref_word)
					accs[f"{j}-{k}"] = cnt / len(ref_words) if len(ref_words) != 0 else + 0
			accs = dict(sorted(accs.items(), key=lambda item: item[1], reverse=True))
			mapped_ref = []
			mapped_hyp = []
			for acc in accs:
				if acc.split("-")[0] not in mapped_ref and acc.split("-")[1] not in mapped_hyp:
					mapped_ref.append(acc.split("-")[0])
					mapped_hyp.append(acc.split("-")[1])
					matched += 1
					accuracy += accs[acc]

	return accuracy / matched if matched > 0 else 0



def exact_match(l2, references, outputs, ids, LOG):
	correct = 0
	wrong = 0
	correctl = 0
	wrongl = 0
	for i, id in enumerate(ids):
		if id in references:
			c, w, cl, wl = compare_EXACT(outputs[i], references[id])
			correct += c
			wrong += w
			correctl += cl
			wrongl += wl

	print(f"Exact-Match Statistics")
	print(f"\tTotal correct (span): {correct}")
	print(f"\tTotal wrong (span): {wrong}")
	print(f"\tTotal correct (word): {correctl}")
	print(f"\tTotal wrong (word): {wrongl}")
	print(f"CSR at word-level: {(correctl) / (correctl + wrongl)}")
	print(f"Exact-Match Accuracy: {(correct) / (correct + wrong)}")
	with open(LOG, 'a') as op:
		op.write(f"Exact-Match Statistics\n")
		op.write(f"\tTotal correct: {correct}\n")
		op.write(f"\tTotal wrong: {wrong}\n")
		op.write(f"\tTotal correct (lemma): {correctl}\n")
		op.write(f"\tTotal wrong (lemma): {wrongl}\n")
		op.write(f"Exact-Match Accuracy: {(correct + correctl) / (correct + correctl + wrong + wrongl)}\n")

def comet(l2, sources, outputs, references, LOG):
	from comet.models import download_model
	model = download_model("wmt-large-da-estimator-1719", "comet_models/")
	#references = [references
	data = {"src": sources, "mt": outputs, "ref": references}
	print(data['src'][:10])
	print(data['mt'][:10])
	print(data['ref'][:10])
	data = [dict(zip(data, t)) for t in zip(*data.values())]
	temp = model.predict(data, cuda=False, show_progress=True)
	comet_score = np.mean(temp[1])
	print(f"All comment values: {temp[1]}\n")
	print(f"COMET score: {comet_score}\n")
	with open(LOG, 'a') as op:
		op.write(f"All comment values: {temp[1]}\n")
		op.write(f"COMET score: {comet_score}\n")


def bleu(l2, references, outputs, LOG):
	references = [references]
	bleu_score = sacrebleu.corpus_bleu(outputs, references)
	print(f"BLEU score: {bleu_score.score}")
	with open(LOG, 'a') as op:
		op.write(f"BLEU score: {bleu_score.score}\n")


def ter_w_shift(l2, references, outputs, IDS_to_exclude=[], LOG=None):
	ter = 0
	cnt = 0
	for i in range(len(outputs)):
		if i in IDS_to_exclude:
			continue
		ter += TER.ter(outputs[i].split(), references[i].split())
		cnt += 1
	print(f"1 - TER Score: {1 - (ter / cnt)}")
	with open(LOG, 'a') as op:
		op.write(f"1 - TER Score: {1 - (ter / cnt)}\n")


def mod_ter_w_shift(l2, references, outputs, nonreferences, ids, lc, IDS_to_exclude=[], LOG=''):
	ter = 0.0
	for i, sid in enumerate(ids):
		if i in IDS_to_exclude:
			continue
		if sid in references:
			ter += compare_TER_w(outputs[i], references[sid], lc)
		else:
			ter += TER_modified.ter(outputs[i].split(), nonreferences[i].split(), lc)
		
	print(f"1 - TERm Score: {1 - (ter / len(ids))}")
	with open(LOG, 'a') as op:
		op.write(f"1 - TER Score: {1 - (ter / len(ids))}\n")


def exact_window_overlap_match(l2, references, outputs, ids, window, LOG):
	acc = 0.0
	for i, id in enumerate(ids):
		if id in references:
			if outputs[i] != "":
				acc1 = compare_exact_window_overlap(outputs[i], references[id], window)
			acc += acc1
	
	print(f"\tExact Window Overlap Accuracy: {acc / (len(references))}")
	with open(LOG, 'a') as op:
		op.write(f"\tExact Window Overlap Accuracy: {acc / (len(references))}")



parser = argparse.ArgumentParser()
parser.add_argument("--language", help="target language", type=str, default="")
parser.add_argument("--hypothesis", help="hypothesis file", type=str, default="")
parser.add_argument("--source", help="directory where source side sgm file is located", type=str, default="")
parser.add_argument("--target_reference", help="directory where target side sgm file is located", type=str, default="")
parser.add_argument("--const", help="", type=str, default="")
parser.add_argument("--log", help="to write all outputs", type=str, default="log.txt")
parser.add_argument("--BLEU", help="", type=str, default="False")
parser.add_argument("--COMET", help="", type=str, default="False")
parser.add_argument("--EXACT_MATCH", help="", type=str, default="True")
parser.add_argument("--WINDOW_OVERLAP", help="", type=str, default="True")
parser.add_argument("--MOD_TER", help="", type=str, default="True")
parser.add_argument("--TER", help="", type=str, default="False")
args = parser.parse_args()

l2 = args.language
windows = [2]

LOG = args.log

SUPPORTED = False
try:
	stanza.download(l2, processors='tokenize,pos,lemma,depparse')
	l2_stanza = stanza.Pipeline(processors='tokenize,pos,lemma,depparse', lang=l2, use_gpu=True, tokenize_pretokenized=True)
	SUPPORTED = True
except:
	print(f"Language {l2} does not seem to be supported by Stanza -- or something went wrong with downloading the models.")
	print(f"Will continue without searching over lemmatized versions of the data.")
	SUPPORTED = False

ids, outputs = read_outputs_wmt(args.hypothesis)
if True:
	sources, sentreferences, exactreferences = read_reference_data_wmt(args.target_reference, args.source, args.const)
	if args.BLEU == "True":
		bleu(l2, sentreferences, outputs, LOG)
	if args.COMET == "True":
		comet(l2, sources, outputs, sentreferences, LOG)
	if args.EXACT_MATCH == "True":
		exact_match(l2, exactreferences, outputs, ids, LOG)
	if args.WINDOW_OVERLAP == "True":
		print("Window Overlap Accuracy :")
		with open(LOG, 'a') as op:
			op.write("Window Overlap Accuracy :\n")
		for window in windows:
			print(f"\tWindow {window}:")
			with open(LOG, 'a') as op:
				op.write("Window Overlap Accuracy :\n")
			exact_window_overlap_match(l2, exactreferences, outputs, ids, window, LOG)
	if args.MOD_TER == "True":
		mod_ter_w_shift(l2, exactreferences, outputs, sentreferences, ids, 2, [], LOG)
	if args.TER == "True":
		ter_w_shift(l2, sentreferences, outputs)
