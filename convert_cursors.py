#!/usr/bin/env python3
"""
Windows to Linux Cursor Converter
Uses win2xcur to convert Windows cursor themes to Linux format
"""

import os
import sys
import shutil
import subprocess
import tempfile
import glob
from pathlib import Path
from typing import Dict, List, Optional

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Cursor mappings from Windows to Linux
CURSOR_MAPPINGS = {
    "Alternate": "bottom_left_corner bottom_right_corner bottom_side down-arrow left-arrow left_side right-arrow right_side top_left_corner top_right_corner top_side up_arrow",
    "Busy": "half-busy wait watch",
    "Cross": "cross crosshair",
    "Default": "arrow default left_ptr size-bdiag size-fdiag size-hor size-ver top_left_arrow",
    "Dgn1": "nw-resize nwse-resize se-resize size_fdiag",
    "Dgn2": "ne-resize nesw-resize sw-resize size_bdiag",
    "Hand": "draft pencil",
    "Help": "help left_ptr_help question_arrow whats_this",
    "Horizontal": "col-resize e-resize ew-resize h_double_arrow sb_h_double_arrow size_hor split_h w-resize",
    "Link": "grab hand hand1 hand2 openhand pointer pointing_hand",
    "Move": "all-scroll closedhand dnd-move dnd-none fleur grabbing move size_all",
    "Text": "ibeam text xterm",
    "Unavailable": "circle crossed_circle dnd_no_drop forbidden no_drop not_allowed",
    "Vertical": "n-resize ns-resize row-resize s-resize sb_v_double_arrow size_ver split_v v_double_arrow",
    "Work": "left_ptr_watch pirate progress"
}

class CursorConverter:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.input_dir = self.script_dir / "input"
        self.output_dir = self.script_dir / "output"
    
    def print_message(self, color: str, message: str):
        print(f"{color}{message}{Colors.NC}")
    
    def check_win2xcur(self) -> bool:
        try:
            subprocess.run(["win2xcur", "--help"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_message(Colors.RED, "Error: win2xcur is not installed or not in PATH")
            self.print_message(Colors.YELLOW, "Please install win2xcur from: https://github.com/quantum5/win2xcur")
            return False
    
    def create_directories(self) -> bool:
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)
            self.print_message(Colors.YELLOW, f"Created input directory: {self.input_dir}")
            self.print_message(Colors.BLUE, "Please place your Windows cursor folders (with .cur/.ani files and install.inf) in this directory")
            self.print_message(Colors.BLUE, "Each cursor theme should be in its own subfolder")
            return False
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.output_dir.exists():
            self.print_message(Colors.GREEN, f"Created output directory: {self.output_dir}")
        
        return True
    
    def find_cursor_files(self, directory: Path) -> List[Path]:
        cursor_files = []
        for pattern in ["*.cur", "*.ani"]:
            cursor_files.extend(directory.glob(pattern))
        return cursor_files
    
    def get_cursor_name_from_inf(self, inf_file: Optional[Path], cursor_file: Path) -> str:
        """Get cursor name from install.inf file or filename"""
        if inf_file and inf_file.exists():
            try:
                with open(inf_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for the file in the [Strings] section
                file_name = cursor_file.name
                for line in content.split('\n'):
                    if f'= "{file_name}"' in line:
                        cursor_var = line.split('=')[0].strip()
                        
                        mapping = {
                            "pointer": "Default",
                            "help": "Help",
                            "working": "Work",
                            "busy": "Busy",
                            "precision": "Cross",
                            "text": "Text",
                            "hand": "Hand",
                            "unavailable": "Unavailable",
                            "vert": "Vertical",
                            "horz": "Horizontal",
                            "dgn1": "Dgn1",
                            "dgn2": "Dgn2",
                            "move": "Move",
                            "alternate": "Alternate",
                            "link": "Link"
                        }
                        
                        return mapping.get(cursor_var.lower())
            except Exception:
                pass
        
        # Fallback: try to match by filename patterns
        base_name = cursor_file.stem.lower()
        
        if any(x in base_name for x in ["normal", "arrow", "default"]):
            return "Default"
        elif any(x in base_name for x in ["busy", "wait"]):
            return "Busy"
        elif any(x in base_name for x in ["text", "beam"]):
            return "Text"
        elif any(x in base_name for x in ["handwriting", "hand"]):
            return "Hand"
        elif "link" in base_name:
            return "Link"
        elif any(x in base_name for x in ["precision", "cross"]):
            return "Cross"
        elif "move" in base_name:
            return "Move"
        elif "help" in base_name:
            return "Help"
        elif any(x in base_name for x in ["unavailable", "no"]):
            return "Unavailable"
        elif any(x in base_name for x in ["vertical", "vert"]):
            return "Vertical"
        elif any(x in base_name for x in ["horizontal", "horz"]):
            return "Horizontal"
        elif any(x in base_name for x in ["diagonal1", "dgn1"]):
            return "Dgn1"
        elif any(x in base_name for x in ["diagonal2", "dgn2"]):
            return "Dgn2"
        elif any(x in base_name for x in ["working", "work", "progress"]):
            return "Work"
        elif any(x in base_name for x in ["alternate", "alt"]):
            return "Alternate"
        else:
            return None
    
    def convert_cursor_file(self, input_file: Path, output_dir: Path, 
                          cursor_name: str, linux_names: str) -> bool:
        self.print_message(Colors.BLUE, f"  Converting {cursor_name} -> {linux_names}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                result = subprocess.run([
                    "win2xcur", "-o", str(temp_path), str(input_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    converted_files = list(temp_path.glob("*"))
                    if converted_files:
                        converted_file = converted_files[0]
                        
                        for linux_name in linux_names.split():
                            shutil.copy2(converted_file, output_dir / linux_name)
                        
                        return True
            except Exception as e:
                self.print_message(Colors.RED, f"    Error converting {input_file.name}: {e}")
        
        return False
    
    def create_index_theme(self, theme_dir: Path, theme_name: str):
        index_file = theme_dir / "index.theme"
        
        content = f"""[Icon Theme]
Name={theme_name}
Comment=Converted Windows cursor theme: {theme_name}
Inherits=core
"""
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.print_message(Colors.BLUE, "  Created index.theme file")
    
    def process_cursor_theme(self, theme_dir: Path):
        theme_name = theme_dir.name
        output_theme_dir = self.output_dir / theme_name
        
        self.print_message(Colors.GREEN, f"Processing cursor theme: {theme_name}")
        
        cursors_dir = output_theme_dir / "cursors"
        cursors_dir.mkdir(parents=True, exist_ok=True)
        
        inf_files = list(theme_dir.glob("install.inf")) + list(theme_dir.glob("*.inf"))
        inf_file = inf_files[0] if inf_files else None
        
        cursor_files = self.find_cursor_files(theme_dir)
        
        if not cursor_files:
            self.print_message(Colors.YELLOW, f"  No cursor files found in {theme_name}")
            return
        
        converted_count = 0
        total_count = len(cursor_files)
        
        for cursor_file in cursor_files:
            cursor_name = self.get_cursor_name_from_inf(inf_file, cursor_file)
            
            if cursor_name is None:
                self.print_message(Colors.YELLOW, f"    Skipping unmapped cursor: {cursor_file.name}")
                continue
                
            linux_names = CURSOR_MAPPINGS.get(cursor_name, "")
            
            if linux_names:
                if self.convert_cursor_file(cursor_file, cursors_dir, cursor_name, linux_names):
                    converted_count += 1
                else:
                    self.print_message(Colors.RED, f"    Failed to convert: {cursor_file.name}")
            else:
                self.print_message(Colors.YELLOW, f"    No mapping found for: {cursor_name} ({cursor_file.name})")
        
        self.print_message(Colors.GREEN, f"  Converted {converted_count}/{total_count} cursor files")
        
        self.create_index_theme(output_theme_dir, theme_name)
    
    def run(self):
        self.print_message(Colors.BLUE, "Windows to Linux Cursor Converter")
        self.print_message(Colors.BLUE, "=================================")
        
        if not self.check_win2xcur():
            sys.exit(1)
        
        if not self.create_directories():
            sys.exit(0)
        
        theme_dirs = [d for d in self.input_dir.iterdir() if d.is_dir()]
        
        if not theme_dirs:
            self.print_message(Colors.YELLOW, f"No cursor theme directories found in {self.input_dir}")
            self.print_message(Colors.BLUE, "Please create subdirectories in input/ for each cursor theme")
            sys.exit(0)
        
        self.print_message(Colors.GREEN, f"Found {len(theme_dirs)} cursor theme(s) to process")
        
        for theme_dir in theme_dirs:
            self.process_cursor_theme(theme_dir)
            print()
        
        self.print_message(Colors.GREEN, "Conversion completed!")
        self.print_message(Colors.BLUE, f"Converted cursor themes are available in: {self.output_dir}")
        self.print_message(Colors.BLUE, "To install a theme, copy it to ~/.icons/ or /usr/share/icons/")

def main():
    converter = CursorConverter()
    converter.run()

if __name__ == "__main__":
    main()
