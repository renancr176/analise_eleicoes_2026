# Cruzamento entre eleições (2014, 2018, 2022, 2026) por município e resumo comparável por ano
# Uso: python -P cross.py <pasta_scratch> saida.json
import sys, os, json
import numpy as np

base = sys.argv[1]
ANOS = {2014: 'sec_2014.npz', 2018: 'sec_2018.npz', 2022: 'sec_2022.npz', 2026: 'secoes.npz'}
REG = {'N': 'AC AM AP PA RO RR TO', 'NE': 'AL BA CE MA PB PE PI RN SE', 'CO': 'DF GO MS MT',
       'SE': 'ES MG RJ SP', 'S': 'PR RS SC', 'EXT': 'ZZ'}
UF2REG = {u: r for r, us in REG.items() for u in us.split()}

mun = {}
for ano, fn in ANOS.items():
    d = np.load(os.path.join(base, fn))
    A = d['arr']; C = {c: i for i, c in enumerate(d['cols'])}
    names = {int(c): (str(u), str(n)) for c, u, n in zip(d['mun_codes'], d['mun_uf'], d['mun_nome'])}
    m = A[:, C['mun']]
    cols = ['t1_lula', 't1_flavio', 't1_outros', 't2_lula', 't2_flavio', 't1_comp', 't2_comp', 't1_aptos',
            't1_brancos', 't1_nulos', 't2_brancos', 't2_nulos']
    order = np.argsort(m, kind='stable'); ms = m[order]
    u, st = np.unique(ms, return_index=True)
    sums = np.add.reduceat(A[order][:, [C[c] for c in cols]], st, axis=0)
    mun[ano] = {int(k): dict(zip(cols, map(int, row))) for k, row in zip(u, sums)}
    for k in mun[ano]: mun[ano][k]['uf'], mun[ano][k]['nome'] = names.get(k, ('', ''))

def share2(r):  # % PT no 2º turno sobre válidos
    v = r['t2_lula'] + r['t2_flavio']; return r['t2_lula'] / v if v else np.nan
def share1(r):
    v = r['t1_lula'] + r['t1_flavio']; return r['t1_lula'] / v if v else np.nan

out = {'pares': {}}
for a, b in [(2014, 2018), (2018, 2022), (2022, 2026)]:
    ks = [k for k in mun[a] if k in mun[b] and mun[a][k]['t2_lula'] + mun[a][k]['t2_flavio'] >= 500
          and mun[b][k]['t2_lula'] + mun[b][k]['t2_flavio'] >= 500 and mun[b][k]['uf'] != 'ZZ']
    x = np.array([share2(mun[a][k]) for k in ks]); y = np.array([share2(mun[b][k]) for k in ks])
    w = np.array([mun[b][k]['t2_lula'] + mun[b][k]['t2_flavio'] for k in ks], float)
    # regressão y = α + β x ponderada pelo tamanho
    X = np.column_stack([np.ones_like(x), x]) * np.sqrt(w)[:, None]
    coef, *_ = np.linalg.lstsq(X, y * np.sqrt(w), rcond=None)
    res = y - (coef[0] + coef[1] * x)
    res = res - np.median(res)  # centra (a regressão ponderada é dominada pelas capitais)
    sw = y - x
    r = dict(n=len(ks), corr=float(np.corrcoef(x, y)[0, 1]), alpha=float(coef[0]), beta=float(coef[1]),
             swing_medio=float(np.average(sw, weights=w)), swing_dp=float(np.sqrt(np.average((sw - np.average(sw, weights=w)) ** 2, weights=w))),
             swing_dp_simples=float(np.std(sw)), resid_dp=float(np.std(res)),
             hist=np.histogram(np.clip(sw * 100, -29.99, 29.99), bins=np.arange(-30, 31, 1))[0].tolist())
    # por UF
    r['uf'] = {}
    for uf in sorted({mun[b][k]['uf'] for k in ks}):
        kk = [i for i, k in enumerate(ks) if mun[b][k]['uf'] == uf]
        r['uf'][uf] = dict(swing=float(np.average(sw[kk], weights=w[kk])), dp=float(np.std(sw[kk])), n=len(kk))
    if (a, b) == (2022, 2026):
        # amostra para dispersão: todos os municípios (x, y em %, tamanho, região)
        r['pts'] = [[round(float(x[i]) * 100, 1), round(float(y[i]) * 100, 1), int(w[i]), UF2REG.get(mun[b][k]['uf'], '?')] for i, k in enumerate(ks)]
        idx = np.argsort(res)
        fmt = lambda i: dict(mun=mun[b][ks[i]]['nome'], uf=mun[b][ks[i]]['uf'], s_a=round(float(x[i]) * 100, 1), s_b=round(float(y[i]) * 100, 1),
                             resid=round(float(res[i]) * 100, 1), votos=int(w[i]),
                             comp_a=mun[a][ks[i]]['t2_comp'], comp_b=mun[b][ks[i]]['t2_comp'])
        big = [i for i in idx if w[i] >= 2000]
        r['top_neg'] = [fmt(i) for i in big[:15]]; r['top_pos'] = [fmt(i) for i in big[::-1][:15]]
        s = np.median(np.abs(res)) * 1.4826
        r['resid_mad'] = float(s); r['resid_z4_pos'] = int((res > 4 * s).sum()); r['resid_z4_neg'] = int((res < -4 * s).sum())
        r['resid_z4'] = r['resid_z4_pos'] + r['resid_z4_neg']
    out['pares'][f'{a}-{b}'] = r

# virada 1º→2º turno por município, cada ano
out['virada_mun'] = {}
for ano in ANOS:
    ks = [k for k, r in mun[ano].items() if r['t2_lula'] + r['t2_flavio'] >= 500 and r['uf'] != 'ZZ']
    s = np.array([share2(mun[ano][k]) - share1(mun[ano][k]) for k in ks]) * 100
    out['virada_mun'][ano] = dict(media=float(np.mean(s)), dp=float(np.std(s)), p05=float(np.percentile(s, 5)), p95=float(np.percentile(s, 95)),
                                  pct_pro_pt=float((s > 0).mean() * 100),
                                  hist=np.histogram(np.clip(s, -19.99, 19.99), bins=np.arange(-20, 20.5, 0.5))[0].tolist())

# comparecimento por região e ano
out['comp_reg'] = {}
for ano in ANOS:
    out['comp_reg'][ano] = {}
    for rg in ['N', 'NE', 'CO', 'SE', 'S', 'EXT']:
        rs = [r for r in mun[ano].values() if UF2REG.get(r['uf']) == rg]
        c1 = sum(r['t1_comp'] for r in rs); c2 = sum(r['t2_comp'] for r in rs); ap = sum(r['t1_aptos'] for r in rs)
        out['comp_reg'][ano][rg] = dict(c1=c1, c2=c2, aptos=ap)

json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
for k, v in out['pares'].items(): print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if not isinstance(vv, (list, dict))})
for k, v in out['virada_mun'].items(): print(k, {kk: round(vv, 3) for kk, vv in v.items() if kk != 'hist'})
for ano, v in out['comp_reg'].items(): print(ano, {r: round(100 * (x['c2'] - x['c1']) / max(x['aptos'], 1), 2) for r, x in v.items()})
