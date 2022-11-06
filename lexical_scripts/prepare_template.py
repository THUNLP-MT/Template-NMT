import sys
import re
import random


# Usage: python prepare_training_data_public.py {src_lang} {tgt_lang} {filename_prefix} {constraint_filename} {t2s | t2s.infer | t2s.orig.infer}
# t2s: prepare training data
# t2s.infer: prepare inference data
# t2s.orig.infer: prepare inference data for non-constrained translation

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


def t2s(srctext, tgttext, const_pair, inference=False):
    src_toks = srctext.split()
    tgt_toks = tgttext.split()
    src_const_list = [c.strip() for c in const_pair[::2]]
    tgt_const_list = [c.strip() for c in const_pair[1::2]]
    ood_num = 0
    index = 0
    src_const = []
    tgt_const = []
    for sc, tc in zip(src_const_list, tgt_const_list):
        sc_toks = sc.split()
        tc_toks = tc.split()
        src_match = const_finder(src_toks, sc_toks)
        tgt_match = const_finder(tgt_toks, tc_toks)
        if src_match is None or tgt_match is None:
            ood_num += 1
        else:
            src_place = src_match[0]
            tgt_place = tgt_match[0]
            ph_str = '[C{}]'.format(index)
            index += 1
            src_const = src_const + [ph_str] + sc_toks
            tgt_const = tgt_const + [ph_str] + tc_toks
            src_toks = src_toks[:src_place] + [ph_str] + src_toks[src_place + len(sc_toks):]
            tgt_toks = tgt_toks[:tgt_place] + [ph_str] + tgt_toks[tgt_place + len(tc_toks):]
    
    pattern = re.compile(r'(\[C[0-9]+?\])')
    def _build_t_and_s(p, my_list):
        template_toks = ['[{}0]'.format(p)]
        string_toks = ['[{}0]'.format(p)]
        index = 1    
        for tok in my_list:
            if pattern.match(tok) is not None:
                ph_str = '[{}{}]'.format(p, index)
                index += 1
                template_toks.append(tok)
                template_toks.append(ph_str)
                string_toks.append(ph_str)
            else:
                string_toks.append(tok)
        return template_toks, string_toks
    src_template, src_string = _build_t_and_s('S', src_toks)
    tgt_template, tgt_string = _build_t_and_s('T', tgt_toks)

    src_list = src_const + ['[SEP]'] + src_template + ['[SEP]'] + src_string
    if inference:
        if len(tgt_const) > 0:
            tgt_list = tgt_const + ['[SEP]']
        else:
            # tgt_list = ['[SEP]']
            tgt_list = ['[SEP] [T0] [SEP] [T0]']
    else:
        tgt_list = tgt_const + ['[SEP]'] + tgt_template + ['[SEP]'] + tgt_string
    return ' '.join(src_list), ' '.join(tgt_list), ood_num


def t2s_orig(srctext, tgttext, inference=False):
    if inference:
        return '[SEP] [S0] [SEP] [S0] ' + srctext, '[SEP] [T0] [SEP] [T0]'
    else:
        return '[SEP] [S0] [SEP] [S0] ' + srctext, '[SEP] [T0] [SEP] [T0] ' + tgttext


src = sys.argv[1]
tgt = sys.argv[2]
ipt_pref = sys.argv[3]
src_cps = ipt_pref + '.' + src
tgt_cps = ipt_pref + '.' + tgt
const_cps = sys.argv[4]
suffix = sys.argv[5]
res_src_cps = ipt_pref + f'.{suffix}.' + src
res_tgt_cps = ipt_pref + f'.{suffix}.' + tgt
res_src_f = open(res_src_cps, 'w')
res_tgt_f = open(res_tgt_cps, 'w')

with open(src_cps, 'r') as fr:
    src_lines = fr.readlines()
with open(tgt_cps, 'r') as fr:
    tgt_lines = fr.readlines()
with open(const_cps, 'r') as fr:
    const_lines = fr.readlines()

assert len(src_lines) == len(tgt_lines)
assert len(src_lines) == len(const_lines)

total_ood_num = 0
for i, (sl, tl, cl) in enumerate(zip(src_lines, tgt_lines, const_lines)):
    if i % 10000 == 0:
            print('Finished {} lines...'.format(i))
    srctext = sl.strip()
    tgttext = tl.strip()
    const_pair = cl.strip().split('|||')[:-1]
    assert len(const_pair) % 2 == 0
    const_pair = [x.strip() for x in const_pair]
    
    infos = 0

    if suffix == 't2s':
        res_src, res_tgt, infos = t2s(srctext, tgttext, const_pair, inference=False)
        total_ood_num += infos
    elif suffix == 't2s.infer':
        res_src, res_tgt, infos = t2s(srctext, tgttext, const_pair, inference=True)
        total_ood_num += infos
    elif suffix == 't2s.orig.infer':
        res_src, res_tgt = t2s_orig(srctext, tgttext, inference=True)

    res_src_f.write(res_src + '\n')
    res_tgt_f.write(res_tgt + '\n')

res_src_f.close()
res_tgt_f.close()
print(f"Skip {total_ood_num} Constraints")
print('Finished all lines')

