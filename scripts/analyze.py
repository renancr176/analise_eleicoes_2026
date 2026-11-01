# Análises estatísticas por seção - presidente 2026 (1º x 2º turno)
# Uso: python -P analyze.py secoes.npz saida.json
import sys, json
import numpy as np

d = np.load(sys.argv[1], allow_pickle=False)
A = d['arr']; cols = list(d['cols']); C = {c: i for i, c in enumerate(cols)}
UFS = list(d['ufs']); MODELOS = list(d['modelos'])
MUN = {int(c): (str(u), str(n)) for c, u, n in zip(d['mun_codes'], d['mun_uf'], d['mun_nome'])}
col = lambda n: A[:, C[n]]
REG = {'N': 'AC AM AP PA RO RR TO', 'NE': 'AL BA CE MA PB PE PI RN SE', 'CO': 'DF GO MS MT',
       'SE': 'ES MG RJ SP', 'S': 'PR RS SC', 'EXT': 'ZZ'}
UF2REG = {u: r for r, us in REG.items() for u in us.split()}
uf = np.array([UFS[i] for i in col('uf')])
reg = np.array([UF2REG.get(u, '?') for u in uf])
out = {}

L1, F1, O1 = col('t1_lula'), col('t1_flavio'), col('t1_outros')
L2, F2 = col('t2_lula'), col('t2_flavio')
B1 = col('t1_brancos') + col('t1_nulos'); B2 = col('t2_brancos') + col('t2_nulos')
AP1, AP2, CP1, CP2 = col('t1_aptos'), col('t2_aptos'), col('t1_comp'), col('t2_comp')
AB1, AB2 = AP1 - CP1, AP2 - CP2

def tot(m=None):
    m = np.ones(len(A), bool) if m is None else m
    s = lambda x: int(x[m].sum())
    return dict(lula1=s(L1), flavio1=s(F1), outros1=s(O1), cury=s(col('t1_cury')), renan=s(col('t1_renan')),
                caiado=s(col('t1_caiado')), zema=s(col('t1_zema')), bn1=s(B1), brancos1=s(col('t1_brancos')),
                nulos1=s(col('t1_nulos')), comp1=s(CP1), aptos1=s(AP1),
                lula2=s(L2), flavio2=s(F2), bn2=s(B2), brancos2=s(col('t2_brancos')), nulos2=s(col('t2_nulos')),
                comp2=s(CP2), aptos2=s(AP2), secoes=int(m.sum()))

out['nacional'] = tot()
out['nacional']['secoes_t1'] = int((CP1 > 0).sum()); out['nacional']['secoes_t2'] = int((CP2 > 0).sum())

# ---------- por UF ----------
out['uf'] = []
for u in sorted(set(uf)):
    t = tot(uf == u); t['uf'] = u; t['regiao'] = UF2REG.get(u, '?'); out['uf'].append(t)
out['regiao'] = []
for r in REG:
    t = tot(reg == r); t['regiao'] = r; out['regiao'].append(t)

# ---------- seções presentes nos dois turnos ----------
both = (CP1 > 0) & (CP2 > 0)
out['pareamento'] = dict(ambos=int(both.sum()), so_t1=int(((CP1 > 0) & (CP2 == 0)).sum()),
                         so_t2=int(((CP1 == 0) & (CP2 > 0)).sum()),
                         aptos_diferentes=int((both & (AP1 != AP2)).sum()),
                         aptos_dif_abs=int(np.abs(AP1 - AP2)[both].sum()))
dL, dF = (L2 - L1), (F2 - F1)
out['perdas'] = dict(
    secoes_flavio_perdeu=int((both & (dF < 0)).sum()), votos_flavio_perdeu=int(-dF[both & (dF < 0)].sum()),
    secoes_lula_perdeu=int((both & (dL < 0)).sum()), votos_lula_perdeu=int(-dL[both & (dL < 0)].sum()),
    secoes_lula_ganhou_mais_que_pool=int((both & (dL > O1 + np.maximum(0, CP2 - CP1) + np.maximum(0, B1 - B2))).sum()),
    secoes_flavio_ganhou_mais_que_pool=int((both & (dF > O1 + np.maximum(0, CP2 - CP1) + np.maximum(0, B1 - B2))).sum()))

# ---------- regressão ecológica (Goodman) - matriz de transição ----------
def goodman(m):
    X = np.column_stack([L1, F1, O1, B1, AB1])[m].astype(float)
    res = {}
    for name, y in [('lula2', L2), ('flavio2', F2), ('bn2', B2), ('abst2', AB2)]:
        coef, *_ = np.linalg.lstsq(X, y[m].astype(float), rcond=None)
        res[name] = [round(float(c), 4) for c in coef]
    return res
out['goodman'] = {'BR': goodman(both)}
for r in ['N', 'NE', 'CO', 'SE', 'S']:
    out['goodman'][r] = goodman(both & (reg == r))
out['goodman_uf'] = {}
for u in sorted(set(uf)):
    m = both & (uf == u)
    if m.sum() > 200: out['goodman_uf'][u] = goodman(m)

# ---------- distribuição da % Lula por seção ----------
v1 = L1 + F1 + O1; v2 = L2 + F2
def hist(x, w, bins):
    h, _ = np.histogram(x, bins=bins, weights=w); return h.tolist()
bins = np.linspace(0, 1, 101)
m1 = v1 >= 20; m2 = v2 >= 20
out['hist_share'] = dict(t1_lula=hist(L1[m1] / v1[m1], None, bins), t1_flavio=hist(F1[m1] / v1[m1], None, bins),
                         t2_lula=hist(L2[m2] / v2[m2], None, bins))
# seções com 100% dos válidos
def unan(L, F, v, m):
    mm = m & (v > 0)
    return dict(lula=int((mm & (L == v)).sum()), flavio=int((mm & (F == v)).sum()),
                lula_votos=int(L[mm & (L == v)].sum()), flavio_votos=int(F[mm & (F == v)].sum()))
out['unanimes'] = dict(t2=unan(L2, F2, v2, CP2 > 0), t1=unan(L1, F1, v1, CP1 > 0),
                       t2_ge50=unan(L2, F2, v2, v2 >= 50))
lst = []
for i in np.where((v2 > 0) & ((L2 == v2) | (F2 == v2)))[0]:
    lst.append(dict(uf=str(uf[i]), mun=MUN.get(int(A[i, C['mun']]), ('', ''))[1], zona=int(A[i, C['zona']]),
                    secao=int(A[i, C['secao']]), aptos=int(AP2[i]), comp=int(CP2[i]), lula=int(L2[i]), flavio=int(F2[i]),
                    bn=int(B2[i]), lula1=int(L1[i]), flavio1=int(F1[i]), outros1=int(O1[i])))
lst.sort(key=lambda x: -(x['lula'] + x['flavio']))
out['unanimes_lista'] = lst
out['unanimes_regiao'] = {r: unan(L2, F2, v2, (CP2 > 0) & (reg == r)) for r in REG}

# ---------- swing por seção (bipartidário) e outliers robustos ----------
s1 = np.where(L1 + F1 > 0, L1 / np.maximum(L1 + F1, 1), np.nan)
s2 = np.where(v2 > 0, L2 / np.maximum(v2, 1), np.nan)
sw = s2 - s1
ms = both & (L1 + F1 >= 30) & (v2 >= 30)
out['hist_swing'] = dict(edges=np.linspace(-0.3, 0.3, 61).round(3).tolist(),
                         counts=hist(np.clip(sw[ms], -0.2999, 0.2999), None, np.linspace(-0.3, 0.3, 61)))
out['swing_stats'] = dict(media=float(np.nanmean(sw[ms])), mediana=float(np.nanmedian(sw[ms])), dp=float(np.nanstd(sw[ms])),
                          p01=float(np.nanpercentile(sw[ms], 1)), p99=float(np.nanpercentile(sw[ms], 99)))
# resíduo em relação à mediana do município
mun = col('mun')
idx = np.where(ms)[0]
order = idx[np.argsort(mun[idx], kind='stable')]
mu, starts = np.unique(mun[order], return_index=True)
resid = np.full(len(A), np.nan); munmed = np.full(len(A), np.nan)
for k in range(len(mu)):
    seg = order[starts[k]: starts[k + 1] if k + 1 < len(mu) else len(order)]
    if len(seg) < 5: continue
    med = np.median(sw[seg]); resid[seg] = sw[seg] - med; munmed[seg] = med
mr = ~np.isnan(resid)
mad = np.median(np.abs(resid[mr])) * 1.4826
z = resid / mad
out['outliers_cfg'] = dict(mad=float(mad), n=int(mr.sum()), z4=int((np.abs(z[mr]) > 4).sum()), z6=int((np.abs(z[mr]) > 6).sum()),
                           z4_pro_lula=int((z[mr] > 4).sum()), z4_pro_flavio=int((z[mr] < -4).sum()),
                           esperado_normal_z4=float(mr.sum() * 6.3e-5))
zh, _ = np.histogram(np.clip(z[mr], -10, 9.999), bins=np.arange(-10, 10.5, 0.5))
out['hist_z'] = dict(edges=np.arange(-10, 10.5, 0.5).tolist(), counts=zh.tolist())
top = np.where(mr)[0][np.argsort(-np.abs(z[mr]))][:40]
out['outliers'] = [dict(uf=str(uf[i]), mun=MUN.get(int(mun[i]), ('', ''))[1], zona=int(A[i, C['zona']]), secao=int(A[i, C['secao']]),
                        z=round(float(z[i]), 1), sw=round(float(sw[i]) * 100, 1), munmed=round(float(munmed[i]) * 100, 1),
                        lula1=int(L1[i]), flavio1=int(F1[i]), outros1=int(O1[i]), lula2=int(L2[i]), flavio2=int(F2[i]),
                        comp1=int(CP1[i]), comp2=int(CP2[i]), aptos=int(AP2[i])) for i in top]
# por UF: taxa de outliers
out['outliers_uf'] = {u: dict(n=int((mr & (uf == u)).sum()), z4=int((mr & (uf == u) & (np.abs(z) > 4)).sum()))
                      for u in sorted(set(uf))}

# ---------- impressão digital (comparecimento x % Lula), 2º turno ----------
mfp = (AP2 >= 50) & (v2 >= 20)
H, _, _ = np.histogram2d(CP2[mfp] / AP2[mfp], L2[mfp] / v2[mfp], bins=[np.linspace(0.3, 1, 71), np.linspace(0, 1, 101)])
out['fingerprint'] = dict(t2=H.astype(int).tolist(), turn_edges=[0.3, 1.0, 70], share_edges=[0, 1, 100])
mfp1 = (AP1 >= 50) & (v1 >= 20)
H1, _, _ = np.histogram2d(CP1[mfp1] / AP1[mfp1], L1[mfp1] / v1[mfp1], bins=[np.linspace(0.3, 1, 71), np.linspace(0, 1, 101)])
out['fingerprint']['t1'] = H1.astype(int).tolist()
# correlação comparecimento x % Lula
out['corr_turn_share'] = dict(t1=float(np.corrcoef(CP1[mfp1] / AP1[mfp1], L1[mfp1] / v1[mfp1])[0, 1]),
                              t2=float(np.corrcoef(CP2[mfp] / AP2[mfp], L2[mfp] / v2[mfp])[0, 1]))

# ---------- variação de comparecimento por seção ----------
mt = both & (AP2 >= 50)
dt = (CP2 - CP1)[mt] / AP2[mt]
out['hist_dturn'] = dict(edges=np.linspace(-0.3, 0.3, 61).round(3).tolist(),
                         counts=hist(np.clip(dt, -0.2999, 0.2999), None, np.linspace(-0.3, 0.3, 61)))

# ---------- modelo de urna ----------
mods = []
for k, nm in enumerate(MODELOS):
    m2 = (col('t2_modelo') == k) & (v2 > 0)
    m1 = (col('t1_modelo') == k) & (v1 > 0)
    mm = mr & (col('t2_modelo') == k)
    if m2.sum() + m1.sum() == 0: continue
    mods.append(dict(modelo=nm, secoes_t2=int(m2.sum()), lula2=int(L2[m2].sum()), flavio2=int(F2[m2].sum()),
                     secoes_t1=int(m1.sum()), lula1=int(L1[m1].sum()), flavio1=int(F1[m1].sum()), outros1=int(O1[m1].sum()),
                     resid_medio=float(np.mean(resid[mm]) * 100) if mm.sum() else None,
                     resid_n=int(mm.sum())))
out['modelos'] = mods

# ---------- horário de recebimento do BU (curva da apuração) ----------
def curva(bu, L, F, mask):
    m = mask & (bu >= 0)
    if not m.any(): return []
    o = np.argsort(bu[m], kind='stable')
    t = bu[m][o]; l = np.cumsum(L[m][o]); f = np.cumsum(F[m][o])
    pts = []
    for tm in range(int(t.min()) // 10 * 10, int(t.max()) + 10, 10):
        k = np.searchsorted(t, tm, side='right')
        if k == 0: continue
        pts.append([tm, int(l[k - 1]), int(f[k - 1]), int(k)])
    return pts
out['curva'] = dict(t1=curva(col('t1_bu_min'), L1, F1, v1 > 0), t2=curva(col('t2_bu_min'), L2, F2, v2 > 0))
# composição regional ao longo da apuração (2º turno, por hora)
bu2 = col('t2_bu_min')
out['curva_regiao'] = {r: [[m, int(((bu2 >= 0) & (bu2 <= m) & (reg == r) & (v2 > 0)).sum())] for m in range(18 * 60 + 30, 23 * 60 + 1, 10)] for r in REG}

# ---------- Benford (2º dígito) e último dígito ----------
def digits(x):
    x = x[x >= 10]
    s = x.astype(str)
    d2 = np.array([int(v[1]) for v in s]); dl = x % 10
    return np.bincount(d2, minlength=10).tolist(), np.bincount(dl, minlength=10).tolist(), int(len(x))
out['digitos'] = {}
for nm, x in [('lula2', L2), ('flavio2', F2), ('lula1', L1), ('flavio1', F1)]:
    b2, ld, n = digits(x)
    out['digitos'][nm] = dict(segundo=b2, ultimo=ld, n=n)

# ---------- verificações das afirmações da conversa ----------
rio = [c for c, (u, n) in MUN.items() if u == 'RJ' and n.upper() == 'RIO DE JANEIRO']
mrio = np.isin(mun, rio)
out['rio_capital'] = tot(mrio)
out['rj_estado'] = tot(uf == 'RJ')

# ---------- municípios: maiores variações ----------
mun_rows = []
for c in np.unique(mun):
    m = mun == c
    t1v = int(v1[m].sum()); t2v = int(v2[m].sum())
    if t1v < 1000: continue
    l1, f1, l2, f2 = int(L1[m].sum()), int(F1[m].sum()), int(L2[m].sum()), int(F2[m].sum())
    mun_rows.append(dict(uf=MUN.get(int(c), ('', ''))[0], mun=MUN.get(int(c), ('', ''))[1], v1=t1v, v2=t2v,
                         l1=l1, f1=f1, o1=int(O1[m].sum()), l2=l2, f2=f2,
                         sw=round((l2 / max(t2v, 1) - l1 / max(l1 + f1, 1)) * 100, 2)))
out['municipios_n'] = len(mun_rows)
sws = np.array([r['sw'] for r in mun_rows])
out['hist_swing_mun'] = dict(edges=np.linspace(-20, 20, 41).tolist(), counts=hist(np.clip(sws, -19.99, 19.99), None, np.linspace(-20, 20, 41)))
mun_rows.sort(key=lambda r: r['sw'])
out['mun_top_flavio'] = mun_rows[:15]; out['mun_top_lula'] = mun_rows[-15:][::-1]
out['mun_flavio_perdeu'] = sum(1 for r in mun_rows if r['f2'] < r['f1'])
out['mun_lula_perdeu'] = sum(1 for r in mun_rows if r['l2'] < r['l1'])
# "Flávio ganhou só 1 voto" - municípios com diferença de 0-2 votos entre turnos
out['mun_delta_flavio_pequeno'] = [r for r in mun_rows if abs(r['f2'] - r['f1']) <= 2][:30]

json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print('ok', len(json.dumps(out)) // 1024, 'KB')

# ---------- extras ----------
from math import erfc, sqrt, exp, lgamma, log
def chi2_sf(x, k):
    # cauda superior da qui-quadrado (série incompleta gama regularizada)
    a = k / 2.0; x2 = x / 2.0
    if x2 < a + 1:
        s = term = 1.0 / a; n = a
        for _ in range(500):
            n += 1; term *= x2 / n; s += term
        return 1 - s * exp(-x2 + a * log(x2) - lgamma(a))
    b = x2 + 1 - a; c = 1e300; dd = 1 / b; h = dd
    for i in range(1, 500):
        an = -i * (i - a); b += 2; dd = an * dd + b; c = b + an / c; dd = 1 / dd; h *= dd * c
    return exp(-x2 + a * log(x2) - lgamma(a)) * h
for nm, v in out['digitos'].items():
    obs = np.array(v['ultimo'], float); e = obs.sum() / 10
    chi = float(((obs - e) ** 2 / e).sum()); v['chi2_ultimo'] = chi; v['p_ultimo'] = chi2_sf(chi, 9)
bmask = mr & (np.abs(z) > 4)
imp = (resid * v2)[bmask]
out['outliers_impacto'] = dict(liquido_lula=float(imp.sum()), votos_secoes=int(v2[bmask].sum()))
mm = both & (AP1 != AP2)
out['aptos_dif_hist'] = np.bincount(np.clip(np.abs(AP1 - AP2)[mm], 0, 10)).tolist()
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print({k: v.get('p_ultimo') for k, v in out['digitos'].items()}, out['outliers_impacto'], out['aptos_dif_hist'])
