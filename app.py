import streamlit as st
from mido import MidiFile, MidiTrack, MetaMessage
from collections import defaultdict
import os
import tempfile

# ---------- SUAS FUNÇÕES ----------

def remover_acordes_priorizar_maior(track: MidiTrack) -> MidiTrack:
    abs_time = 0
    note_ons_por_tempo = defaultdict(list)

    for idx, msg in enumerate(track):
        abs_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            note_ons_por_tempo[abs_time].append((msg.note, idx))

    note_on_remover = set()

    for tempo, lista in note_ons_por_tempo.items():
        if len(lista) > 1:
            maior_nota = max(n for (n, _) in lista)
            for nota, _ in lista:
                if nota != maior_nota:
                    note_on_remover.add((tempo, nota))

    if not note_on_remover:
        return track

    nova_track = MidiTrack()

    abs_time = 0
    dt_acumulado = 0
    notas_sendo_removidas = defaultdict(int)

    for msg in track:
        abs_time += msg.time
        dt_acumulado += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            chave = (abs_time, msg.note)

            if chave in note_on_remover:
                notas_sendo_removidas[msg.note] += 1
                continue

            nova_msg = msg.copy(time=dt_acumulado)
            nova_track.append(nova_msg)
            dt_acumulado = 0
            continue

        if (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
            if notas_sendo_removidas[msg.note] > 0:
                notas_sendo_removidas[msg.note] -= 1
                continue

            nova_msg = msg.copy(time=dt_acumulado)
            nova_track.append(nova_msg)
            dt_acumulado = 0
            continue

        nova_msg = msg.copy(time=dt_acumulado)
        nova_track.append(nova_msg)
        dt_acumulado = 0

    return nova_track


def limpar_cymbal_prioridade(track: MidiTrack) -> MidiTrack:
    PRIORIDADE = [49, 57]

    abs_time = 0
    note_ons_por_tempo = defaultdict(list)

    for idx, msg in enumerate(track):
        abs_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            note_ons_por_tempo[abs_time].append((msg.note, idx))

    note_on_remover_idx = set()

    for tempo, lista in note_ons_por_tempo.items():
        if len(lista) <= 1:
            continue

        notas = [n for (n, _) in lista]

        nota_keep = None
        for p in PRIORIDADE:
            if p in notas:
                nota_keep = p
                break

        if nota_keep is None:
            nota_keep = max(notas)

        kept_one = False
        for nota, idx in lista:
            if nota == nota_keep and not kept_one:
                kept_one = True
            else:
                note_on_remover_idx.add(idx)

    if not note_on_remover_idx:
        return track

    nova_track = MidiTrack()

    abs_time = 0
    dt_acumulado = 0
    notas_sendo_removidas = defaultdict(int)

    for idx, msg in enumerate(track):
        abs_time += msg.time
        dt_acumulado += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            if idx in note_on_remover_idx:
                notas_sendo_removidas[msg.note] += 1
                continue

            nova_msg = msg.copy(time=dt_acumulado)
            nova_track.append(nova_msg)
            dt_acumulado = 0
            continue

        if (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
            if notas_sendo_removidas[msg.note] > 0:
                notas_sendo_removidas[msg.note] -= 1
                continue

            nova_msg = msg.copy(time=dt_acumulado)
            nova_track.append(nova_msg)
            dt_acumulado = 0
            continue

        nova_msg = msg.copy(time=dt_acumulado)
        nova_track.append(nova_msg)
        dt_acumulado = 0

    return nova_track


def transpose_bassdrum(track: MidiTrack) -> MidiTrack:
    nova_track = MidiTrack()

    for msg in track:
        if msg.is_meta and msg.type == 'track_name':
            nova_track.append(msg.copy(time=0))
            break

    NOVO_35 = 59
    NOVO_36 = 60
    OFFSET = 21

    dt_acc = 0

    for msg in track:
        dt_acc += msg.time

        if msg.type in ('note_on', 'note_off'):
            old_note = msg.note

            if old_note == 35:
                new_note = NOVO_35
            elif old_note == 36:
                new_note = NOVO_36
            else:
                new_note = old_note + OFFSET

            novo_msg = msg.copy(note=new_note, time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

        elif msg.is_meta and msg.type == 'track_name':
            continue
        else:
            novo_msg = msg.copy(time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

    return nova_track


def transpose_snaredrum(track: MidiTrack) -> MidiTrack:
    nova_track = MidiTrack()

    for msg in track:
        if msg.is_meta and msg.type == 'track_name':
            nova_track.append(msg.copy(time=0))
            break

    MAP = {
        38: 68,
        39: 84,
        40: 68
    }

    dt_acc = 0

    for msg in track:
        dt_acc += msg.time

        if msg.type in ('note_on', 'note_off'):
            old_note = msg.note
            new_note = MAP.get(old_note, old_note)

            novo_msg = msg.copy(note=new_note, time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

        elif msg.is_meta and msg.type == 'track_name':
            continue
        else:
            novo_msg = msg.copy(time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

    return nova_track


def transpose_cymbal(track: MidiTrack) -> MidiTrack:
    nova_track = MidiTrack()

    for msg in track:
        if msg.is_meta and msg.type == 'track_name':
            nova_track.append(msg.copy(time=0))
            break

    MAP = {
        49: 78,
        57: 81
    }

    dt_acc = 0

    for msg in track:
        dt_acc += msg.time

        if msg.type in ('note_on', 'note_off'):
            old_note = msg.note
            new_note = MAP.get(old_note, old_note)

            novo_msg = msg.copy(note=new_note, time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

        elif msg.is_meta and msg.type == 'track_name':
            continue
        else:
            novo_msg = msg.copy(time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

    return nova_track


def transpose_bongo(track: MidiTrack) -> MidiTrack:
    nova_track = MidiTrack()

    for msg in track:
        if msg.is_meta and msg.type == 'track_name':
            nova_track.append(msg.copy(time=0))
            break

    dt_acc = 0

    for msg in track:
        dt_acc += msg.time

        if msg.type in ('note_on', 'note_off'):
            old_note = msg.note
            new_note = max(0, min(127, old_note + 10))

            novo_msg = msg.copy(note=new_note, time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

        elif msg.is_meta and msg.type == 'track_name':
            continue
        else:
            novo_msg = msg.copy(time=dt_acc)
            nova_track.append(novo_msg)
            dt_acc = 0

    return nova_track


def processar_midi_bateria(arquivo: str, drumkit_name: str) -> str:
    mid = MidiFile(arquivo)

    drumkit_track = None
    for track in mid.tracks:
        for msg in track:
            if msg.is_meta and msg.type == 'track_name' and msg.name == drumkit_name:
                drumkit_track = track
                break
        if drumkit_track is not None:
            break

    if drumkit_track is None:
        raise RuntimeError(f"Não encontrei a track '{drumkit_name}' no MIDI.")

    # SnareDrum
    snare_index = None
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.is_meta and msg.type == 'track_name' and msg.name == 'SnareDrum':
                snare_index = i
                break

    snare_track = MidiTrack()
    snare_track.append(MetaMessage('track_name', name='SnareDrum', time=0))
    NOTAS_SNARE = {38, 39, 40}

    acc_time = 0
    for msg in drumkit_track:
        acc_time += msg.time
        if msg.type in ('note_on', 'note_off') and msg.note in NOTAS_SNARE:
            copied = msg.copy(time=acc_time)
            copied.channel = 9
            snare_track.append(copied)
            acc_time = 0

    if snare_index is not None:
        mid.tracks[snare_index] = snare_track
    else:
        mid.tracks.append(snare_track)
        snare_index = len(mid.tracks) - 1

    # BassDrum
    bassdrum_index = None
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.is_meta and msg.type == 'track_name' and msg.name == 'BassDrum':
                bassdrum_index = i
                break

    bassdrum_track = MidiTrack()
    bassdrum_track.append(MetaMessage('track_name', name='BassDrum', time=0))
    NOTAS_BASSDRUM = {35, 36, 41, 43, 45, 47, 48, 50}

    acc_time = 0
    for msg in drumkit_track:
        acc_time += msg.time
        if msg.type in ('note_on', 'note_off') and msg.note in NOTAS_BASSDRUM:
            copied = msg.copy(time=acc_time)   # <---- AQUI CORRIGIDO
            copied.channel = 9
            bassdrum_track.append(copied)
            acc_time = 0

    if bassdrum_index is not None:
        mid.tracks[bassdrum_index] = bassdrum_track
    else:
        mid.tracks.append(bassdrum_track)
        bassdrum_index = len(mid.tracks) - 1


    # Cymbal
    cymbal_index = None
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.is_meta and msg.type == 'track_name' and msg.name == 'Cymbal':
                cymbal_index = i
                break

    cymbal_track = MidiTrack()
    cymbal_track.append(MetaMessage('track_name', name='Cymbal', time=0))
    NOTAS_CYMBAL = {49, 57}

    acc_time = 0
    for msg in drumkit_track:
        acc_time += msg.time
        if msg.type in ('note_on', 'note_off') and msg.note in NOTAS_CYMBAL:
            copied = msg.copy(time=acc_time)
            copied.channel = 9
            cymbal_track.append(copied)
            acc_time = 0

    if cymbal_index is not None:
        mid.tracks[cymbal_index] = cymbal_track
    else:
        mid.tracks.append(cymbal_track)
        cymbal_index = len(mid.tracks) - 1

    # Bongo (condicional)
    bongo = 'Bongo'
    bongo_track = None
    bongo_index = None

    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.is_meta and msg.type == 'track_name' and msg.name == bongo:
                bongo_index = i
                break

    NOTAS_BONGO = {60, 61, 62, 63, 64}

    has_bongo_notes = any(
        msg.type in ('note_on', 'note_off') and msg.note in NOTAS_BONGO
        for msg in drumkit_track
    )

    if has_bongo_notes:
        bongo_track = MidiTrack()
        bongo_track.append(MetaMessage('track_name', name='Bongo', time=0))

        acc_time = 0
        for msg in drumkit_track:
            acc_time += msg.time
            if msg.type in ('note_on', 'note_off') and msg.note in NOTAS_BONGO:
                copied = msg.copy(time=acc_time)
                if hasattr(copied, "channel") and copied.type in ("note_on", "note_off"):
                    copied.channel = 9
                bongo_track.append(copied)
                acc_time = 0

        bongo_track_limpa = remover_acordes_priorizar_maior(bongo_track)
        bongo_track_transposta = transpose_bongo(bongo_track_limpa)

        if bongo_index is not None:
            mid.tracks[bongo_index] = bongo_track_transposta
        else:
            mid.tracks.append(bongo_track_transposta)
            bongo_index = len(mid.tracks) - 1

    # BassDrum
    bassdrum_track_limpa = remover_acordes_priorizar_maior(bassdrum_track)
    bassdrum_track_transposta = transpose_bassdrum(bassdrum_track_limpa)
    mid.tracks[bassdrum_index] = bassdrum_track_transposta

    # SnareDrum
    snare_track_limpa = remover_acordes_priorizar_maior(snare_track)
    snare_track_transposta = transpose_snaredrum(snare_track_limpa)
    mid.tracks[snare_index] = snare_track_transposta

    # Cymbal
    cymbal_track_limpa = limpar_cymbal_prioridade(cymbal_track)
    cymbal_track_transposta = transpose_cymbal(cymbal_track_limpa)
    mid.tracks[cymbal_index] = cymbal_track_transposta

    base, ext = os.path.splitext(arquivo)
    if not ext:
        ext = ".mid"
    saida = f"{base} (MOD){ext}"

    mid.save(saida)
    return saida

# ---------- APP STREAMLIT ----------

def main():
    st.title("Drum MIDI Processor")
    st.write("Send a MIDI file and specify the **exact name** of the drum track (drumkit).")

    uploaded_file = st.file_uploader(
        "Select the MIDI file",
        type=["mid", "midi"]
    )

    drumkit_name = st.text_input(
        "Drum track name",
        placeholder="Ex: Drumkit"
    )

    processar = st.button("Process MIDI")

    if processar:
        if uploaded_file is None:
            st.warning("Please send a MIDI file.")
            return
        if not drumkit_name.strip():
            st.warning("Please enter the drum track name (drumkit_name).")
            return

        # Nome original do arquivo enviado
        nome_original = uploaded_file.name

        # Salva o upload em um arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            saida_path = processar_midi_bateria(tmp_path, drumkit_name=drumkit_name.strip())

            # Lê o arquivo gerado para oferecer download
            with open(saida_path, "rb") as f:
                midi_bytes = f.read()

            # Monta o nome de saída baseado no nome original do usuário
            base_original, ext_original = os.path.splitext(nome_original)
            if not ext_original:
                ext_original = ".mid"
            saida_nome = f"{base_original} (MOD){ext_original}"

            # Mensagem na tela usa apenas o nome "bonito"
            st.success(f"Generated file: {saida_nome}")

            st.download_button(
                label="⬇️ Download processed MIDI",
                data=midi_bytes,
                file_name=saida_nome,
                mime="audio/midi"
            )

        except Exception as e:
            st.error(f"Error processing MIDI: {e}")

if __name__ == "__main__":
    main()

