# Monta o HTML final a partir do template + JSONs (lidos da pasta atual)
# Uso: python -P build.py [saida.html]
import os, sys
saida = sys.argv[1] if len(sys.argv) > 1 else 'analise_eleicoes_2026.html'
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html'), encoding='utf-8').read()
d = {k: open(f, encoding='utf-8').read() for k, f in [('2014', 'res_2014.json'), ('2018', 'res_2018.json'), ('2022', 'res_2022.json')]}
anos = '{' + ','.join(f'"{k}":{v}' for k, v in d.items()) + '}'
out = (t.replace('/*__DATA__*/null', open('res.json', encoding='utf-8').read())
        .replace('/*__ANOS__*/null', anos).replace('/*__CROSS__*/null', open('cross.json', encoding='utf-8').read())
        .replace('/*__H22__*/null', open('hist22.json', encoding='utf-8').read()).replace('/*__BN__*/null', open('bn_check.json', encoding='utf-8').read()))
open(saida, 'w', encoding='utf-8').write(out)
print('gerado:', os.path.abspath(saida))
