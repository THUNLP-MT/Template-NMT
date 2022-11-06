import sys

tagTypeList = ['ph', 'xref', 'uicontrol', 'b', 'codeph', 'parmname', 'i', 'title',
                'menucascade', 'varname', 'userinput', 'filepath', 'term',
                'systemoutput', 'cite', 'li', 'ul', 'p', 'note', 'indexterm', 'u', 'fn']
tagBegList = ['<'+t+'>' for t in tagTypeList]
tagEndList = ['</'+t+'>' for t in tagTypeList]
tagList = tagBegList + tagEndList


def t2s(ipt_line, ph_pref):
    index = 0
    template_toks = ['[{}{}]'.format(ph_pref, index)]
    string_toks = ['[{}{}]'.format(ph_pref, index)]
    for tok in ipt_line.split():
        if tok in tagList:
            template_toks.append(tok)
            index += 1
            template_toks.append('[{}{}]'.format(ph_pref, index))
            string_toks.append('[{}{}]'.format(ph_pref, index))
        else:
            string_toks.append(tok)
    template_str = ' '.join(template_toks)
    string_str = ' '.join(string_toks)
    return f"{template_str} [SEP] {string_str}"


def template(src_line, tgt_line):
    res_src = t2s(src_line, 'S')
    res_tgt = t2s(tgt_line, 'T')
    return res_src, res_tgt


def template_inference(src_tem):
    if src_tem.startswith('[S0] [SEP] [S0]'):
        return '[T0] [SEP] [T0]'
    else:
        return '[T0]'


src = sys.argv[1]
tgt = sys.argv[2]
ipt_pref = sys.argv[3]
src_cps = ipt_pref + '.' + src
tgt_cps = ipt_pref + '.' + tgt
suffix = sys.argv[4]
res_src_cps = ipt_pref + f'.{suffix}.' + src
res_tgt_cps = ipt_pref + f'.{suffix}.' + tgt
res_src_f = open(res_src_cps, 'w')
res_tgt_f = open(res_tgt_cps, 'w')

with open(src_cps, 'r') as fr:
    src_lines = fr.readlines()
with open(tgt_cps, 'r') as fr:
    tgt_lines = fr.readlines()

assert len(src_lines) == len(tgt_lines)

for i, (sl, tl) in enumerate(zip(src_lines, tgt_lines)):
    if i % 10000 == 0:
            print('Finished {} lines'.format(i))
    srctext = sl.strip()
    tgttext = tl.strip()
    res_src, res_tgt = template(srctext, tgttext)
    if suffix == 't2s.infer':
        res_tgt = template_inference(res_src)
    res_src_f.write(res_src + '\n')
    res_tgt_f.write(res_tgt + '\n')

res_src_f.close()
res_tgt_f.close()
print('Finished All lines')