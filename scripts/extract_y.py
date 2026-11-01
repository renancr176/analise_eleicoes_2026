# Extrai, por seção eleitoral, os dados de presidente do 1º e 2º turno (TSE 2026)
# Uso: python -I extract.py <pasta_dados> <saida.npz>
import zipfile, io, csv, sys, os, time
import numpy as np

src, out = sys.argv[1], sys.argv[2]
ANO, NA, NB, NC = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
UFS = {}
MUNS = {}
LOCS = {}

def key(row, ix):
    return (int(row[ix['CD_MUNICIPIO']]), int(row[ix['NR_ZONA']]), int(row[ix['NR_SECAO']]))

# colunas do vetor por seção
COLS = ['uf', 'mun', 'zona', 'secao', 'local',
        't1_lula', 't1_flavio', 't1_outros', 't1_aptos', 't1_comp', 't1_brancos', 't1_nulos', 't1_bu_min', 't1_modelo',
        't2_lula', 't2_flavio', 't2_aptos', 't2_comp', 't2_brancos', 't2_nulos', 't2_bu_min', 't2_modelo',
        't1_cury', 't1_renan', 't1_caiado', 't1_zema']
C = {c: i for i, c in enumerate(COLS)}
data = {}

def get(k, uf, local):
    v = data.get(k)
    if v is None:
        v = [0] * len(COLS)
        v[C['uf']] = UFS.setdefault(uf, len(UFS))
        v[C['mun']], v[C['zona']], v[C['secao']] = k
        v[C['local']] = local
        v[C['t1_bu_min']] = v[C['t2_bu_min']] = -1
        v[C['t1_modelo']] = v[C['t2_modelo']] = -1
        data[k] = v
    return v

t0 = time.time()
# 1) votos por candidato por seção
z = zipfile.ZipFile(os.path.join(src, f'votacao_secao_{ANO}_BR.zip'))
with z.open(f'votacao_secao_{ANO}_BR.csv') as f:
    r = csv.reader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';')
    h = next(r); ix = {k: i for i, k in enumerate(h)}
    iT, iN, iQ, iU, iC, iMN, iL = ix['NR_TURNO'], ix['NR_VOTAVEL'], ix['QT_VOTOS'], ix['SG_UF'], ix['CD_CARGO'], ix['NM_MUNICIPIO'], ix['NR_LOCAL_VOTACAO']
    n = 0
    for row in r:
        if row[iC].lstrip('0') != '1':
            continue
        k = key(row, ix)
        MUNS.setdefault(k[0], (row[iU], row[iMN].encode('latin-1').decode('latin-1')))
        v = get(k, row[iU], int(row[iL]))
        t, nv, q = row[iT], row[iN], int(row[iQ])
        if t == '1':
            if nv == NA: v[C['t1_lula']] += q
            elif nv == NB: v[C['t1_flavio']] += q
            elif nv in ('95', '96', '97', '98'): pass  # branco/nulo vêm do detalhe
            else:
                v[C['t1_outros']] += q
                if nv == NC: v[C['t1_cury']] += q
        else:
            if nv == NA: v[C['t2_lula']] += q
            elif nv == NB: v[C['t2_flavio']] += q
        n += 1
        if n % 5_000_000 == 0:
            print('votos', n, len(data), round(time.time() - t0), flush=True)
print('votos ok', n, len(data), round(time.time() - t0), flush=True)

# 2) detalhe por seção: aptos, comparecimento, brancos, nulos, hora do BU, modelo da urna
MODELOS = {}
def minutes(s, de):
    # "dd/mm/yyyy HH:MM:SS" -> minutos desde 00:00 do dia da eleição (+1440 por dia seguinte)
    if not s or len(s) < 16 or not s[0].isdigit(): return -1
    d = int(s[0:2]); hh = int(s[11:13]); mm = int(s[14:16])
    return hh * 60 + mm + 1440 * (d - int(de[0:2]))

z = zipfile.ZipFile(os.path.join(src, f'detalhe_votacao_secao_{ANO}.zip'))
with z.open(f'detalhe_votacao_secao_{ANO}_BR.csv') as f:
    r = csv.reader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';')
    h = next(r); ix = {k: i for i, k in enumerate(h)}
    n = 0
    for row in r:
        if row[ix['CD_CARGO']].strip('0') != '1':
            continue
        k = key(row, ix)
        v = get(k, row[ix['SG_UF']], int(row[ix['NR_LOCAL_VOTACAO']]))
        p = 't1_' if row[ix['NR_TURNO']] == '1' else 't2_'
        v[C[p + 'aptos']] = int(row[ix['QT_APTOS']])
        v[C[p + 'comp']] = int(row[ix['QT_COMPARECIMENTO']])
        v[C[p + 'brancos']] = int(row[ix['QT_VOTOS_BRANCOS']])
        v[C[p + 'nulos']] = int(row[ix['QT_VOTOS_NULOS']])
        if 'DT_RECEBIMENTO_BU_HOR_TSE' in ix:
            v[C[p + 'bu_min']] = minutes(row[ix['DT_RECEBIMENTO_BU_HOR_TSE']], row[ix['DT_ELEICAO']])
        if 'DS_MODELO_URNA' in ix:
            v[C[p + 'modelo']] = MODELOS.setdefault(row[ix['DS_MODELO_URNA']] + ' | ' + row[ix['DS_ORIGEM_VOTO']], len(MODELOS))
        n += 1
print('detalhe ok', n, round(time.time() - t0), flush=True)

arr = np.array(list(data.values()), dtype=np.int64)
np.savez_compressed(out, arr=arr, cols=np.array(COLS),
                    ufs=np.array(sorted(UFS, key=UFS.get)),
                    modelos=np.array(sorted(MODELOS, key=MODELOS.get)),
                    mun_codes=np.array(list(MUNS.keys())),
                    mun_uf=np.array([m[0] for m in MUNS.values()]),
                    mun_nome=np.array([m[1] for m in MUNS.values()]))
print('salvo', arr.shape, round(time.time() - t0))
