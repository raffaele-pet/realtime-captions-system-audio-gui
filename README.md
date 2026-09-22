# Realtime Captions – Windows GUI

Sottotitoli in tempo reale per tutto l'audio riprodotto dal computer.

L'app cattura l'audio di sistema tramite WASAPI, lo trascrive localmente con
Whisper e mostra il testo in una moderna interfaccia Windows e, opzionalmente,
in un overlay sempre in primo piano.

Nessun account, servizio cloud o abbonamento è necessario. Dopo il download
iniziale del modello, la trascrizione funziona offline.

## Funzionalità

- Cattura diretta dell'audio di sistema, senza microfono o cavi virtuali.
- Interfaccia grafica pulita e semplice da usare.
- Download e gestione dei modelli Whisper direttamente dalla GUI.
- Scelta indipendente del modello installato da utilizzare.
- Supporto per `tiny.en`, `small.en` e `medium.en`.
- Accelerazione NVIDIA CUDA, selezionata come impostazione predefinita.
- Modalità CPU disponibile per computer senza GPU NVIDIA compatibile.
- Sottotitoli sovrapposti, allineati a sinistra e sempre aggiornati sul testo più recente.
- Trascrizione live e cronologia delle frasi completate.
- Salvataggio progressivo delle trascrizioni in file `.txt`.
- Monitoraggio di CPU, RAM, GPU e VRAM.
- Protezione da avvii multipli: il collegamento apre una sola istanza dell'app.
- Elaborazione interamente locale per tutelare la privacy.

## Requisiti

- Windows 11.
- Python 3.11 o superiore.
- Un dispositivo audio compatibile con WASAPI loopback.
- Connessione Internet solo per installazione e download dei modelli.
- GPU NVIDIA consigliata, ma non obbligatoria.

## Installazione

Scarica o clona la repository:

```powershell
git clone https://github.com/raffaele-pet/realtime-captions-system-audio-gui.git
cd realtime-captions-system-audio-gui
```

Esegui:

```text
install.bat
```

L'installer:

1. crea un ambiente Python isolato in `.venv`;
2. installa RealtimeSTT, Faster Whisper, Silero VAD e le altre dipendenze;
3. scarica e prepara l'icona dell'app;
4. crea il collegamento **Realtime Captions** sul desktop;
5. avvia l'interfaccia grafica.

L'installer può essere eseguito nuovamente per riparare o aggiornare le
dipendenze senza eliminare modelli e trascrizioni.

## Utilizzo

1. Apri **Realtime Captions** dal collegamento sul desktop.
2. Seleziona il dispositivo audio che sta riproducendo il contenuto.
3. Scarica uno o più modelli Whisper.
4. Scegli il modello attivo e il tipo di elaborazione.
5. Abilita, se desiderato, overlay e salvataggio su file.
6. Premi **Avvia trascrizione**.
7. Premi **Stop ascolto** per terminare la sessione.

Puoi scaricare tutti e tre i modelli e cambiare quello attivo prima di ogni
sessione.

## Modelli disponibili

| Modello | Download indicativo | Profilo | Utilizzo consigliato |
|---|---:|---|---|
| `tiny.en` | ~75 MB | Molto veloce | Sottotitoli rapidi e sistemi meno potenti |
| `small.en` | ~460 MB | Bilanciato | Miglior compromesso tra velocità e precisione |
| `medium.en` | ~1,5 GB | Accurato | Trascrizioni più precise con hardware adeguato |

I modelli `.en` sono ottimizzati per l'inglese. I file vengono conservati nella
cache locale di Hugging Face e non vengono inclusi nella repository.

## CPU e CUDA

`CUDA` è l'impostazione predefinita. Richiede una GPU NVIDIA e driver
compatibili. Se l'avvio fallisce su un computer senza CUDA, seleziona `cpu`
dalla voce **Elaborazione**.

Il modello rimane in RAM o VRAM durante l'ascolto. I buffer audio sono limitati,
la cronologia nell'interfaccia conserva al massimo 100 segmenti e il testo live
non cresce indefinitamente. Le trascrizioni complete vengono scritte
progressivamente nella cartella `transcripts`.

## Privacy

- L'audio non viene inviato a servizi di trascrizione online.
- La trascrizione avviene sul computer dell'utente.
- Non sono richiesti account o API key.
- Internet viene utilizzato soltanto per scaricare dipendenze e modelli.

## Interfaccia da terminale

La precedente interfaccia testuale resta disponibile per utenti avanzati:

```powershell
.venv\Scripts\python.exe console.py
```

## Risoluzione dei problemi

### Nessun dispositivo audio disponibile

Avvia la riproduzione di un audio e premi il pulsante di aggiornamento accanto
alla sorgente. È inoltre disponibile il controllo diagnostico:

```powershell
.venv\Scripts\python.exe tools\check_loopback.py
```

### Il modello non parte con CUDA

Verifica i driver NVIDIA oppure seleziona `cpu` nell'interfaccia.

### Dove vengono salvate le trascrizioni?

I file si trovano nella cartella `transcripts` con nome simile a:

```text
transcript_20260922_143000.txt
```

I dettagli degli errori dell'interfaccia vengono registrati in
`logs/realtime-captions.log`.

## Componenti principali

- [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Silero VAD](https://github.com/snakers4/silero-vad)
- [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch)

## Crediti

Questo progetto deriva da
[emidium-science/realtime-captions-system-audio](https://github.com/emidium-science/realtime-captions-system-audio)
ed è stato ampliato con installer Windows, gestione grafica dei modelli,
interfaccia desktop, overlay aggiornato, controlli di memoria e avvio a istanza
singola.

L'icona del collegamento desktop è fornita da
[Icons8](https://icons8.it/icon/QfXoGJ7IiNP0/chat-room).
