#!/usr/bin/env python3
"""
Musical Note Player - Plays notes from a text file using PC speaker
Usage: python note_player.py <filename>

File format:
- First line: BPM (beats per minute)
- Remaining lines: Notes separated by spaces, periods for pauses
- Notes: A, B, C, D, E, F, G (case insensitive)
"""

import sys
import time
import argparse
import os

# Note frequencies in Hz - 3 octaves (3rd, 4th, 5th)
NOTE_FREQUENCIES = {
   # Lower octave (3rd octave) - marked with -
   '-C': 130.81,
   '-D': 146.83,
   '-E': 164.81,
   '-F': 174.61,
   '-G': 196.00,
   '-A': 220.00,
   '-B': 246.94,
   # Middle octave (4th octave) - no modifier
   'C': 261.63,
   'D': 293.66,
   'E': 329.63,
   'F': 349.23,
   'G': 392.00,
   'A': 440.00,
   'B': 493.88,
   # Higher octave (5th octave) - marked with +
   '+C': 523.25,
   '+D': 587.33,
   '+E': 659.25,
   '+F': 698.46,
   '+G': 783.99,
   '+A': 880.00,
   '+B': 987.77
}

def play_tone(frequency, duration):
   """
   Play a tone using the system beep functionality
   """
   try:
       if os.name == 'nt':  # Windows
           import winsound
           winsound.Beep(int(frequency), int(duration * 1000))
       else:  # Unix/Linux/Mac
           # Try different audio commands in order of preference
           commands = [
               f'play -n synth {duration} sine {frequency}',
               f'sox -n -t alsa default synth {duration} sine {frequency}',
               f'paplay <(sox -n -p synth {duration} sine {frequency})'
           ]
           
           played = False
           for cmd in commands:
               if os.system(f'{cmd} 2>/dev/null') == 0:
                   played = True
                   break
           
           if not played:
               # Fallback: print and sleep
               # print(f" {frequency:.1f}Hz", end=' ')
       time.sleep(duration)

def parse_music_file(filename):
   """
   Parse the music file and return BPM and list of notes
   """
   try:
       with open(filename, 'r') as file:
           lines = file.readlines()
       
       if not lines:
           raise ValueError("File is empty")
       
       # Parse BPM from first line
       bpm = int(lines[0].strip())
       if bpm <= 0:
           raise ValueError("BPM must be positive")
       
       # Parse notes from remaining lines
       notes = []
       for line in lines[1:]:
           line_notes = line.strip().split()
           notes.extend(line_notes)
       
       return bpm, notes
   
   except FileNotFoundError:
       print(f"Error: File '{filename}' not found")
       sys.exit(1)
   except ValueError as e:
       print(f"Error parsing file: {e}")
       sys.exit(1)
   except Exception as e:
       print(f"Error reading file: {e}")
       sys.exit(1)

def play_music(bpm, notes):
   """
   Play the sequence of notes at the specified BPM
   """
   # Calculate beat duration in seconds
   beat_duration = 60.0 / bpm
   
   print(f"Playing at {bpm} BPM (each beat = {beat_duration:.3f} seconds)")
   print(f"Total notes/beats: {len(notes)}")
   # print("Available notes: -C through -B (low), C through B (middle), +C through +B (high)")
   # print("Press Ctrl+C to stop\n")
   
   try:
       for i, note in enumerate(notes):
           note = note.upper().strip()
           
           # print(f"Beat {i+1:3d}: ", end='', flush=True)
           
           if note == '.' or note == '':
               # Pause/rest
               # print("(rest)")
               time.sleep(beat_duration)
           elif note in NOTE_FREQUENCIES:
               # Play the note
               frequency = NOTE_FREQUENCIES[note]
               # print(f"{note} ({frequency:.1f}Hz)")
               play_tone(frequency, beat_duration * 0.3)  # Short note duration
               time.sleep(beat_duration * 0.7)  # Most of beat is silence
           else:
               # Unknown note - treat as rest but warn
               # print(f"Unknown note '{note}' - treating as rest")
               time.sleep(beat_duration)
   
   except KeyboardInterrupt:
       print("\n\nPlayback stopped by user")
   except Exception as e:
       print(f"\nError during playback: {e}")

def main():
   parser = argparse.ArgumentParser(
       description="Play musical notes from a text file using PC speaker",
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
File format example:
120
G G D D E E D . C C B B A A G . D D C C B B A

First line: BPM (beats per minute)
Following lines: Notes (-C to -B for low, C to B for middle, +C to +B for high) and periods (.) for rests, space-separated
       """
   )
   
   parser.add_argument('filename', help='Text file containing the musical notes')
   parser.add_argument('--test', action='store_true', 
                      help='Test all notes (plays C D E F G A B)')
   
   args = parser.parse_args()
   
   if args.test:
       print("Testing all notes at 120 BPM...")
       test_notes = ['-C', '-D', '-E', '-F', '-G', '-A', '-B', 
                    'C', 'D', 'E', 'F', 'G', 'A', 'B',
                    '+C', '+D', '+E', '+F', '+G', '+A', '+B']
       play_music(120, test_notes)
       return
   
   # Parse and play the music file
   bpm, notes = parse_music_file(args.filename)
   play_music(bpm, notes)

if __name__ == "__main__":
   main()
