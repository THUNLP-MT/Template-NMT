import sys
import re

ref_cps = sys.argv[1]
hyp_cps = sys.argv[2]
out_cps = sys.argv[3]

with open(ref_cps, 'r') as fr:
	ref_lines = fr.readlines()

with open(hyp_cps, 'r') as fr:
	hyp_lines = fr.readlines()

fw = open(out_cps, 'w')

ref_lines = [l.split('[SEP]') for l in ref_lines]
hyp_lines = [l.split('[SEP]') for l in hyp_lines]

c_ptrn = re.compile(r'(\[C[0-9]+?\])')
t_ptrn = re.compile(r'(\[T[0-9]+?\])')

p_ood_num = 0
for idx, (r_infos, infos) in enumerate(zip(ref_lines, hyp_lines)):
	c_info = r_infos[0]
	assert len(infos) == 3
	t_info = infos[1]
	s_info = infos[2]
	spans = c_ptrn.split(c_info)
	assert len(spans) % 2 == 1
	restore_dict = {}
	restore_dict_str = ''
	if len(spans) > 1:
		keys = spans[1::2]
		values = spans[2::2]
		for k, v in zip(keys, values):
			restore_dict[k] = v.strip()
			restore_dict_str += '{}: {}\t'.format(k, v)
	t_span = t_info.split()
	s_span = s_info.split()
	restore_dict_p = {}
	cur_p = None
	for tok in s_span:
		if t_ptrn.match(tok) is not None:
			cur_p = tok
			restore_dict_p[cur_p] = ''
		else:
			restore_dict_p[cur_p] = restore_dict_p[cur_p] + ' ' + tok

	res = []
	for c_key in restore_dict:
		assert c_key in t_span
	for t_key in restore_dict_p:
		assert t_key in t_span
	for tok in t_span:
		if c_ptrn.match(tok) is not None:
			assert tok in restore_dict
			res.append(restore_dict[tok])
		elif t_ptrn.match(tok) is not None:
			if tok in restore_dict_p:
				if restore_dict_p[tok].endswith('@@'):
					restore_dict_p[tok] = restore_dict_p[tok][:-2]
				res.append(restore_dict_p[tok])
	res = [x.strip() for x in res]
	fw.write(' '.join(res) + '\n')
