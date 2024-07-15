import random

class MusicTool:
    def __init__(self):
        self.scales = {
            'C': ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
            'G': ['G', 'A', 'B', 'C', 'D', 'E', 'F#'],
            'F': ['F', 'G', 'A', 'Bb', 'C', 'D', 'E']
        }
        self.chord_progressions = {
            'pop': ['I', 'V', 'vi', 'IV'],
            'blues': ['I', 'IV', 'I', 'V', 'IV', 'I'],
            'jazz': ['ii', 'V', 'I']
        }

    def generate_melody(self, key, length):
        return ' '.join(random.choices(self.scales[key], k=length))

    def generate_chord_progression(self, style, length):
        progression = random.choice(self.chord_progressions[style])
        return ' '.join(random.choices(progression, k=length))

    def generate_rhythm(self, length):
        patterns = ['x', '.', 'x', 'x', '.', 'x', '.', '.']
        return ' '.join(random.choices(patterns, k=length))

    def play_music(self, input_data):
        key = input_data.get('key', 'C')
        style = input_data.get('style', 'pop')
        length = input_data.get('length', 8)

        melody = self.generate_melody(key, length)
        chords = self.generate_chord_progression(style, length // 2)
        rhythm = self.generate_rhythm(length)

        return {
            'melody': melody,
            'chords': chords,
            'rhythm': rhythm
        }

music_tool = MusicTool()

def process_music_tool(input_data):
    return music_tool.play_music(input_data)
