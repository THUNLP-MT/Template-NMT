import sys
import re

hyp_cps = sys.argv[1]
out_cps = sys.argv[2]

with open(hyp_cps, 'r') as fr:
    hyp_lines = fr.readlines()

fw = open(out_cps, 'w')

hyp_lines = [l.split('[SEP]') for l in hyp_lines]

t_ptrn = re.compile(r'(\[T[0-9]+\])')
tagTypeList = ['ph', 'xref', 'uicontrol', 'b', 'codeph', 'parmname', 'i', 'title',
                'menucascade', 'varname', 'userinput', 'filepath', 'term',
                'systemoutput', 'cite', 'li', 'ul', 'p', 'note', 'indexterm', 'u', 'fn']
tagBegList = ['<'+t+'>' for t in tagTypeList]
tagEndList = ['</'+t+'>' for t in tagTypeList]
tagList = tagBegList + tagEndList

p_ood_num = 0
for idx, infos in enumerate(hyp_lines):
    assert len(infos) == 2
    t_info = infos[0]
    s_info = infos[1]
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
    for tok in t_span:
        if t_ptrn.match(tok) is not None:
            if tok in restore_dict_p:
                res.append(restore_dict_p[tok])
        else:
            assert tok in tagList
            res.append(tok)
    res = [x.strip() for x in res]
    fw.write(' '.join(res) + '\n')
fw.close()