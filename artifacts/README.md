# Artefatos locais

Modelos, manifestos reais e outputs ficam apenas no ambiente autorizado. Todo o
conteudo desta pasta, exceto este guia, esta ignorado pelo Git.

`scripts/gerar_artefato_modelo.py` produz um pipeline ajustado e seu manifesto.
O modo `--sintetico` serve somente para demonstracao funcional. Nenhum artefato
gerado por este pacote tem aprovacao automatica para producao.

## Geracao sintetica

Na raiz do repositorio, usando o ambiente de treinamento:

```bash
python scripts/gerar_artefato_modelo.py --sintetico \
  --modelo artifacts/modelo-sintetico-v1.joblib \
  --manifesto artifacts/manifesto-sintetico-v1.json \
  --versao-modelo sintetico-v1 --versao-fontes artificial
```

Os destinos nao podem existir: o script recusa sobrescrever uma versao.
Para fontes reais autorizadas, substituir `--sintetico` por `--base` com o
caminho local da base analitica Parquet. Nao publicar os arquivos gerados.

## Manifesto

O JSON gerado registra:

| Campos | Conteudo |
| --- | --- |
| `versao_modelo`, `versao_contrato`, `versao_politica_fila`, `commit_fonte` | Identificacao da entrega e do codigo |
| `sha256`, `sha256_configuracao` | Integridade do binario e da configuracao |
| `versoes` | Python e bibliotecas efetivamente utilizadas |
| `features`, `tipos`, `features_transformadas` | Schema bruto e saida do preprocessador |
| `classes`, `classe_positiva` | Classes do modelo; Detrator corresponde a 1 |
| `parametros`, `semente` | Configuracao efetiva do estimador |
| `cortes`, `split`, `periodo_treino` | Particionamento e periodo observado no treino |
| `calibracao` | Sigmoid no treino, explicitamente in-sample |
| `versao_fontes`, `fingerprint_base`, `gerado_em` | Proveniencia e instante de geracao |
| `dados_sinteticos`, `aprovado_producao` | Demonstracao artificial e ausencia de aprovacao automatica |
| `avaliacao_referencia`, `limitacoes` | Referencia historica e limites da entrega |

O exemplo completo e produzido localmente pelo comando acima. Os testes de
`tests/test_artefato_modelo.py` verificam manifesto, hash, equivalencia apos
serializacao e determinismo exclusivamente com dados artificiais.

O manifesto registra o ambiente efetivo e o SHA-256. Carregar apenas arquivos de
origem confiavel: hash nao autentica o fornecedor e Joblib pode executar codigo.
