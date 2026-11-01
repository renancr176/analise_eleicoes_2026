# Curva oficial de totalização 2022 (TSE) a cada 10 min: [minuto, lula, bolsonaro, % seções]
import zipfile, io, csv, sys, json, os
out = {}
for t in ('1T', '2T'):
    z = zipfile.ZipFile(os.path.join(sys.argv[1], f'Historico_Totalizacao_Presidente_BR_{t}_2022.zip'))
    with z.open(f'Historico_Totalizacao_Presidente_BR_{t}_2022.csv') as f:
        r = csv.reader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';')
        h = [c.strip() for c in next(r)]; ix = {k: i for i, k in enumerate(h)}
        pts, last = [], -1
        for row in r:
            s = row[ix["DT_TOTALIZACAO"]].strip() if row else ""
            if len(s) < 16: continue
            d0 = int(s[0:2]); m = int(s[11:13]) * 60 + int(s[14:16]) + (1440 if d0 not in (2, 30) else 0)
            l = int(row[ix['LULA_QT_VOTOS_TOT_ACUMULADO']]); b = int(row[ix['JAIR_BOLSONARO_QT_VOTOS_TOT_ACUMULADO']])
            p = float(row[ix['PE_SECOES_TOT_ACUMULADO']].strip().replace(',', '.'))
            if m // 10 != last: pts.append([m, l, b, p]); last = m // 10
            else: pts[-1] = [m, l, b, p]
    out[t] = pts
json.dump(out, open(sys.argv[2], 'w'))
for t in out: print(t, len(out[t]), out[t][0], out[t][-1])
