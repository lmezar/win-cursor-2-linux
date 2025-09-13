#!/bin/bash

# Windows to Linux Cursor Converter Script
# Uses win2xcur to convert Windows cursor themes to Linux format

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"

# Cursor mappings from Windows to Linux
declare -A mappings=(
  [Alternate]="bottom_left_corner bottom_right_corner bottom_side down-arrow left-arrow left_side right-arrow right_side top_left_corner top_right_corner top_side up_arrow"
  [Busy]="half-busy wait watch"
  [Cross]="cross crosshair"
  [Default]="arrow default left_ptr size-bdiag size-fdiag size-hor size-ver top_left_arrow"
  [Dgn1]="nw-resize nwse-resize se-resize size_fdiag"
  [Dgn2]="ne-resize nesw-resize sw-resize size_bdiag"
  [Hand]="draft pencil"
  [Help]="help left_ptr_help question_arrow whats_this"
  [Horizontal]="col-resize e-resize ew-resize h_double_arrow sb_h_double_arrow size_hor split_h w-resize"
  [Link]="grab hand hand1 hand2 openhand pointer pointing_hand"
  [Move]="all-scroll closedhand dnd-move dnd-none fleur grabbing move size_all"
  [Text]="ibeam text xterm"
  [Unavailable]="circle crossed_circle dnd_no_drop forbidden no_drop not_allowed"
  [Vertical]="n-resize ns-resize row-resize s-resize sb_v_double_arrow size_ver split_v v_double_arrow"
  [Work]="left_ptr_watch pirate progress"
)

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

check_win2xcur() {
    if ! command -v win2xcur &> /dev/null; then
        print_message $RED "Error: win2xcur is not installed or not in PATH"
        print_message $YELLOW "Please install win2xcur from: https://github.com/quantum5/win2xcur"
        exit 1
    fi
}

create_directories() {
    if [ ! -d "$INPUT_DIR" ]; then
        mkdir -p "$INPUT_DIR"
        print_message $YELLOW "Created input directory: $INPUT_DIR"
        print_message $BLUE "Please place your Windows cursor folders (with .cur/.ani files and install.inf) in this directory"
        print_message $BLUE "Each cursor theme should be in its own subfolder"
        exit 0
    fi
    
    if [ ! -d "$OUTPUT_DIR" ]; then
        mkdir -p "$OUTPUT_DIR"
        print_message $GREEN "Created output directory: $OUTPUT_DIR"
    fi
}

find_cursor_files() {
    local dir=$1
    find "$dir" -type f \( -name "*.cur" -o -name "*.ani" \) -print0 2>/dev/null | tr '\0' '\n'
}

get_cursor_name_from_inf() {
    local inf_file=$1
    local cursor_file=$2
    
    if [ ! -f "$inf_file" ]; then
        return 1
    fi
    
    # Extract filename with extension
    local file_name=$(basename "$cursor_file")
    
    # Look for the file in the [Strings] section of install.inf
    # Format: variable = "filename.ani"
    local cursor_var=$(grep -i "= \"${file_name}\"" "$inf_file" | head -1 | cut -d'=' -f1 | tr -d ' ' | tr -d '\t')
    
    if [ -n "$cursor_var" ]; then
        # Map the variable name to our cursor types
        case "$cursor_var" in
            pointer) echo "Default" ;;
            help) echo "Help" ;;
            working) echo "Work" ;;
            busy) echo "Busy" ;;
            precision) echo "Cross" ;;
            text) echo "Text" ;;
            hand) echo "Hand" ;;
            unavailable) echo "Unavailable" ;;
            vert) echo "Vertical" ;;
            horz) echo "Horizontal" ;;
            dgn1) echo "Dgn1" ;;
            dgn2) echo "Dgn2" ;;
            move) echo "Move" ;;
            alternate) echo "Alternate" ;;
            link) echo "Link" ;;
            *) echo "" ;;
        esac
    else
        # Fallback: try to match by filename patterns
        local base_name=$(basename "$cursor_file" | sed 's/\.[^.]*$//')
        case "$base_name" in
            *Normal*|*arrow*|*default*) echo "Default" ;;
            *Busy*|*wait*) echo "Busy" ;;
            *Text*|*beam*) echo "Text" ;;
            *Handwriting*|*hand*) echo "Hand" ;;
            *Link*) echo "Link" ;;
            *Precision*|*cross*) echo "Cross" ;;
            *Move*) echo "Move" ;;
            *Help*) echo "Help" ;;
            *Unavailable*|*no*) echo "Unavailable" ;;
            *Vertical*|*vert*) echo "Vertical" ;;
            *Horizontal*|*horz*) echo "Horizontal" ;;
            *Diagonal1*|*dgn1*) echo "Dgn1" ;;
            *Diagonal2*|*dgn2*) echo "Dgn2" ;;
            *Working*|*work*|*progress*) echo "Work" ;;
            *Alternate*|*alt*) echo "Alternate" ;;
            *) echo "" ;;
        esac
    fi
}

convert_cursor_file() {
    local input_file=$1
    local output_dir=$2
    local cursor_name=$3
    local linux_names=$4
    
    print_message $BLUE "  Converting $cursor_name -> $linux_names"
    
    local temp_dir=$(mktemp -d)
    
    if win2xcur -o "$temp_dir" "$input_file" 2>/dev/null; then
        local converted_file=$(find "$temp_dir" -type f | head -1)
        if [ -f "$converted_file" ]; then
            for linux_name in $linux_names; do
                cp "$converted_file" "$output_dir/$linux_name"
            done
            rm -rf "$temp_dir"
            return 0
        fi
    fi
    
    rm -rf "$temp_dir"
    return 1
}

process_cursor_theme() {
    local theme_dir=$1
    local theme_name=$(basename "$theme_dir")
    local output_theme_dir="$OUTPUT_DIR/$theme_name"
    
    print_message $GREEN "Processing cursor theme: $theme_name"
    
    mkdir -p "$output_theme_dir/cursors"
    
    local inf_file=$(find "$theme_dir" -name "install.inf" -o -name "*.inf" | head -1)
    
    # Find all cursor files
    local cursor_files=()
    while IFS= read -r -d '' file; do
        cursor_files+=("$file")
    done < <(find "$theme_dir" -type f \( -name "*.cur" -o -name "*.ani" \) -print0 2>/dev/null)
    
    if [ ${#cursor_files[@]} -eq 0 ]; then
        print_message $YELLOW "  No cursor files found in $theme_name"
        return
    fi
    
    local converted_count=0
    local total_count=${#cursor_files[@]}
    
    for cursor_file in "${cursor_files[@]}"; do
        local cursor_name=$(get_cursor_name_from_inf "$inf_file" "$cursor_file")
        
        if [ -z "$cursor_name" ]; then
            print_message $YELLOW "    Skipping unmapped cursor: $(basename "$cursor_file")"
            continue
        fi
        
        local linux_names="${mappings[$cursor_name]}"
        
        if [ -n "$linux_names" ]; then
            if convert_cursor_file "$cursor_file" "$output_theme_dir/cursors" "$cursor_name" "$linux_names"; then
                ((converted_count++))
            else
                print_message $RED "    Failed to convert: $(basename "$cursor_file")"
            fi
        else
            print_message $YELLOW "    No mapping found for: $cursor_name ($(basename "$cursor_file"))"
        fi
    done
    
    print_message $GREEN "  Converted $converted_count/$total_count cursor files"
    
    create_index_theme "$output_theme_dir" "$theme_name"
}

create_index_theme() {
    local theme_dir=$1
    local theme_name=$2
    local index_file="$theme_dir/index.theme"
    
    cat > "$index_file" << EOF
[Icon Theme]
Name=$theme_name
Comment=Converted Windows cursor theme: $theme_name
Inherits=core
EOF
    
    print_message $BLUE "  Created index.theme file"
}

main() {
    print_message $BLUE "Windows to Linux Cursor Converter"
    print_message $BLUE "================================="
    
    check_win2xcur
    create_directories
    
    local theme_dirs=()
    while IFS= read -r -d '' dir; do
        theme_dirs+=("$dir")
    done < <(find "$INPUT_DIR" -mindepth 1 -maxdepth 1 -type d -print0)
    
    if [ ${#theme_dirs[@]} -eq 0 ]; then
        print_message $YELLOW "No cursor theme directories found in $INPUT_DIR"
        print_message $BLUE "Please create subdirectories in input/ for each cursor theme"
        exit 0
    fi
    
    print_message $GREEN "Found ${#theme_dirs[@]} cursor theme(s) to process"
    
    for theme_dir in "${theme_dirs[@]}"; do
        process_cursor_theme "$theme_dir"
        echo
    done
    
    print_message $GREEN "Conversion completed!"
    print_message $BLUE "Converted cursor themes are available in: $OUTPUT_DIR"
    print_message $BLUE "To install a theme, copy it to ~/.icons/ or /usr/share/icons/"
}

main "$@"
