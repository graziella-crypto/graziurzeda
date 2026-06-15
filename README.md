# ✈ Caça-Passagens — Goiânia → Maceió

Aplicativo web para encontrar **passagens aéreas baratas** e **promoções
relâmpago** no trecho **Goiânia (GYN) → Maceió (MCZ)**, ida e volta, com
foco no período solicitado: **15/08/2026 a 22/08/2026**.

Mostra na própria tela:

- 💰 **Comparativo de preços** — as ofertas ordenadas da mais barata, cada
  uma com os **preços por site/agência** (qual buscador está mais barato),
  prontos para clicar.
- 📅 **Comparativo de datas** — uma faixa com os dias próximos e seus
  preços, destacando o **dia mais barato**. Toque num dia para refazer a
  busca mantendo a duração da viagem.
- ⚡ **Promoções relâmpago** — tarifas abaixo de um limite configurável (padrão R$ 700).
- ↓ **Achados** — tarifas abaixo da mediana das tarifas encontradas (padrão 15%).

> Para preços **reais** na tela, conecte a fonte de dados Skyscanner via
> RapidAPI (gratuita, sem cartão — veja abaixo). Sem chave, o app funciona
> em **modo demonstração** com preços simulados claramente sinalizados.

## Preços reais: Skyscanner via RapidAPI (recomendado)

1. Crie uma conta gratuita em <https://rapidapi.com>.
2. Assine a API **"Sky-Scrapper"** (apiheya) — há **plano gratuito sem cartão**.
3. Copie sua **X-RapidAPI-Key** e configure:

```bash
export RAPIDAPI_KEY=sua_chave
python app.py
```

No **Render**, basta colar a chave em *Environment* → `RAPIDAPI_KEY`. Como
`FF_PROVIDER=auto`, o app passa a usar a Skyscanner automaticamente e o
banner de demonstração some.

## Como funciona

A busca usa uma arquitetura de provedores:

| Provedor | Quando é usado | Dados |
|----------|----------------|-------|
| **Skyscanner** (RapidAPI) | `RAPIDAPI_KEY` configurada | Reais — preços por site + calendário |
| **Amadeus** | Credenciais Amadeus configuradas | Reais (API Self-Service) |
| **Demo** | Padrão / fallback | Estimativas geradas localmente |

No modo `auto` (padrão), a ordem de preferência é **Skyscanner → Amadeus →
demonstração**. Sem nenhuma chave, o app roda em **modo demonstração** com
preços simulados (claramente sinalizados) — ideal para ver a interface.

## Executando

```bash
pip install -r requirements.txt
python app.py
# abra http://localhost:5000
```

Para usar preços reais, crie uma conta gratuita em
<https://developers.amadeus.com>, gere um app e exporte as credenciais
(ou copie `.env.example` para `.env`):

```bash
export AMADEUS_CLIENT_ID=seu_id
export AMADEUS_CLIENT_SECRET=seu_secret
python app.py
```

### Atenção: ambiente de Teste x Produção (a pegadinha da Amadeus)

Ao se cadastrar, as chaves geradas são do **ambiente de Teste**
(`test.api.amadeus.com`), que usa uma base **limitada e parcialmente
sintética**. Muitas rotas domésticas brasileiras (incluindo **GYN-MCZ**)
**não retornam voos** nesse ambiente — é o motivo mais comum de "não
funcionar". Nesse caso o app mostra um aviso e cai na demonstração.

Para tarifas reais de verdade você precisa das chaves de **Produção**:

1. No painel da Amadeus, abra seu app e clique em algo como
   **"Request production key"** / mude para *Production*.
2. É preciso cadastrar um **cartão** (há cota mensal gratuita; cobra só
   se exceder).
3. Use as chaves de produção **e** defina o host de produção:

```bash
export AMADEUS_HOST=https://api.amadeus.com
export AMADEUS_CLIENT_ID=chave_de_producao
export AMADEUS_CLIENT_SECRET=segredo_de_producao
```

> Dica: se preferir não cadastrar cartão, mantenha o app como **buscador**
> — os botões "Ver preços reais" (Kayak/Skyscanner/Google) já trazem as
> tarifas verdadeiras de GYN→MCZ sem nenhuma chave.

## Configuração

Tudo é ajustável por variáveis de ambiente (veja `.env.example`) ou
diretamente pela interface (origem, destino, datas e o limite de alerta de
promoção). Os padrões já vêm preparados para a viagem GYN → MCZ em
agosto/2026.

## Endpoints

- `GET /` — interface web.
- `GET /api/search` — JSON com as ofertas analisadas. Parâmetros opcionais:
  `origin`, `destination`, `departure`, `return`, `adults`, `flash`.
- `GET /healthz` — verificação de saúde.

Exemplo:

```bash
curl "http://localhost:5000/api/search?origin=GYN&destination=MCZ&departure=2026-08-15&return=2026-08-22"
```

## Estrutura

```
app.py                      # App Flask (rotas e API)
flight_finder/
  config.py                 # Configuração (defaults da viagem + env vars)
  models.py                 # FlightOffer / SearchResult
  links.py                  # Links de busca preenchidos (Kayak/Skyscanner/...)
  service.py                # Orquestra busca + análise + calendário
  providers/
    base.py                 # Interface FlightProvider
    demo.py                 # Dados de demonstração (preços + calendário)
    skyscanner.py           # API Skyscanner via RapidAPI (dados reais)
    amadeus.py              # API Amadeus (dados reais)
templates/index.html        # Interface
static/style.css, app.js    # Front-end (comparativo de preços e datas)
test_flight_finder.py       # Testes
```

## Testes

```bash
python -m pytest test_flight_finder.py -q   # ou: python test_flight_finder.py
```

## Aviso

Os preços do modo demonstração são **estimativas** geradas localmente e não
representam tarifas reais. Confirme sempre o valor no site da companhia
aérea antes de comprar.
