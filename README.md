# PW11-EOQ-inventory
# Inventory Management – EOQ & Safety Stock

Applicazione Python per la gestione delle scorte di magazzino basata sul modello **EOQ (Economic Order Quantity)** con integrazione della **scorta di sicurezza** e simulazione operativa.

Il progetto è pensato come strumento di supporto decisionale per un magazzino del settore primario (es. prodotti agricoli o mangimi per allevamenti) e permette di confrontare diverse politiche di riordino in condizioni di domanda incerta.

---

## Obiettivi del progetto

L’applicazione consente di:

- determinare quanto ordinare (EOQ)
- determinare quando ordinare (ROP)
- ridurre il rischio di stockout
- analizzare il compromesso tra livello di servizio e giacenza media
- confrontare riordino classico vs riordino con scorta di sicurezza

Il confronto avviene tramite simulazione su un dataset realistico di **3 anni di domanda giornaliera**.

---

## Modello utilizzato

### EOQ
EOQ = sqrt((2 * D * S) / H)

### Punto di riordino
ROP = d * L + SS

### Scorta di sicurezza (lead time variabile)
SS = z * sqrt((sigma_d^2 * L) + (d^2 * sigma_L^2))

---

## Struttura del progetto
data_gen.py # Generazione dataset simulato (3 anni)
- models.py # Calcoli EOQ, Safety Stock e ROP
- inventory.py # Simulazione operativa del magazzino
- app.py # Interfaccia utente Streamlit
- demand_3y.csv # Dataset generato
- README.md


---

## Descrizione moduli

| File | Funzione |
|----|----|
| data_gen.py | Genera domanda giornaliera realistica con variabilità e stagionalità |
| models.py | Implementa il modello matematico di gestione scorte |
| inventory.py | Simula il comportamento del magazzino nel tempo |
| app.py | Interfaccia grafica interattiva per l’utente |

---

## Funzionalità principali

- Inserimento costi e parametri operativi
- Scelta del livello di servizio
- Supporto a lead time fisso o variabile
- Calcolo automatico delle politiche di riordino
- Simulazione su 3 anni
- KPI di performance:
  - giorni di stockout
  - livello di servizio
  - giacenza media
- Grafico dinamico delle scorte

---

## Avvio dell'applicazione
### 1. Clona il repository
git clone https://github.com/NappiV/PW11-EOQ-inventory.git
cd PW11-EOQ-inventor
### 2. Installa le dipendenze
pip install -r requirements.txt
### 3. Genera il dataset
python data_gen.py
### 4. Avvia l'app
streamlit run app.py

---

## Utilizzo

1. Imposta costi e tempi nella sidebar
2. Seleziona il livello di servizio
3. (Opzionale) abilita lead time variabile
4. Analizza risultati e confronto tra strategie

---

## Scopo didattico

Il progetto mostra come un modello teorico di gestione scorte possa diventare uno strumento interattivo e verificato tramite simulazione.

Trade-off osservato:

maggiore sicurezza → meno stockout → maggiore giacenza media


