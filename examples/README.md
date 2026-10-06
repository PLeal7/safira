# Entrada sintetica safira-batch-v1

O contrato normativo esta em [contrato-entrega-operacional.md](../documents/extras/contrato-entrega-operacional.md).
Nao colocar dados reais, artefatos reais ou identificadores pessoais neste diretorio.

## Interfaces

Com `src/` no caminho de importacao:

```python
from contrato_inferencia import COLUNAS_MODELO, validar_entrada
from dados_sinteticos_operacionais import criar_entrada_sintetica

entrada = criar_entrada_sintetica()
normalizada, correcoes = validar_entrada(
    entrada,
    t_score="2026-10-06T12:00:00Z",
    fuso_operacional="America/Sao_Paulo",
)
x = normalizada.loc[:, list(COLUNAS_MODELO)]
```

- `ler_entrada(caminho: str | Path) -> pd.DataFrame`: CSV UTF-8, virgula, cabecalho unico e schema exato, registros com a mesma quantidade de campos. Todos os campos sao lidos como texto, inclusive vazios; `NA`/`NULL` e zeros iniciais permanecem literais.
- `validar_entrada(df, *, t_score: str, fuso_operacional: str) -> tuple[pd.DataFrame, dict]`: copia com as quatro colunas de passagem, as 14 features na ordem canonica e `DIA_OPERACIONAL` (`YYYY-MM-DD`). Preserva indice, linhas, IDs e timestamps; nao modifica a entrada.
- `ErroContrato(ValueError)`: bloqueia o lote inteiro com regra/coluna/quantidade, sem valores individuais, nomes arbitrarios de colunas extras ou caminhos.
- `COLUNAS_MODELO`: tupla do V1 seguida do historico. `COLUNAS_PASSAGEM`: lista dos dois IDs e dos dois timestamps. Nenhuma coluna de passagem ou dia entra em `x`.

Campos vazios/em branco e nulos reais sao ausencia; textos numericos invalidos nao sao convertidos silenciosamente. Booleano aceita somente `true`/`false` ou booleanos reais. Categorias novas sao aceitas como texto e normalizadas conforme treino, sem aprender categorias. Numeros usam decimal ponto, sem booleanos ou infinitos. Parsing numerico precede a mascara de cancelamento; `N_TRECHOS` e validado depois da mascara. Contagem historica e obrigatoria, inteira e nao negativa; zero exige indicador/taxa nulos, positivo exige indicador binario e taxa finita em `[0,1]`, com indicador 1 exatamente quando taxa positiva.

O resumo contem somente contagens inteiras: `categorias_normalizadas` (celulas textuais alteradas), `tempo_voo_nao_positivo` (duracoes convertidas em nulo) e `campos_mascarados_cancelamento` (celulas ainda preenchidas removidas pela mascara). Lote vazio com schema correto retorna copia valida e contagens zero.

## Limites

Nao ha `fit`, imputacao, encoding, recalculo de historico, carregamento de artefato ou scoring nesta interface. Sem encoder fitted, nao se contabilizam categorias desconhecidas. Timestamps declarados ate `t_score` nao comprovam reconstrucao as-of, ausencia de resposta atual, proveniencia autorizada ou populacao diaria completa. Essas garantias continuam sob responsabilidade da fonte e da integracao; validacao sintetica nao autoriza uso de dados reais.

Os casos inteiramente artificiais e executaveis estao em `tests/test_contrato_inferencia.py`; nenhum CSV real e necessario.
