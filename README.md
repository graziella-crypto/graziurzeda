# ✈ Caça-Passagens — Goiânia → Maceió

Aplicativo web para encontrar **passagens aéreas baratas** e **promoções
relâmpago** no trecho **Goiânia (GYN) → Maceió (MCZ)**, ida e volta, com
foco no período solicitado: **15/08/2026 a 22/08/2026**.

A aplicação busca as ofertas, ordena pelo menor preço e destaca
automaticamente:

- ⚡ **Promoções relâmpago** — tarifas abaixo de um limite configurável (padrão R$ 700).
- ↓ **Achados** — tarifas que ficam um percentual abaixo da mediana das tarifas encontradas (padrão 15%).

Também mostra um resumo com a tarifa mais barata, o preço mediano e a
contagem de promoções e achados.

## Como funciona

A busca usa uma arquitetura de provedores:

| Provedor | Quando é usado | Dados |
|----------|----------------|-------|
| **Amadeus** | Quando há credenciais configuradas | Reais (API Self-Service) |
| **Demo** | Padrão / fallback | Estimativas realistas geradas localmente |

Sem credenciais, o app já roda imediatamente em **modo demonstração**, com
preços plausíveis para o trecho — ideal para testar a interface. Para
preços reais, basta configurar a API Amadeus (gratuita).

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

> O ambiente padrão é o de **teste** do Amadeus, que tem cobertura de
> dados limitada. Para produção, defina `AMADEUS_HOST=https://api.amadeus.com`.

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
  service.py                # Orquestra busca + análise de preços
  providers/
    base.py                 # Interface FlightProvider
    demo.py                 # Dados de demonstração
    amadeus.py              # API Amadeus (dados reais)
templates/index.html        # Interface
static/style.css, app.js    # Front-end
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
