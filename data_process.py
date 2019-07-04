import numpy as np
from keras.utils import np_utils
from music21 import stream, note, chord, instrument
import midi_util


KeyToPitch = midi_util.KeyToPitch
OffsetStep = midi_util.OffsetStep

def prepare_sequences(data, sequence_length):
    """ Prepare the sequences used by the Neural Network """
    keyboard_size = len(KeyToPitch)
    
    # create a dictionary to map pitches to integers
    
    network_input = []
    network_output = []

    # create input sequences and the corresponding outputs
    for notes in data:
        for i in range(0, len(notes) - sequence_length, 1):
            sequence_in = notes[i:i + sequence_length]
            sequence_out = notes[i + sequence_length]
            network_input.append(sequence_in)
            network_output.append(sequence_out)

    # reshape the input into a format compatible with LSTM layers
    n_patterns = len(network_input)
    network_input = np.reshape(network_input, (n_patterns, sequence_length, keyboard_size))

    n_patterns = len(network_output)
    network_output = np.reshape(network_output, (n_patterns, keyboard_size))

    return (network_input, network_output)

def generate_notes(model, network_input):
    """ Generate notes from the neural network based on a sequence of notes """
    sequence_len = network_input.shape[1]
    pitch_size = network_input.shape[2]

    # random pattern
    # pattern = np.vstack((random_seq_pitch, random_seq_duraion)).T
    # random_pitch_indices = np.random.randint(pitch_size, size=sequence_len)
    # pattern = np_utils.to_categorical(random_pitch_indices, num_classes=pitch_size)
    # random sequence in network_input
    start = np.random.randint(0, len(network_input)-1)
    pattern = np.array(network_input[start])

    print(pattern.shape)

    prediction_output = []
    
    # generate 512 notes
    for _ in range(256):

         # random modify the pattern to prevent looping
        random_offset_index = np.random.randint(0, sequence_len-1)
        random_pitch_index = np.random.randint(0, pitch_size)
        copy_pattern = np.copy(pattern)
        copy_pattern[random_offset_index] = np_utils.to_categorical(random_pitch_index, num_classes=pitch_size)

        prediction_input = np.reshape(copy_pattern, (1, sequence_len, pitch_size))
        prediction = model.predict(prediction_input, verbose=0)
        predict_index = np.argmax(prediction)

        predict_pitch = KeyToPitch[predict_index]
        prediction_output.append(predict_pitch)

        pattern[0:-1] = pattern[1:]
        pattern[-1] = np_utils.to_categorical(predict_index, num_classes=pitch_size)



    return prediction_output

def create_midi(prediction_output, scale_name=None):
    offset = 0
    output_notes = []
    print(prediction_output)
    # create note and chord objects based on the values generated by the model
    for pitch in prediction_output:
        if pitch != 0:
            new_note = note.Note(pitch)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)
        else:
            new_note = note.Rest()
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)
        # increase offset each iteration so that notes do not stack
        offset += OffsetStep

    midi_stream = stream.Stream(output_notes)

    if scale_name:
        midi_util.to_major(midi_stream, scale_name)

    midi_stream.write('midi', fp='test_output.mid')