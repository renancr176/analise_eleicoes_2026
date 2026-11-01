# Robustez do coeficiente branco/nulo -> PT: (a) separando brancos, nulos e eliminados; (b) efeito fixo de município
import numpy as np, json, sys
out = {}
for ano, fn in [(2014, 'sec_2014.npz'), (2018, 'sec_2018.npz'), (2022, 'sec_2022.npz'), (2026, 'secoes.npz')]:
    d = np.load(fn); A = d['arr'].astype(float); C = {c: i for i, c in enumerate(d['cols'])}; c = lambda n: A[:, C[n]]
    m = (c('t1_comp') > 0) & (c('t2_comp') > 0)
    L1, F1, O1 = c('t1_lula'), c('t1_flavio'), c('t1_outros'); B, Nu = c('t1_brancos'), c('t1_nulos'); AB = c('t1_aptos') - c('t1_comp')
    cols = [L1, F1]
    names = ['pt', 'adv']
    if ano == 2026:
        for k in ['t1_cury', 't1_renan', 't1_caiado', 't1_zema']: cols.append(c(k)); names.append(k[3:])
        cols.append(O1 - c('t1_cury') - c('t1_renan') - c('t1_caiado') - c('t1_zema')); names.append('resto')
    else:
        cols.append(c('t1_cury')); names.append('terceiro'); cols.append(O1 - c('t1_cury')); names.append('resto')
    cols += [B, Nu, AB]; names += ['brancos', 'nulos', 'abst']
    X = np.column_stack(cols)[m]; yL = c('t2_lula')[m]; yF = c('t2_flavio')[m]
    r = {}
    r['simples'] = {n: [round(a, 3), round(b, 3)] for n, a, b in zip(names, np.linalg.lstsq(X, yL, rcond=None)[0], np.linalg.lstsq(X, yF, rcond=None)[0])}
    # efeito fixo de município: subtrai a média do município (com intercepto implícito)
    mun = c('mun')[m].astype(np.int64); u, inv = np.unique(mun, return_inverse=True)
    def dm(v):
        s = np.bincount(inv, weights=v); n = np.bincount(inv); return v - (s / n)[inv]
    Xd = np.column_stack([dm(X[:, j]) for j in range(X.shape[1])])
    r['ef_mun'] = {n: [round(a, 3), round(b, 3)] for n, a, b in zip(names, np.linalg.lstsq(Xd, dm(yL), rcond=None)[0], np.linalg.lstsq(Xd, dm(yF), rcond=None)[0])}
    out[ano] = r
    print(ano, 'simples', r['simples']); print('     ef_mun', r['ef_mun'])
json.dump(out, open('bn_check.json', 'w'))
