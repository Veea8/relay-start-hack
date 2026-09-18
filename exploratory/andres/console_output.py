# Script: console_output.py
# Purpose: Let an analysis script save everything it prints into a text file next to itself
# Author: Andrés Gallardo
# Date: September 2026

import sys
from pathlib import Path









#### Step 1: A writer that sends text to two places ####

# Pass every piece of printed text on to the console and to an open text file.
class ConsoleAndFileWriter:

    def __init__(self, console_stream, file_stream):
        self.console_stream = console_stream
        self.file_stream = file_stream

    def write(self, text):
        self.console_stream.write(text)
        self.file_stream.write(text)

    def flush(self):
        self.console_stream.flush()
        self.file_stream.flush()









#### Step 2: The function an analysis script calls once at its top ####

# Save all printed output of the calling script as <script name>_output.txt in the same folder.
def save_printed_output(script_path):
    script_path = Path(script_path)
    output_path = script_path.with_name(script_path.stem + "_output.txt")

    # Print accented characters correctly on a Windows console.
    sys.stdout.reconfigure(encoding="utf-8")

    output_file = open(output_path, "w", encoding="utf-8", newline="\n")
    sys.stdout = ConsoleAndFileWriter(sys.stdout, output_file)
    return output_path
