#!/bin/python3

import argparse
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Input, Static, Button, Label, Header
from textual.containers import Container, ScrollableContainer,Horizontal, Vertical
from textual.screen import Screen 
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from textual import on
from textual.screen import ModalScreen

import os
from pathlib import Path


import pyperclip
import csv
from pathlib import Path
import sys
import re
from typing import Optional

from helpscreen import HelpScreen
import formatstr
from functools import partial
import openfile
import savedialog
from yesnodialog import YesNoDialog
from utils import *
import funcstr
from undomanager import UndoManager
# command completion
from cmddesc import COMMAND_DESCRIPTIONS

PROGRAM_NAME = "TermCell"
PROGRAM_VERSION = "0.1"

class CSVEditor(App):
    COMMAND_PALETTE_BINDING = "ctrl+backslash"
    
    themes = {
        "dark": "textual-dark",
        "light": "textual-light",
        "vscode": "vscode-dark",
        "monokai": "monokai",
        "github": "github-dark",
        "dracula": "dracula",
    }
    
    BINDINGS = [
        Binding("ctrl+s", "save", "Save", key_display="^s"),
        Binding("ctrl+q", "", "Exit", key_display="^q"),
        Binding("ctrl+z", "undo", "Undo", key_display="^z"),
        Binding("ctrl+y", "redo", "Redo", key_display="^y"),
        #("ctrl+\\", "app.open_theme_picker", "Themes"),
        Binding("!", "help", "Help"), 
    ]
    """Terminal-based CSV editor with Vim-style key chords."""

    THEMES = {
        "textual-dark": {
            "primary": "ansi_bright_blue",
            "secondary": "ansi_bright_magenta",
            "surface": "ansi_black",
            "panel": "#1a1a1a",
            "text": "#ffffff",
            "text-muted": "#888888",
            "success": "ansi_green",
            "warning": "ansi_yellow",
            "error": "ansi_red",
        },
        "textual-light": {
            "primary": "ansi_blue",
            "secondary": "ansi_magenta",
            "surface": "ansi_white",
            "panel": "#f0f0f0",
            "text": "#000000",
            "text-muted": "#666666",
            "success": "ansi_green",
            "warning": "ansi_yellow",
            "error": "ansi_red",
        },
        "vscode": {
            "primary": "#569CD6",
            "secondary": "#C586C0",
            "surface": "#1E1E1E",
            "panel": "#252526",
            "text": "#D4D4D4",
            "text-muted": "#858585",
            "success": "#4EC9B0",
            "warning": "#DCDCAA",
            "error": "#F44747",
        },
        "arctic": {
              "primary": " #5e81ac",
              "secondary": " #81a1c1",
              "surface": " #3b4252",
              "panel": " #434c5e",
              "accent": " #88c0d0",
              "text": "#D4D4D4",
              "text-muted": "#858585",
              "foreground": " #eceff4",
              "background": " #2e3440",
              "success": " #a3be8c",
              "warning": " #ebcb8b",
              "error": " #bf616a",
          },
        "monokai": {
            "primary": "#A6E22E",
            "secondary": "#FD971F",
            "surface": "#272822",
            "panel": "#3E3D32",
            "text": "#F8F8F2",
            "text-muted": "#75715E",
            "success": "#A6E22E",
            "warning": "#FD971F",
            "error": "#F92672",
        },
    }


    CSS = """
    #cell_input {
        height: 3;
    }
    #status_line {
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    DataTable {
        height: 1fr;
    }
    .align-left {
        text-align: left;
    }
    .align-center {
        text-align: center;
    }
    .align-right {
        text-align: right;
    }
    .row-number {
        color: $primary-lighten-2;
        background: $surface-darken-1;
        text-align: center;
    }
    """
    # dialog css
    CSS += """
#dialog-container {
    padding: 1;
    background: $surface;
    border: panel $primary;
    width: 100%;
    height: 100%;
}

#fixed_top {
    height: auto;
    margin-bottom: 1;
}

#path_controls {
    height: auto;
    width: auto;
}

#filter_controls {
    height: auto;
}

.filter-select {
    width: 30;
}

.nav-button {
    width: 10;
    margin-right: 1;
}

#tree_container {
    height: 1.2fr;
    border: solid $primary;
}

.savedialog-top {
        height: 10;
        padding: 1;
        /* border: solid $accent; */
        background: $panel;
    }



#buttons_container {
    height: auto;
}

#button_row {
    height: auto;
    align: right middle;
}
.dialog-input {
        width: 1fr;
        margin-bottom: 0;
}
"""
    
    CSS += """
    /* Search match highlighting */
    .datatable--cell.match {
        background: $warning;
        color: $text;
    }

    .datatable--cell.current-match {
        background: $success;
        color: $text;
        text-style: bold;
    }
    """

    # --- State ---
    current_theme_index = 0
    count_buffer: reactive[str] = reactive("")
    current_file: reactive[Path | None] = reactive(None)
    current_cell = None
    cursor_mode: reactive[str] = reactive("cell")   # cell | row | column
    key_buffer: reactive[str] = reactive("")
    pending_column_insert: reactive[bool] = reactive(False)
    pending_goto_row: reactive[bool] = reactive(False)
    pending_goto_column: reactive[bool] = reactive(False)
    pending_column_insert_at_cursor: reactive[bool] = reactive(False)
    pending_width_reset: reactive[bool] = reactive(False)
    pending_column_width: reactive[bool] = reactive(False)
    #pending_yes_no: reactive[bool] = reactive(False)
    clipboard_cell: reactive[str | None] = reactive(None)
    clipboard_row: reactive[list[str] | None] = reactive(None)
    clipboard_column: reactive[list[str] | None] = reactive(None)
    clipboard_type: reactive[str] = reactive("")  # "cell", "row", "column"
    command_mode: reactive[bool] = reactive(False)
    command_buffer: reactive[str] = reactive("")
    search_mode: reactive[bool] = reactive(False)
    search_direction: reactive[str] = reactive("forward")  # "forward" or "backward"
    search_pattern: reactive[str] = reactive("")
    search_matches: reactive[list] = reactive([])
    current_match_index: reactive[int] = reactive(-1)
    thetable = None
    changed = False
    last_command = None
    last_command_args = None
    number_column_width = 3
    message_delay = 3
    
    
    def __init__(self, delimiter: str = ",", filename: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = delimiter
        self.changed = False
        self.dark = True
        self.undo_manager = None
        self.filename = filename  # Store filename passed from command line

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Cell editor / prompt", id="cell_input")
        yield Static("Ready", id="status_line")
        yield DataTable(id="table")
        yield Footer()
        

    def on_mount(self) -> None:
        self.theme = "textual-dark"
        
        self.thetable = self.query_one(DataTable)
        self.thetable.cursor_type = "cell"
        self.thetable.focus()
        
        self.undo_manager = UndoManager(self.thetable, max_history_size=30)
        self.thetable.fixed_columns = 1
        self.thetable.zebra_stripes = True
        
        # Initialize current cell to (0, 0)
        self.update_status_with_coords()
        
        if len(sys.argv) > 1:
            path = Path(sys.argv[1]).expanduser().resolve()
            if path.exists():
                self.load_csv(path)
                self.set_status(
                    f"Loaded: {path} | Delimiter: '{self.delimiter}'",
                    temporary=True
                )
            else:
                self.set_status(f"File not found: {path}")
                self.create_new_file()
        else:
            self.create_new_file()

    # def set_theme(self, theme_name: str) -> None:
        # for theme in self.THEMES:
            # self.set_class(theme, root=True, remove=True)
        # # Add the new one
        # self.set_class(theme_name, root=True)
        # self.current_theme_index = self.THEMES.index(theme_name)

    # def next_theme(self) -> None:
        # themes = list(self.THEMES.keys())
        # self.current_theme_index = (self.current_theme_index + 1) % len(self.THEMES)
        # self.set_theme(self.THEMES[themes[self.current_theme_index]])
        # self.set_status(f"Theme: {display_name}")

    # ============================================================
    # Undo Manager functions                    
    # ============================================================
        
    def save_state_before_change(self, action_description: str = ""):
        """Save current state before making changes."""
        if not self.undo_manager:
            return
        
        # Start tracking changes for delta snapshots
        self.undo_manager.start_tracking_changes()
        
        # Create snapshot
        snapshot_id = self.undo_manager.create_snapshot(action_description)
        
        if snapshot_id > 0:
            self.set_status(f"Saved state: {action_description}", temporary=True)

    # Update undo/redo methods:
    def undo(self) -> None:
        """Undo the last change (called from keyboard shortcuts)."""
        self._cmd_undo([])

    def redo(self) -> None:
        """Redo the last undone change (called from keyboard shortcuts)."""
        self._cmd_redo([])

    def _cmd_undo(self, args: list[str]) -> None:
        """Undo the last change."""
        if not self.undo_manager:
            self.set_status("Undo manager not initialized", temporary=True)
            return
        
        # Get count from args if provided (e.g., ":undo 3" to undo 3 times)
        count = 1
        if args:
            try:
                count = int(args[0])
            except ValueError:
                self.set_status(f"Invalid count: {args[0]}", temporary=True)
                return
        
        # Perform undo multiple times if count > 1
        for i in range(count):
            success, action = self.undo_manager.undo()
            if not success:
                if i == 0:
                    self.set_status(action, temporary=True)
                else:
                    self.set_status(f"Undid {i} actions (last: {action})", temporary=True)
                break
        
        if success:
            self.changed = True
            if count > 1:
                self.set_status(f"Undid {count} actions")
            else:
                self.set_status(f"Undo: {action}")
            
            # Update input field with current cell value
            if self.current_cell:
                value = self.thetable.get_cell_at(self.current_cell)
                inp = self.query_one("#cell_input", Input)
                inp.value = str(value)

    def _cmd_redo(self, args: list[str]) -> None:
        """Redo the last undone change."""
        if not self.undo_manager:
            self.set_status("Redo manager not initialized", temporary=True)
            return
        
        # Get count from args if provided
        count = 1
        if args:
            try:
                count = int(args[0])
            except ValueError:
                self.set_status(f"Invalid count: {args[0]}", temporary=True)
                return
        
        # Perform redo multiple times if count > 1
        for i in range(count):
            success, action = self.undo_manager.redo()
            if not success:
                if i == 0:
                    self.set_status(action, temporary=True)
                else:
                    self.set_status(f"Redid {i} actions (last: {action})", temporary=True)
                break
        
        if success:
            self.changed = True
            if count > 1:
                self.set_status(f"Redid {count} actions")
            else:
                self.set_status(f"Redo: {action}")
            
            # Update input field with current cell value
            if self.current_cell:
                value = self.thetable.get_cell_at(self.current_cell)
                inp = self.query_one("#cell_input", Input)
                inp.value = str(value)

    def _cmd_undo_info(self, args: list[str]) -> None:
        """Show undo/redo information."""
        if not self.undo_manager:
            self.set_status("Undo manager not available", temporary=True)
            return
        
        stats = self.undo_manager.get_stats()
        
        # Create status message
        msg = f"Undo: {len(self.undo_manager.undo_stack)} available"
        if self.undo_manager.can_undo():
            last_action = self.undo_manager.get_last_action()
            if last_action:
                msg += f" (last: {last_action[:30]}...)" if len(last_action) > 30 else f" (last: {last_action})"
        
        msg += f" | Redo: {len(self.undo_manager.redo_stack)} available"
        msg += f" | Disk: {stats.get('disk_used', 0) // 1024} KB"
        
        self.set_status(msg, temporary=False)
        
        # Show detailed history if requested
        if args and args[0] == "history":
            history = self.undo_manager.get_history_info()
            if history:
                import datetime
                self.notify("Recent undo history:")
                for item in history[:5]:  # Last 5 actions
                    dt = datetime.datetime.fromtimestamp(item['timestamp'])
                    time_str = dt.strftime("%H:%M:%S")
                    action_preview = item['action'][:40] + "..." if len(item['action']) > 40 else item['action']
                    self.notify(f"  {item['index']}: {action_preview} ({time_str})")
            else:
                self.notify("No undo history available")

    # Add action handlers:
    def action_undo(self) -> None:
        """Undo action."""
        self.undo()

    def action_redo(self) -> None:
        """Redo action."""
        self.redo()
        
    # suggestions
    
    def update_command_suggestions_simple(self, current_input: str) -> None:
        """Show command suggestions in status line."""
        if not current_input.startswith(":"):
            self.query_one("#status_line", Static).update("Ready")
            return
        
        partial = current_input[1:].strip().lower()
        
        if not partial:
            # Show hint about available commands
            self.set_status("Type command (w, q, e, help, undo, redo, fill...)", temporary=False)
            return
        
        # Get matching commands
        matches = []
        for cmd in COMMAND_DESCRIPTIONS.keys():
            if cmd.startswith(partial):
                matches.append(cmd)
        
        if matches:
            # Show matches in status line
            match_text = ", ".join(matches[:5])
            if len(matches) > 5:
                match_text += f" (+{len(matches)-5} more)"
            
            self.set_status(f"Suggestions: {match_text}", temporary=False)
        else:
            self.set_status(f"No command starting with '{partial}'", temporary=True)

    # Then in on_input_changed:
    def on_input_changed(self, event: Input.Changed) -> None:
        if self.command_mode:
            self.update_command_suggestions_simple(event.value)
    # ============================================================
    # Global Key Handling (Ctrl + Vim chords)
    # ============================================================

    def on_key(self, event: events.Key) -> None:
        # print(f"Key pressed: {event.key}")  # Add this line
        # self.notify(f"Key pressed: {event.key}")
        
        if len(self.screen_stack) > 1: return
        
        # Check if help screen is active
        # help_screen_active = any(isinstance(screen, HelpScreen) for screen in self.screen_stack)
        
        # If help screen is active, let it handle the key
        # if help_screen_active:
            # Don't process keys here when help screen is open
            # return
            
        # overlay = self.query("FileListOverlay")
        # if overlay:
            # # Get the overlay instance
            # overlay_widget = overlay.first()
            # if overlay_widget:
                # # Let overlay handle navigation keys
                # if event.key == "up":
                    # overlay_widget.key_up(event)
                    # return
                # elif event.key == "down":
                    # overlay_widget.key_down(event)
                    # return
                # elif event.key == "enter":
                    # overlay_widget.key_enter(event)
                    # return
                # elif event.key == "escape":
                    # overlay_widget.key_escape(event)
                    # return
        if event.key == "tab":
            # Exit command mode if active
            if self.command_mode:
                  self.thetable.focus()
                  self.command_mode = False
                  return
                  
        # Handle Escape 
        if event.key == "escape":
            # Exit command mode if active
            if self.command_mode:
                self.command_mode = False
                self.command_buffer = ""
                inp = self.query_one("#cell_input", Input)
                inp.placeholder = "Cell editor / prompt"
                inp.value = ""
                
                self.thetable.focus()
                self.set_status("Command mode cancelled", temporary=True)
                event.stop()
                return
                
            self.key_buffer = ""
            self.count_buffer = ""

        colon_keys = ["colon",":", "shift+;", "shift+:"]
        if event.key in colon_keys and not self.command_mode:
            self.command_mode = True
            self.command_buffer = ":"
            inp = self.query_one("#cell_input", Input)
            inp.value = ":"
            inp.placeholder = "Command mode (press Enter to execute, Esc to cancel)"
            inp.focus()
            event.stop()
            return
            
        if self.search_matches and not self.search_mode:
            if event.key == "n":  # n for next match
                self.find_next_match()
                event.stop()
                return
            elif event.key == "N":  # Shift+N for previous match
                self.find_prev_match()
                event.stop()
                return

        # Handle search mode entry
        if event.key == "slash" and not self.search_mode and not self.command_mode:
            self.enter_search_mode("forward")
            event.stop()
            return
        
        if event.key == "question_mark" and not self.search_mode and not self.command_mode:
            self.enter_search_mode("backward")
            event.stop()
            return
        
        #self.notify(event.key)
        if event.key == "period" or event.key == "." or event.key == "full_stop":
            if not self.command_mode and not self.search_mode:
                if self.last_command:
                    # Re-execute the stored command
                    #self.notify(str(self.last_command))
                    full_command = f":{self.last_command}"
                    if self.last_command_args:
                        full_command += f" {' '.join(self.last_command_args)}"
                    #self.execute_command(":"+full_command)
                    self.execute_command(":"+self.last_command)
                    self.set_status(f"Repeated: {self.last_command}", temporary=True)
                else:
                    self.set_status("No command to repeat", temporary=True)
                event.stop()
                return

        # Handle typing in search mode
        if self.search_mode:
            if event.key == "escape":
                self.exit_search_mode()
                event.stop()
                return
            elif event.key == "n" and not event.ctrl:  # n for next match
                self.find_next_match()
                event.stop()
                return
            elif event.key == "N" and event.shift:  # Shift+N for previous match
                self.find_prev_match()
                event.stop()
                return
            elif event.key == "backspace":
                # Update the pattern
                if self.search_pattern:
                    self.search_pattern = self.search_pattern[:-1]
                    self.update_search_input()
                event.stop()
                return
            elif event.character and event.character.isprintable():
                # Add to pattern (skip the prompt character if user types it)
                if event.character not in ["/", "?"]:
                    self.search_pattern += event.character
                    self.update_search_input()
                event.stop()
                return
            # Don't handle Enter here - let on_input_submitted handle it

            
        existing_help = self.query("HelpPopup")
        if existing_help:
            existing_help.remove()
            self.set_status("Help closed", temporary=True)
            event.stop()
            return
        # If input has focus and is empty, return focus to table
        inp = self.query_one("#cell_input", Input)
        if inp.has_focus and inp.value == "":
            
            self.thetable.focus()
            event.stop()
            return
        
        # --- Global Ctrl shortcuts ---
        if event.key == "ctrl+s":
            self.action_save()
            event.stop()
            return
        if event.key == "ctrl+q":
            self.action_quit()
            event.stop()
            return
        if event.key == "!":  # This should trigger the help action
            self.action_help()
            event.stop()
            return

        # --- Vim-style chords ---
        if event.key.isdigit():
            self.count_buffer += event.key
            event.stop()
            return
            
        if len(event.key) == 1 and event.key.isalpha():
            self.key_buffer += event.key
            # try:
                # table = self.query_one(DataTable)  # Get reference first if needed
            # except:
                # return
            count = int(self.count_buffer) if self.count_buffer else 1
            commands = {
                "dr": lambda: self.iremove_row(count),
                "dc": lambda: self.iremove_column(count),
                "ir": lambda: self.insert_row_at_cursor(count),  
                "ic": lambda: self.prompt_insert_column_at_cursor(), 
                "ar": lambda: self.append_row(count),
                "ac": lambda: self.prompt_insert_column(),
                "cl": lambda: self.set_cursor_mode("cell"),
                "cr": lambda: self.set_cursor_mode("row"),
                "cc": lambda: self.set_cursor_mode("column"),
                "fr": lambda: self.fixed_row(count),
                "fc": lambda: self.fixed_column(count),
                "sh": lambda: setattr(self.thetable, "show_header", not self.thetable.show_header),
                "sl": lambda: setattr(self.thetable, "show_row_labels", not self.thetable.show_row_labels),
                "sz": lambda: setattr(self.thetable, "zebra_stripes", not self.thetable.zebra_stripes),
                "sc": lambda: setattr(self.thetable, "show_cursor", not self.thetable.show_cursor),
                "sa": lambda: self.sort_current_column(ascending=True),
                "sd": lambda: self.sort_current_column(ascending=False),
                #"tt": lambda: self.action_open_theme_picker(),
                "tt": lambda: self.action_toggle_theme(),
                # copy/paste functions
                # Add copy/paste commands
                "yy": lambda: self.copy_selection(),  # Copy (yank)
                "dd": lambda: self.cut_selection(),   # Cut (delete and copy)
                "pp": lambda: self.paste_selection(), # Paste
                #":q": exit(),
                "gr": lambda: self.prompt_goto_row(),       # Go to row (prompt)
                "gc": lambda: self.prompt_goto_column(),    # Go to column (prompt)
                "wa": lambda: self.auto_width(),  # Auto width
                "wr": lambda: self.prompt_reset_widths(),  # Reset widths
                "wc": lambda: self.prompt_column_width(),
                # Relative movements
                "k": lambda: self.goto_cell(0, -count, True),   # Up
                "j": lambda: self.goto_cell(0, count, True),    # Down
                "h": lambda: self.goto_cell(-count, 0, True),   # Left
                "l": lambda: self.goto_cell(count, 0, True),    # Right
                "K": lambda: self.goto_cell(-2, 0, False),   # Top
                "J": lambda: self.goto_cell(-2, -1, False),    # Down
                "H": lambda: self.goto_cell(0, -2, False),   # Left
                "L": lambda: self.goto_cell(-1, -2, False),    # Right
                
                
            }  

            if self.key_buffer in commands:
                commands[self.key_buffer]()
                self.key_buffer = ""
                self.count_buffer = ""
                event.stop()
                return

            if len(self.key_buffer) > 2:
                self.key_buffer = ""
                self.count_buffer = ""

    # ============================================================
    # File Operations
    # ============================================================

    def get_column_letter(self, col_idx: int) -> str:
        """Convert 0-indexed column number to spreadsheet letter (A, B, C, ..., AA, AB, etc.)"""
        result = ""
        col_idx += 1  # Convert to 1-indexed for calculation
        
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            result = chr(65 + remainder) + result
        
        return result
    
    def load_csv(self, path: Path) -> None:
        
        self.thetable.clear(columns=True)

        with path.open(newline="") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            rows = list(reader)

        if not rows:
            return
        
        self.changed = False
        self.update_status_with_coords()  # Add this line if not already there
        self.thetable.focus()
    
        
        # Determine if first row looks like a header
        has_header = False
        if rows:
            # Check if first row has non-empty values
            first_row = rows[0]
            has_header = any(cell.strip() for cell in first_row)
        
        has_header = False
        # Add row number column first
        self.thetable.add_column("#", key="row_number", width=self.number_column_width)
        
        # Add spreadsheet-like column headers (A, B, C, ...)
        if rows:
            num_columns = len(rows[0])
            for col_idx in range(num_columns):
                # Convert to spreadsheet column letters (A, B, C, ..., AA, AB, etc.)
                col_letter = self.get_column_letter(col_idx)
                self.thetable.add_column(col_letter, key=f"col_{col_idx}")
        
        # Add rows with row numbers
        start_row = 1 if has_header else 0  # Skip header row if it exists
        for i, row in enumerate(rows[start_row:], start=1):
            # Pad row with empty values if needed
            padded_row = row + [""] * (num_columns - len(row))
            self.thetable.add_row(str(i), *padded_row)
        
        # Store original header if it exists
        self.original_header = rows[0] if has_header else []
        self.current_file = path
        self.set_status(f"Loaded: {path} (Columns: {num_columns}, Rows: {len(rows) - (1 if has_header else 0)})")

    def action_help(self) -> None:  # Add this method
        """Show help screen"""
        if any(isinstance(screen, HelpScreen) for screen in self.screen_stack):
            return  # Help screen already open
        self.push_screen(HelpScreen())
        #self.app.push_screen(HelpScreen())
        
    
#    def action_toggle_dark(self) -> None:
 #       self.dark = not self.dark # Toggles between True/False for dark mode
        # Or: self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"
        
    def action_toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        self.dark = not self.dark
    
    
    def _handle_quit_confirmation(self, quit_anyway: bool) -> None:
        if quit_anyway:
            self.exit()
        else:
            self.set_status("Quit cancelled", temporary=True)
            
    def _handle_reload_confirmation(self, quit_anyway: bool) -> None:
        if quit_anyway:
            self._cmd_reload([])
    
    def action_save(self) -> None:
        if not self.current_file:
            self.set_status("No file loaded")
            return

        # Use original header if available, otherwise use spreadsheet letters
        if hasattr(self, 'original_header') and self.original_header:
            headers = list(self.original_header)
            # Ensure header length matches number of data columns
            data_columns = len(self.thetable.columns) - 1  # Exclude row number column
            if len(headers) < data_columns:
                # Add missing headers as spreadsheet letters
                for i in range(len(headers), data_columns):
                    headers.append(self.get_column_letter(i))
            elif len(headers) > data_columns:
                # Truncate if there are more headers than columns
                headers = headers[:data_columns]
        else:
            # Use spreadsheet letters as headers
            headers = []
            for i in range(len(self.thetable.columns) - 1):  # Exclude row number column
                headers.append(self.get_column_letter(i))

        with self.current_file.open("w", newline="") as f:
            writer = csv.writer(f, delimiter=self.delimiter)
            #writer.writerow(headers)
            
            # Write rows without the row number
            for row_key in self.thetable.rows:
                row_data = self.thetable.get_row(row_key)
                # Skip the first value (row number)
                writer.writerow(row_data[1:])
        self.changed = False
        self.set_status(f"Saved: {self.current_file} (delimiter: '{self.delimiter}')")

    # ============================================================
    # Vim Structural Commands
    # ============================================================
    
    def save_file_callback(self, filename: Optional[str]) -> None:
        if not filename: return
        try:
            self.current_file = Path(filename)
            self.action_save()
        except PermissionError:
            self.notify("Permission denied to save file", severity="error")
        except OSError as e:
            self.notify(f"File system error: {e}", severity="error")
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")
    
    def _cmd_save(self, args: list[str]) -> None:
        """Save current file."""
        if args:
            # Save as different filename
            filename = args[0]
            old_file = self.current_file
            self.current_file = Path(filename)
            self.action_save()
            if old_file:
                self.current_file = old_file
            #self.set_status(f"Saved as: {filename}")
            self.notify(f"Saved as: {filename}")
        else:
            # Save current file
            self.action_save()
            
    def _cmd_save_dialog(self, args: list[str]) -> None:
        self.push_screen(savedialog.SaveFileDialog(), callback=self.save_file_callback)

    def _cmd_save_and_quit(self, args: list[str]) -> None:
        """Save and quit."""
        #self.action_save()
        self._cmd_save(args)
        self.exit()

    def _cmd_scan(self, args: list[str] = None) -> None:
        """Scan and replace special strings in table."""
        if args is None:
            args = []
        self.scan_and_replace_special_strings()

    
    def action_quit(self) -> None:
        self._cmd_quit([])
    
    def _cmd_quit(self, args: list[str]) -> None:
        """Quit if no unsaved changes."""
        if self.changed:
            self.push_screen(
                YesNoDialog("You have unsaved changes. Quit anyway?"),
                self._handle_quit_confirmation
            )
        else:
            self.exit()

    def _cmd_force_quit(self, args: list[str]) -> None:
        """Force quit without saving."""
        self.exit()
            
    def _cmd_edit(self, args: list[str]) -> None:
        """Edit a file."""
        if args:
            filename = args[0]
            path = Path(filename)
            if path.exists():
                self.load_csv(path)
                self.set_status(f"Editing: {filename}")
            else:
                self.set_status(f"File not found: {filename}", temporary=True)
        else:
            self.set_status("Usage: :e filename", temporary=True)

    def _handle_new_confirmation(self, quit_anyway: bool) -> None:
        if quit_anyway:
            self.create_new_file()
        else:
            self.set_status("Aborted!", temporary=True)
    
    def _cmd_new(self, args: list[str]) -> None:
        if self.changed:
            self.push_screen(
                YesNoDialog("You have unsaved changes. Procceed?"),
                self._handle_new_confirmation
            )
        else:
            self.create_new_file()

    def create_new_file(self):
        """Create new empty file."""
        
        self.thetable.clear(columns=True)
        
        # Add default columns
        self.thetable.add_column("#", key="row_number", width=self.number_column_width)
        self.thetable.add_column("A", key="col_0")
        self.thetable.add_column("B", key="col_1")
        
        for i in range(5):
            next_row_number = len(self.thetable.rows) + 1
            self.thetable.add_row(str(next_row_number), *([""] * (len(self.thetable.columns) - 1)))
        
        self.reset_widths(10)
        self.goto_cell(1, 0, False)
        
        # Clear original header
        if hasattr(self, 'original_header'):
            self.original_header = []
        
        self.current_file = None
        self.set_status("New file created")
        
    
    def _cmd_string_transform(self, args: list[str], transform_func) -> None:
        """Generic handler for string transformation commands"""
        if len(args) <= 0:
            # Get the function name for error message
            func_name = transform_func.__name__ if hasattr(transform_func, '__name__') else "transform"
            self.set_status(f"Usage: {func_name} $A12 or {func_name} $A1:B4")
            return
        
        try:
            funcstr.apply_cell_transform(self.thetable, args[0], transform_func)
            self.set_status(f"Applied {transform_func.__name__} to {args[0]}")
            self.changed = True
        except Exception as e:
            self.set_status(f"Error: {e}")

    def _cmd_fill(self, args: list[str]) -> None:
        if len(args) < 1:
            self.set_status("Usage: fill <cell> <string> ex. fill $A1:B4 N/A")
            return
        funcstr.fillstr(self.thetable, args[0], " ".join(args[1:]))
        
    def _cmd_replacestr(self, args: list[str]) -> None:
        if len(args) < 4:
            self.set_status("Usage: replace $A12 <old> <new> or lower $A1:B4 <old> <new>")
            return
        #funcstr.apply_cell_transform(self.thetable, args[0], str.replace, args[1], args[2])
    

    def _cmd_next(self, args: list[str]) -> None:
        """Go to next row."""
        
        if self.thetable.row_count > 0:
            current_row = self.thetable.cursor_coordinate.row
            next_row = (current_row + 1) % self.thetable.row_count
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(next_row, self.thetable.cursor_coordinate.column)
            self.set_status(f"Row {next_row + 1} of {self.thetable.row_count}")

    def _cmd_prev(self, args: list[str]) -> None:
        """Go to previous row."""
        
        if self.thetable.row_count > 0:
            current_row = self.thetable.cursor_coordinate.row
            prev_row = (current_row - 1) % self.thetable.row_count
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(prev_row, self.thetable.cursor_coordinate.column)
            self.set_status(f"Row {prev_row + 1} of {self.thetable.row_count}")

    def _cmd_first(self, args: list[str]) -> None:
        """Go to first row."""
        
        if self.thetable.row_count > 0:
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(0, self.thetable.cursor_coordinate.column)
            self.set_status("First row")

    def _cmd_last(self, args: list[str]) -> None:
        """Go to last row."""
        
        if self.thetable.row_count > 0:
            last_row = self.thetable.row_count - 1
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(last_row, self.thetable.cursor_coordinate.column)
            self.set_status(f"Last row ({last_row + 1})")

    def _cmd_help(self, args: list[str]) -> None:
        """Show help."""
        self.action_help()

    def _handle_reload(self, args: list[str]) -> None:
        if self.changed:
            self.push_screen(
                YesNoDialog("You have unsaved changes. Reload anyway?"),
                self._handle_reload_confirmation
            )
            return
    
    def _cmd_reload(self, args: list[str]) -> None:
        """Reload the current file from disk."""
            
        if not self.current_file:
            self.set_status("No file loaded to reload", temporary=True)
            return
        
        # Check if file still exists
        if not self.current_file.exists():
            self.set_status(f"File no longer exists: {self.current_file}", temporary=True)
            return
        
        # Ask for confirmation if there are unsaved changes
        # (optional - you can implement dirty flag tracking later)
        
        if self.thetable.row_count > 0:
            # For now, just warn but proceed
            self.set_status(f"Reloading {self.current_file.name} (unsaved changes will be lost!)", temporary=True)
        
        # Actually reload the file
        try:
            self.load_csv(self.current_file)
            self.set_status(f"Reloaded: {self.current_file.name}")
        except Exception as e:
            self.set_status(f"Failed to reload: {str(e)}", temporary=True)
    
    
    def _cmd_set(self, args: list[str]) -> None:
        """Set options."""
        if not args:
            self.set_status("Usage: :set option=value", temporary=True)
            return
        
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "number_width":
                    #self.thetable.show_row_labels = (value.lower() in ["1", "true", "yes", "on"])
                    self.number_column_width = int(value)
                    self.set_status(f"Width of number column set to: {value}")
                elif key == "delimiter":
                    self.delimiter=value
                    self.set_status(f"Delimiter set to: {self.delimiter}", temporary=True)
                elif key == "wrap":
                    self.set_status("Wrap not implemented yet", temporary=True)
                else:
                    self.set_status(f"Unknown option: {key}", temporary=True)
            else:
                self.set_status(f"Invalid set syntax: {arg}", temporary=True)
    
    def _cmd_column_width(self, args: list[str]) -> None:
        """Set width of current column."""
        if not args:
            self.set_status("Usage: :wc <width>", temporary=True)
            return
        
        try:
            width = int(args[0])
            if width <= 0:
                self.set_status("Width must be greater than 0", temporary=True)
                return
            
            # Get current column
            if not self.current_cell:
                self.set_status("No current column selected", temporary=True)
                return
            
            current_col = self.current_cell.column
            
            # Skip row number column
            if current_col == 0:  # row number column
                self.set_status("Cannot change width of row number column", temporary=True)
                return
            
            # Get column key
            col_keys = list(self.thetable.columns.keys())
            if current_col >= len(col_keys):
                self.set_status("Invalid column index", temporary=True)
                return
            
            col_key = col_keys[current_col]
            
            # Store all data before changing width
            column_keys = []
            for col_key_obj in self.thetable.columns.keys():
                column_keys.append(col_key_obj.value)
            
            # Store all row data
            all_rows = []
            for row_key in self.thetable.rows:
                row_data = []
                for col_key_temp in column_keys:
                    row_data.append(self.thetable.get_cell(row_key, col_key_temp))
                all_rows.append(row_data)
            
            # Store column labels
            column_labels = {}
            for col_key_temp in column_keys:
                column_labels[col_key_temp] = self.thetable.columns[col_key_temp].label
            
            # Clear and rebuild table with updated width
            cursor_pos = self.thetable.cursor_coordinate
            self.thetable.clear(columns=True)
            
            # Re-add columns with updated width for current column
            for idx, col_key_temp in enumerate(column_keys):
                if idx == current_col:
                    self.thetable.add_column(column_labels[col_key_temp], key=col_key_temp, width=width)
                elif col_key_temp == "row_number":
                    self.thetable.add_column(column_labels[col_key_temp], key=col_key_temp, width=self.number_column_width)
                else:
                    # Keep existing width for other columns
                    current_width = self.thetable.columns.get(col_key_temp)
                    if current_width and hasattr(current_width, 'width'):
                        self.thetable.add_column(column_labels[col_key_temp], key=col_key_temp, width=current_width.width)
                    else:
                        self.thetable.add_column(column_labels[col_key_temp], key=col_key_temp)
            
            # Re-add all rows
            for row_data in all_rows:
                self.thetable.add_row(*row_data)
            
            # Restore cursor position
            if cursor_pos and cursor_pos.row < self.thetable.row_count and cursor_pos.column < len(self.thetable.columns):
                try:
                    self.thetable.cursor_coordinate = cursor_pos
                    self.current_cell = cursor_pos
                except:
                    self.thetable.cursor_coordinate = type(cursor_pos)(0, 0)
                    self.current_cell = self.thetable.cursor_coordinate
            
            # Update input field
            if self.current_cell:
                value = self.thetable.get_cell_at(self.current_cell)
                inp = self.query_one("#cell_input", Input)
                inp.value = str(value)
            
            # Force refresh
            self.thetable.refresh(layout=True)
            
            # Update status
            self.update_status_with_coords()
            
            # Get column letter for display
            col_letter = self.get_column_letter(current_col - 1) if current_col > 0 else "#"
            self.set_status(f"Set column {col_letter} width to {width}")
            
        except ValueError:
            self.set_status(f"Invalid width: {args[0]}", temporary=True)

    def sort_current_column(self, ascending: bool = True) -> None:
        """Sort table based on current column values."""
        
        if not self.thetable.row_count or not self.thetable.columns:
            self.set_status("Table is empty", temporary=True)
            return
        
        if not self.current_cell:
            self.set_status("No current column selected", temporary=True)
            return
        
        current_col = self.current_cell.column
        
        # Cannot sort by row number column
        if current_col == 0:
            self.set_status("Cannot sort by row number column", temporary=True)
            return
        
        # Save cursor position
        original_cursor = self.current_cell
        
        # Get all rows with their current column value
        rows_with_values = []
        
        for row_idx in range(self.thetable.row_count):
            cell_coord = type(self.current_cell)(row_idx, current_col)
            cell_value = self.thetable.get_cell_at(cell_coord)
            
            # Convert to appropriate type for sorting
            sort_value = self._get_sortable_value(cell_value)
            
            # Store row data
            row_data = []
            for col_idx in range(len(self.thetable.columns)):
                col_coord = type(self.current_cell)(row_idx, col_idx)
                row_data.append(self.thetable.get_cell_at(col_coord))
            
            rows_with_values.append((sort_value, row_data))
        
        # Sort rows
        rows_with_values.sort(key=lambda x: (x[0][0], x[0][1]), reverse=not ascending)
        
        # Clear all rows
        for row_key in list(self.thetable.rows.keys()):
            self.thetable.remove_row(row_key)
        
        # Add sorted rows back with updated row numbers
        for i, (_, row_data) in enumerate(rows_with_values, start=1):
            # Update row number column (first column)
            row_data[0] = str(i)
            self.thetable.add_row(*row_data)
        
        self.changed = True
        
        # Move cursor to same column, first row
        try:
            self.thetable.cursor_coordinate = type(self.current_cell)(0, current_col)
            self.current_cell = self.thetable.cursor_coordinate
            
            # Update input field
            value = self.thetable.get_cell_at(self.current_cell)
            inp = self.query_one("#cell_input", Input)
            inp.value = str(value)
        except:
            pass
        
        # Update status
        self.update_status_with_coords()
        
        # Get column letter for display
        col_letter = self.get_column_letter(current_col - 1) if current_col > 0 else "#"
        sort_type = "ascending" if ascending else "descending"
        self.set_status(f"Sorted column {col_letter} in {sort_type} order ({self.thetable.row_count} rows)")

    def _get_sortable_value(self, value) -> any:
        """Convert cell value to sortable type with mixed-type handling."""
        if value is None or value == "":
            return (2, "")  # Put empty values at the end
        
        if isinstance(value, (int, float)):
            return (0, value)  # Numbers come first, with their numeric value
        
        if isinstance(value, str):
            stripped = value.strip()
            
            # Try numeric conversion
            try:
                # Check for integer
                if '.' not in stripped:
                    return (0, int(stripped))  # Numbers come first
                else:
                    return (0, float(stripped))  # Numbers come first
            except ValueError:
                pass
            
            # Return as string (type 1 means strings come after numbers)
            return (1, stripped.lower())
        
        # Default fallback for other types
        return (1, str(value))


    def _cmd_file_info(self, args: list[str]) -> None:
        """Show file information."""
        
        
        if self.current_file:
            file_info = f"File: {self.current_file.name}"
            if self.current_file.exists():
                size = self.current_file.stat().st_size
                file_info += f" ({size} bytes)"
        else:
            file_info = "File: (new file)"
        
        rows_info = f"Rows: {self.thetable.row_count}"
        cols_info = f"Columns: {len(self.thetable.columns) - 1}"  # Exclude row number
        
        #self.set_status(f"{file_info} | {rows_info} | {cols_info}", temporary=False)
        self.notify(f"{file_info} | {rows_info} | {cols_info}")
        
    def load_file_callback(self, filename: Optional[str]) -> None:
        if not filename:
            return
        try:
            path = Path(filename)
            if path.exists():
                self.load_csv(path)

            self.set_status(f"Loaded: {path} | Delimiter: '{self.delimiter}'", temporary=True)
        except FileNotFoundError:
            self.notify("File not found", severity="error")
        except PermissionError:
            self.notify("Permission denied to read file", severity="error")
        except UnicodeDecodeError:
            self.notify("File encoding error - try UTF-8 encoded file", severity="error")
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def _cmd_openfile(self, args: list[str]) -> None:
      
        if self.changed:
            self.push_screen(
                YesNoDialog("You have unsaved changes. Procceed?"),
                self._handle_openfile_confirmation
            )
        else:
            self.push_screen(openfile.OpenFileDialog(), callback=self.load_file_callback)
            
    
    def _handle_openfile_confirmation(self, quit_anyway: bool) -> None:
        if quit_anyway:
            self.push_screen(openfile.OpenFileDialog(), callback=self.load_file_callback)
        else:
            self.set_status("Aborted!", temporary=True)


    def _cmd_messages(self, args: list[str]) -> None:
        """Show message history."""
        # For now, just show a placeholder
        self.set_status("Message history not implemented", temporary=True)
    
    
    def execute_command(self, command: str) -> None:
        """Execute a Vim-style command."""
        # Remove leading colon and whitespace
        cmd = command.lstrip(":").strip().lower()
        
        if not cmd:
            self.set_status("Empty command", temporary=True)
            return
        
        # Split command and arguments
        parts = cmd.split()
        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd not in ['r','r!','e','e!']:
            self.last_command = cmd
            self.last_command_args = args
        
        # Command dictionary
        commands = {
            # Undo Operations
            "u": self._cmd_undo,
            "undo": self._cmd_undo,
            "redo": self._cmd_redo,
            
            # File operations
            "w": self._cmd_save,
            "wq": self._cmd_save_and_quit,
            "wd": self._cmd_save_dialog,
            "r!": self._cmd_reload,
            "r": self._handle_reload,
            "reload": self._cmd_reload,
            "q": self._cmd_quit,
            "quit": self._cmd_quit,
            "q!": self._cmd_force_quit,
            "quit!": self._cmd_force_quit,
            "e": self._cmd_edit,
            "edit": self._cmd_edit,
            "ed": self._cmd_openfile,
            "new": self._cmd_new,
            "calc": self._cmd_scan,
            
            # Navigation
            "n": self._cmd_next,
            "next": self._cmd_next,
            "prev": self._cmd_prev,
            "previous": self._cmd_prev,
            "first": self._cmd_first,
            "last": self._cmd_last,
            
            # Various
            "fill": self._cmd_fill,
            
            # String Functions
            "lower": lambda self, args: self._cmd_string_transform(args, str.lower),
            "upper": lambda self, args: self._cmd_string_transform(args, str.upper),
            "strip": lambda self, args: self._cmd_string_transform(args, str.strip),
            "title": lambda self, args: self._cmd_string_transform(args, str.title),
            "isalpha": lambda self, args: self._cmd_string_transform(args, str.isalpha),
            "capitalize": lambda self, args: self._cmd_string_transform(args, str.capitalize),
            "swapcase": lambda self, args: self._cmd_string_transform(args, str.swapcase),
            'isalnum': lambda self, args: self._cmd_string_transform(args, str.isalnum),
            'isascii': lambda self, args: self._cmd_string_transform(args, str.isascii),
            'isdecimal': lambda self, args: self._cmd_string_transform(args, str.isdecimal),
            'isdigit': lambda self, args: self._cmd_string_transform(args, str.isdigit),
            'islower': lambda self, args: self._cmd_string_transform(args, str.islower),
            'isnumeric': lambda self, args: self._cmd_string_transform(args, str.isnumeric),
            'isprintable': lambda self, args: self._cmd_string_transform(args, str.isprintable),
            'isspace': lambda self, args: self._cmd_string_transform(args, str.isspace),
            'istitle': lambda self, args: self._cmd_string_transform(args, str.istitle),
            'isupper': lambda self, args: self._cmd_string_transform(args, str.isupper),
            'lstrip': lambda self, args: self._cmd_string_transform(args, str.lstrip),
            
            "wc": self._cmd_column_width,
            
            # Help
            "h": self._cmd_help,
            "help": self._cmd_help,
            
            # Settings
            "set": self._cmd_set,
            
            # Info
            "f": self._cmd_file_info,
            "file": self._cmd_file_info,
        }
        
        string_functions = ['lower',
        'upper',
        'title',
        'strip',
        'capitalize',
        'isalpha',
        'swapcase',
        'isalpha',
        'isalnum',
        'isascii',
        'isdecimal',
        'isdigit',
        'islower',
        'isnumeric',
        'isprintable',
        'isspace',
        'istitle',
        'isupper',
        'lstrip'
        
        ]
        
        # Execute the command
        if cmd_name in string_functions:
            try:
                commands[cmd_name](self, args)
            except Exception as e:
                self.set_status(f"Command error: {str(e)}", temporary=True)
        elif cmd_name in commands:
            try:
                commands[cmd_name](args)
            except Exception as e:
                self.set_status(f"Command error: {str(e)}", temporary=True)
        else:
            self.set_status(f"Unknown command: {cmd_name}", temporary=True)
    
    def prompt_column_width(self) -> None:
        """Prompt user for column width for current column."""
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        
        # Get current column letter for better UX
        if self.current_cell and self.current_cell.column > 0:
            col_letter = self.get_column_letter(self.current_cell.column - 1)
            inp.placeholder = f"Enter width for column {col_letter} (current: ?)"
        else:
            inp.placeholder = "Enter width for current column"
        
        inp.focus()
        self.pending_column_width = True
    
    def prompt_goto_row(self) -> None:
        """Prompt user for row number to go to."""
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "Enter row number (1-indexed) or 0 for last"
        inp.focus()
        self.pending_goto_row = True

    def prompt_goto_column(self) -> None:
        """Prompt user for column number to go to."""
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "Enter column number (1-indexed) or 0 for last"
        inp.focus()
        self.pending_goto_column = True

    def execute_goto_row(self, row_input: str) -> None:
        """Execute goto row command."""
        try:
            if row_input == "0":
                row = -1  # Last row
            else:
                row = int(row_input) - 1  # Convert 1-indexed to 0-indexed
            
            # Go to current column, specified row
            
            current_col = self.thetable.cursor_coordinate.column
            self.goto_cell(current_col, row, False)
        except ValueError:
            self.set_status(f"Invalid row number: {row_input}", temporary=True)

    def execute_goto_column(self, col_input: str) -> None:
        """Execute goto column command."""
        try:
            col = int(col_input)
            current_row = self.thetable.cursor_coordinate.row
            self.goto_cell(col, current_row, False)
        except ValueError:
            self.set_status(f"Invalid column number: {col_input}", temporary=True)
    
    def goto_cell(self, x: int = -1, y: int = -1, relative: bool = False) -> None:
        """
        Move cursor to specified cell coordinates.
        
        Args:
            x: Column index (0-indexed). 
               Use -1 for last column, -2 to keep current column.
            y: Row index (0-indexed).
               Use -1 for last row, -2 to keep current row.
            relative: If True, x and y are offsets from current position.
                      If False, x and y are absolute coordinates.
        """
        
        
        if not self.thetable.row_count or not self.thetable.columns:
            self.set_status("Table is empty", temporary=True)
            return
        
        # Get current position
        current_row, current_col = self.thetable.cursor_coordinate.row, self.thetable.cursor_coordinate.column
        
        # Calculate target coordinates
        if relative:
            # Relative movement: add offsets to current position
            target_row = current_row + y
            target_col = current_col + x
        else:
            # Absolute movement: use provided coordinates
            # Handle -2 as "keep current"
            target_row = current_row if y == -2 else y
            target_col = current_col if x == -2 else x
        
        # Handle -1 values (go to last row/column)
        if target_row == -1:
            target_row = self.thetable.row_count - 1
        if target_col == -1:
            target_col = len(self.thetable.columns) - 1
        
        # Validate coordinates are within bounds
        if target_row < 0 or target_row >= self.thetable.row_count:
            self.set_status(f"Row {target_row + 1} is out of bounds (1-{self.thetable.row_count})", temporary=True)
            return
        if target_col < 0 or target_col >= len(self.thetable.columns):
            self.set_status(f"Column {target_col + 1} is out of bounds (1-{len(self.thetable.columns)})", temporary=True)
            return
        
        # Move cursor
        #table.cursor_coordinate = DataTable.Coordinate(target_row, target_col)
        
        self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(target_row, target_col)
        
        # Update display
        self.current_cell = self.thetable.cursor_coordinate
        value = self.thetable.get_cell_at(self.current_cell)
        inp = self.query_one("#cell_input", Input)
        inp.value = str(value)
        self.update_status_with_coords()
        
        # Status message
        if relative:
            direction_x = "right" if x > 0 else "left" if x < 0 else ""
            direction_y = "down" if y > 0 else "up" if y < 0 else ""
            
            if x != 0 and y != 0:
                msg = f"Moved {abs(y)} rows {direction_y}, {abs(x)} cols {direction_x}"
            elif x != 0:
                msg = f"Moved {abs(x)} columns {direction_x}"
            elif y != 0:
                msg = f"Moved {abs(y)} rows {direction_y}"
            else:
                msg = "Stayed at current cell"
        else:
            # Show which coordinates changed
            changes = []
            if y != -2 and y != current_row:
                changes.append(f"row {target_row + 1}")
            if x != -2 and x != current_col:
                changes.append(f"col {target_col + 1}")
            
            if changes:
                msg = f"Moved to {' and '.join(changes)}"
            else:
                msg = "Stayed at current cell"
        
        #self.set_status(msg, temporary=True)
    

    def insert_column_at_cursor(self, header: str) -> None:
        """Insert column at cursor position."""
        # Don't insert if trying to add another row number column
        if header.lower() in ["#", "row_number"]:
            self.set_status("Cannot insert row number column - already exists")
            return
        
        # Get current column position (0-indexed)
        current_col = self.thetable.cursor_coordinate.column
        
        # Calculate where to insert among data columns
        data_insert_at = current_col - 1 if current_col > 0 else 0
        
        # Get column keys - need to get the actual key values
        column_keys = []
        for col_key_obj in self.thetable.columns.keys():
            # ColumnKey object has a .value attribute
            column_keys.append(col_key_obj.value)
        
        # Collect all rows data
        all_rows = []
        for row_key in self.thetable.rows:
            row_data = []
            for col_key in column_keys:
                row_data.append(self.thetable.get_cell(row_key, col_key))
            all_rows.append(row_data)
        
        # Clear the entire table
        self.thetable.clear(columns=True)
        
        # Re-add row number column
        self.thetable.add_column("#", key="row_number", width=self.number_column_width)
        
        # Re-add all data columns with new column inserted
        num_data_cols = len(column_keys) - 1  # Exclude row_number
        for col_idx in range(num_data_cols + 1):  # +1 for new column
            col_letter = self.get_column_letter(col_idx)
            self.thetable.add_column(col_letter, key=f"col_{col_idx}")
        
        # Reconstruct all rows with new column inserted
        for row_idx, original_row in enumerate(all_rows):
            new_row = []
            
            # Add row number
            new_row.append(original_row[0])
            
            # Add data cells with empty value inserted at correct position
            for data_idx in range(num_data_cols + 1):  # +1 for new column
                if data_idx == data_insert_at:
                    # Empty value for new column
                    new_row.append("")
                
                if data_idx < num_data_cols:
                    # Get value from original row (skip row_number at index 0)
                    new_row.append(original_row[data_idx + 1])  # +1 to skip row_number
            
            # If inserting at the very end
            if data_insert_at == num_data_cols:
                new_row.append("")
            
            self.thetable.add_row(*new_row)
        
        # Update original header
        if not hasattr(self, 'original_header') or self.original_header is None:
            self.original_header = [""] * num_data_cols
        
        # Insert header at correct position
        if data_insert_at <= len(self.original_header):
            self.original_header.insert(data_insert_at, header)
        else:
            # Pad with empty strings if needed
            while len(self.original_header) < data_insert_at:
                self.original_header.append("")
            self.original_header.append(header)
        
        # Move cursor to the new column
        new_cursor_col = data_insert_at + 1  # +1 for row_number
        if new_cursor_col < len(self.thetable.columns):
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(self.thetable.cursor_coordinate.row, new_cursor_col)
            self.current_cell = self.thetable.cursor_coordinate
        
        # Update input field
        if self.current_cell:
            value = self.thetable.get_cell_at(self.current_cell)
            inp = self.query_one("#cell_input", Input)
            inp.value = str(value)
        
        # Update status
        self.update_status_with_coords()
        
        col_letter = self.get_column_letter(data_insert_at)
        self.set_status(f"Inserted column '{col_letter}' at position {current_col + 1} with header: {header}")
        self.changed = True
    
    def insert_row_at_cursor(self, count: int = 1) -> None:
        """Insert row(s) at cursor position."""
        
        
        if not self.thetable.row_count:
            # If table is empty, just add rows at the end
            for i in range(count):
                self.thetable.add_row("1", *([""] * (len(self.thetable.columns) - 1)))
            self.set_status(f"Inserted {count} row(s)")
            return
        
        # Get current row position (0-indexed)
        current_row = self.thetable.cursor_coordinate.row
        
        # Get column keys - need to get the actual key values
        column_keys = []
        for col_key_obj in self.thetable.columns.keys():
            column_keys.append(col_key_obj.value)
        
        # Collect all rows data
        all_rows = []
        for row_key in self.thetable.rows:
            row_data = []
            for col_key in column_keys:
                row_data.append(self.thetable.get_cell(row_key, col_key))
            all_rows.append(row_data)
        
        # Clear all rows from table (but keep columns)
        for row_key in list(self.thetable.rows.keys()):
            self.thetable.remove_row(row_key)
        
        # Re-add all rows with inserted empty rows
        row_num = 1
        for i in range(len(all_rows) + count):
            if i == current_row:
                # This is where we insert empty rows
                for j in range(count):
                    # Create empty row
                    empty_row = []
                    for col_idx, col_key in enumerate(column_keys):
                        if col_key == "row_number":
                            empty_row.append(str(row_num))
                        else:
                            empty_row.append("")
                    self.thetable.add_row(*empty_row)
                    row_num += 1
            
            if i < len(all_rows):
                # Update row number for existing row
                row_data = all_rows[i]
                for col_idx, col_key in enumerate(column_keys):
                    if col_key == "row_number":
                        row_data[col_idx] = str(row_num)
                self.thetable.add_row(*row_data)
                row_num += 1
        
        # Move cursor to the first inserted row
        if current_row < self.thetable.row_count:
            self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(current_row, self.thetable.cursor_coordinate.column)
            self.current_cell = self.thetable.cursor_coordinate
        
        # Update input field
        if self.current_cell:
            value = self.thetable.get_cell_at(self.current_cell)
            inp = self.query_one("#cell_input", Input)
            inp.value = str(value)
        
        # Update status
        self.update_status_with_coords()
        
        self.set_status(f"Inserted {count} row(s) at row {current_row + 1}")
        self.changed = True
    
    def append_row(self, count: int = 1) -> None:
        """Append row(s) at the end of the table."""
        
        for i in range(count):
            next_row_number = len(self.thetable.rows) + 1
            self.thetable.add_row(str(next_row_number), *([""] * (len(self.thetable.columns) - 1)))
        self.changed = True
        self.set_status(f"Appended {count} row(s)")
    
    def prompt_insert_column_at_cursor(self) -> None:
        """Prompt user for column header and insert at cursor position."""
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "New column header (insert at cursor)"
        inp.focus()
        self.pending_column_insert_at_cursor = True

    def iremove_row(self, count: int = 1) -> None:
        
        for _ in range(count):
            row_key, _ = self.thetable.coordinate_to_cell_key(self.thetable.cursor_coordinate)
            self.thetable.remove_row(row_key)
        
        # Renumber all rows after deletion
        self.renumber_rows()
        self.changed = True
        self.set_status("Removed row")

    def renumber_rows(self) -> None:
        """Renumber all rows in the table"""
        
        if "row_number" not in self.thetable.columns:
            return
        
        # Get all row keys
        row_keys = list(self.thetable.rows.keys())
        
        # Update row numbers
        for i, row_key in enumerate(row_keys, start=1):
            self.thetable.update_cell(row_key, "row_number", str(i))
        
    def iremove_column(self, count: int = 1) -> None:
        
        for _ in range(count):
            _, column_key = self.thetable.coordinate_to_cell_key(self.thetable.cursor_coordinate)
            self.thetable.remove_column(column_key)
        self.changed = True
        self.set_status("Removed column")
        
    def fixed_column(self, count: int = 1) -> None:
        self.thetable.fixed_columns = count
        self.set_status(f"Set {count} fixed column(s)")
        
    def fixed_row(self, count: int = 1) -> None:
        self.thetable.fixed_rows = count
        self.set_status(f"Set {count} fixed row(s)")

    def prompt_insert_column(self) -> None:
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "New column header"
        inp.focus()
        self.pending_column_insert = True

    def append_column(self, header: str) -> None:
        """Append column at the end of the table."""
        
        # Don't insert if trying to add another row number column
        if header.lower() in ["#", "row_number"]:
            self.set_status("Cannot insert row number column - already exists")
            return
        
        # Determine the next spreadsheet letter
        num_data_cols = len(self.thetable.columns) - 1  # Exclude row number column
        next_letter = self.get_column_letter(num_data_cols)
        
        self.thetable.add_column(next_letter, key=f"col_{num_data_cols}")
        
        # Update original header if it exists
        if hasattr(self, 'original_header'):
            self.original_header.append(header)
        else:
            # Initialize original header with empty values for previous columns
            self.original_header = [""] * num_data_cols + [header]
        
        for row_key in self.thetable.rows:
            self.thetable.update_cell(row_key, f"col_{num_data_cols}", "")
        self.changed = True
        self.set_status(f"Appended column '{next_letter}' with header: {header}")

    def set_cursor_mode(self, mode: str) -> None:
        
        self.thetable.cursor_type = mode
        self.cursor_mode = mode
        self.set_status(f"Cursor mode: {mode}")

    def align(self, how: str) -> None:
        
        cls = f"align-{how}"

        if not self.current_cell:
            return

        r = self.current_cell.row
        c = self.current_cell.column

        if self.cursor_mode == "cell":
            self.thetable.set_cell_class(self.current_cell, cls)

        elif self.cursor_mode == "row":
            for col in range(len(self.thetable.columns)):
                self.thetable.set_cell_class((r, col), cls)

        elif self.cursor_mode == "column":
            for row in range(len(self.thetable.rows)):
                self.thetable.set_cell_class((row, c), cls)

        self.set_status(f"Align {how}")

    # ============================================================
    # Cell Editing
    # ============================================================

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        self.current_cell = event.coordinate
        
        value = self.thetable.get_cell_at(event.coordinate)
        inp = self.query_one("#cell_input", Input)
        inp.value = str(value)
        inp.focus()
        
        # Update status with coordinates
        self.update_status_with_coords()
        #self.set_status(f"{event.coordinate.row+1}C{event.coordinate.column+1}", temporary=True)
    
    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        """Called when cursor moves to highlight a cell"""
        self.current_cell = event.coordinate
        
        value = self.thetable.get_cell_at(event.coordinate)
        inp = self.query_one("#cell_input", Input)
        inp.value = str(value)

        # Update status with coordinates
        self.update_status_with_coords()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Called when a row is highlighted (in row mode)."""
        
        current_row, current_col = self.thetable.cursor_coordinate.row, self.thetable.cursor_coordinate.column
        self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(event.cursor_row, current_col)
        self.current_cell = self.thetable.cursor_coordinate
        self.update_status_with_coords()

    def on_data_table_column_highlighted(self, event: DataTable.ColumnHighlighted) -> None:
        """Called when a column is highlighted (in column mode)."""
        
        current_row, current_col = self.thetable.cursor_coordinate.row, self.thetable.cursor_coordinate.column
        self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(current_row, event.cursor_column)
        self.current_cell = self.thetable.cursor_coordinate
        
        self.update_status_with_coords()

    
    def update_status_with_coords(self) -> None:
        if len(self.screen_stack) > 1:
            return
            
        """Update status bar with current coordinates and cell value"""
        if not self.current_cell:
            self.set_status("Ready")
            return
        
        row, col = self.current_cell.row, self.current_cell.column
        
        # Get cell value
        try:
            cell_value = self.thetable.get_cell_at(self.current_cell)
            if cell_value is None:
                cell_value = ""
        except:
            cell_value = ""
        
        # Truncate long values for display
        display_value = str(cell_value)
        if len(display_value) > 30:
            display_value = display_value[:27] + "..."
        
        # Get column info
        col_letter = self.get_column_letter(col - 1) if col > 0 else "#"  # Adjust for row number column
        
        # Get original header if available
        original_header = ""
        if hasattr(self, 'original_header') and self.original_header and col > 0:
            header_idx = col - 1  # Adjust for row number column
            if header_idx < len(self.original_header):
                original_header = self.original_header[header_idx]
                if original_header.strip():
                    #col_info = f"{col_letter} ({original_header})"
                    col_info = f"Name: {original_header}"
                else:
                    col_info = col_letter
            else:
                col_info = col_letter
        else:
            col_info = col_letter
        
        # Format coordinates (1-indexed for user)
        coord_text = f"{row+1}: {col+1} | {col_letter}{row+1} | {col_info}"
        
        # Create status message
        status_msg = f"{coord_text}"
        
        # Add file info if available
        if self.current_file:
            status_msg = f"{self.current_file.name} | {status_msg}"
        
        # Add cursor mode
        #status_msg = f"{status_msg} | Mode: {self.cursor_mode}"
        
        # Add cell value if not too long
        #if display_value and len(display_value) < 20:
        #    status_msg = f"{status_msg} | {display_value}"
        
        self.query_one("#status_line", Static).update(status_msg)
        
        clipboard_info = ""
        if self.clipboard_type:
            if self.clipboard_type == "cell" and self.clipboard_cell:
                clip_preview = str(self.clipboard_cell)[:20]
                clipboard_info = f" | Clipboard: {clip_preview}..."
            elif self.clipboard_type == "row" and self.clipboard_row:
                clipboard_info = f" | Clipboard: row ({len(self.clipboard_row)} cells)"
            elif self.clipboard_type == "column" and self.clipboard_column:
                clipboard_info = f" | Clipboard: column ({len(self.clipboard_column)} cells)"
        
        status_msg = f"{status_msg}{clipboard_info}"
        if self.changed:
            status_msg = f"*{status_msg}"
        
        self.query_one("#status_line", Static).update(status_msg)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        
    # Don't handle input if we're not on the main screen
        if len(self.screen_stack) > 1:
            return
        
        # Check if we're in search mode
        if self.search_mode:
            # The search execution is handled in on_key (Enter key)
            # But we need to handle it here too for completeness
            self.execute_search()
            return
        
       
        # Check if we're in command mode
        if self.command_mode:
            self.command_mode = False
           
            # Reset input field
            inp = self.query_one("#cell_input", Input)
            inp.value = ""
            inp.placeholder = "Cell editor / prompt"
            
            self.execute_command(event.value)
            
            # Return focus to table
            
            self.thetable.focus()
            return
        
        # Width reset prompt
        if hasattr(self, 'pending_width_reset') and self.pending_width_reset:
            self.pending_width_reset = False
            if event.value.strip():
                try:
                    width = int(event.value.strip())
                    if width > 0:
                        self.reset_widths(width)
                    else:
                        self.set_status("Width must be greater than 0", temporary=True)
                except ValueError:
                    self.set_status(f"Invalid width: {event.value}", temporary=True)
            else:
                # Use default width if input is empty
                self.reset_widths()
            self.thetable.focus()
            return
        
        if hasattr(self, 'pending_column_width') and self.pending_column_width:
            self.pending_column_width = False
            if event.value.strip():
                try:
                    width = int(event.value.strip())
                    if width > 0:
                        self._cmd_column_width([event.value.strip()])
                    else:
                        self.set_status("Width must be greater than 0", temporary=True)
                except ValueError:
                    self.set_status(f"Invalid width: {event.value}", temporary=True)
            else:
                self.set_status("Width cannot be empty", temporary=True)
            self.thetable.focus()
            return

        # Goto row prompt
        if hasattr(self, 'pending_goto_row') and self.pending_goto_row:
            self.pending_goto_row = False
            self.execute_goto_row(event.value)
            self.thetable.focus()
            return
        
        # Goto column prompt
        if hasattr(self, 'pending_goto_column') and self.pending_goto_column:
            self.pending_goto_column = False
            self.execute_goto_column(event.value)
            self.thetable.focus()
            return
        
        # Column insert at cursor prompt
        if hasattr(self, 'pending_column_insert_at_cursor') and self.pending_column_insert_at_cursor:
            self.pending_column_insert_at_cursor = False
            if event.value.strip():
                self.insert_column_at_cursor(event.value)
            else:
                self.set_status("Column header cannot be empty")
            self.thetable.focus()
            return
        
        # Column append (at end) prompt
        if self.pending_column_insert:
            self.pending_column_insert = False
            
            # Don't allow inserting a row number column
            if event.value.lower() in ["#", "row_number"]:
                self.set_status("Cannot insert row number column - use '#' instead")
                self.thetable.focus()
                return
                
            if event.value.strip():
                self.append_column(event.value)
            else:
                self.set_status("Column header cannot be empty")
            self.thetable.focus()
            return

        if not self.current_cell:
            return


        # Get old value before change
        old_value = self.thetable.get_cell_at(self.current_cell)
        
        # Track this change for undo
        if self.undo_manager:
            self.undo_manager.track_cell_change(
                (self.current_cell.row, self.current_cell.column),
                old_value,
                event.value
            )
        
        # Save state before change
        cell_ref = f"{self.get_column_letter(self.current_cell.column-1)}{self.current_cell.row+1}"
        self.save_state_before_change(f"edit {cell_ref}")

        self.thetable.update_cell_at(self.current_cell, event.value)
        self.changed = True
        
        # Update status with coordinates
        row, col = self.current_cell.row, self.current_cell.column
        col_name = list(self.thetable.columns.keys())[col]
        #self.set_status(
        #    f"Updated R{row+1}C{col+1} ({col_name})"
        #)
        self.thetable.focus()

    # ============================================================
    # Helpers
    # ============================================================

    async def ask_yes_no(self, question: str, default_yes: bool = False) -> bool:
        """
        Ask a yes/no question using a modal popup.
        
        Args:
            question: The question to ask
            default_yes: If True, Yes button is focused by default
            
        Returns:
            bool: True for Yes, False for No
        """
        # Push the popup screen and wait for result
        result = await self.push_screen_wait(YesNoPopup(question, default_yes))
        return result

    def scan_and_replace_special_strings(self) -> None:
        """Scan entire table and replace special strings with calculated values."""
        if not self.thetable.row_count or not self.thetable.columns:
            self.set_status("Table is empty", temporary=True)
            return
        

        # scan for variables and insert values
        for row in range(self.thetable.row_count):
            for col in range(len(self.thetable.columns)):
                coord = type(self.current_cell)(row, col)
                cell_value = self.thetable.get_cell_at(coord)

                if isinstance(cell_value, str):
                    cell_value_str = str(cell_value).strip()
                    replacement = formatstr.scanvariable(cell_value_str)
                    if replacement:
                        self.thetable.update_cell_at(coord, replacement)

        # scan for cell variables like $A1 and replace them with the value in the cell
        # must happen after replacing all variables.
        for row in range(self.thetable.row_count):
            for col in range(len(self.thetable.columns)):
                coord = type(self.current_cell)(row, col)
                cell_value = self.thetable.get_cell_at(coord)
                cell_value_str = str(cell_value).strip()
                if "$" in cell_value_str:
                    self.changed = True
                    res = list_cell_references(cell_value_str)
                    if res:
                        for r in res:
                            xcol,yrow = parse_cell_coordinate(r)
                            txt = get_cellvalue_by_index(self.thetable, yrow, xcol)
                            cell_value_str = cell_value_str.replace(r,txt)
                    self.thetable.update_cell_at(coord, cell_value_str)
        
        # scan for formulas, after replacing all variables
        for row in range(self.thetable.row_count):
            for col in range(len(self.thetable.columns)):
                coord = type(self.current_cell)(row, col)
                cell_value = self.thetable.get_cell_at(coord)
                cell_value_str = str(cell_value).strip()
                if cell_value_str.startswith('=') and cell_value_str[1]!="(":
                    self.changed = True
                    new_value = funcstr.calculate_formula(self.thetable, cell_value_str)
                    self.thetable.update_cell_at(coord, new_value)
        
        for row in range(self.thetable.row_count):
            for col in range(len(self.thetable.columns)):
                coord = type(self.current_cell)(row, col)
                cell_value = self.thetable.get_cell_at(coord)
                cell_value_str = str(cell_value).strip()
                if cell_value_str.startswith('=(') and cell_value_str.endswith(')'):
                    # remove =( )
                    tmp = cell_value_str[2:-1]
                    self.changed = True
                    new_value = funcstr.safe_math_eval(tmp)
                    self.thetable.update_cell_at(coord, new_value)

    def enter_search_mode(self, direction: str) -> None:
        """Enter search mode."""
        self.search_mode = True
        self.search_direction = direction
        self.search_pattern = ""
        self.search_matches = []
        self.current_match_index = -1
        
        # Update input field for search
        inp = self.query_one("#cell_input", Input)
        prompt = "/" if direction == "forward" else "?"
        inp.value = prompt
        inp.placeholder = f"Search {direction} (press Enter to search, Esc to cancel)"
        inp.focus()
        
        self.set_status(f"Search {direction}", temporary=True)

    def exit_search_mode(self) -> None:
        """Exit search mode without searching."""
        self.search_mode = False
        self.search_pattern = ""
        self.search_matches = []  # Clear matches when explicitly exiting
        self.current_match_index = -1
        
        # Reset input field
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "Cell editor / prompt"
        
        # Return focus to table
        
        self.thetable.focus()
        
        self.set_status("Search cancelled", temporary=True)

    def update_search_input(self) -> None:
        """Update the input field with current search pattern."""
        if not self.search_mode:
            return
        
        inp = self.query_one("#cell_input", Input)
        prompt = "/" if self.search_direction == "forward" else "?"
        
        # Make sure input starts with the prompt
        current_value = inp.value
        if not current_value.startswith(prompt):
            inp.value = prompt + (current_value if current_value else self.search_pattern)
        else:
            # Update just the pattern part if needed
            if self.search_pattern and current_value[len(prompt):] != self.search_pattern:
                inp.value = prompt + self.search_pattern
        
        # Show match count if we have matches
        if self.search_matches:
            match_info = f" [{self.current_match_index + 1}/{len(self.search_matches)}]"
            inp.placeholder = f"Search {self.search_direction}{match_info} (n/N to navigate, Esc to cancel)"
        else:
            inp.placeholder = f"Search {self.search_direction} (press Enter to search, Esc to cancel)"

    def execute_search(self) -> None:
        """Execute the search with current pattern."""
        # Get the search pattern from input field
        inp = self.query_one("#cell_input", Input)
        input_value = inp.value
        
        # Extract pattern (remove leading / or ?)
        if input_value.startswith("/") or input_value.startswith("?"):
            pattern = input_value[1:]
        else:
            pattern = input_value
        
        if not pattern:
            self.set_status("Search pattern is empty", temporary=True)
            self.exit_search_mode()
            return
        
        self.search_pattern = pattern
        
        # Find all matches in the table
        self.find_all_matches()
        
        if not self.search_matches:
            self.set_status(f"Pattern '{self.search_pattern}' not found", temporary=True)
            # Keep search mode active for user to modify pattern
            inp.focus()
            return
        
        # Go to first match
        self.current_match_index = 0
        self.go_to_match(self.current_match_index)
        
        # Exit search mode but keep matches for navigation
        self.search_mode = False
        
        # Clear the input field and return focus to table
        inp.value = ""
        inp.placeholder = "Cell editor / prompt"
        
        self.thetable.focus()
        
        # Show search info in status
        self.set_status(f"Found {len(self.search_matches)} matches. Press n/N to navigate.")

    def find_all_matches(self) -> None:
        """Find all cells matching the search pattern."""
        
        pattern = self.search_pattern.lower()
        self.search_matches = []
        
        # Search through all cells
        for row in range(self.thetable.row_count):
            for col in range(len(self.thetable.columns)):
                try:
                    cell_value = self.thetable.get_cell_at(type(self.current_cell)(row, col))
                    if cell_value and pattern in str(cell_value).lower():
                        self.search_matches.append((row, col, str(cell_value)))
                except:
                    continue
        
        # Sort matches based on search direction
        if self.search_direction == "backward":
            self.search_matches.reverse()

    def find_next_match(self) -> None:
        """Go to next search match."""
        if not self.search_matches:
            # No active search, maybe start a new one
            self.set_status("No active search. Press / to start searching.", temporary=True)
            return
        
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.go_to_match(self.current_match_index)
        
        # Update status with match info
        match_num = self.current_match_index + 1
        total_matches = len(self.search_matches)
        self.set_status(f"Match {match_num}/{total_matches}. Press n/N to navigate.")

    def find_prev_match(self) -> None:
        """Go to previous search match."""
        if not self.search_matches:
            # No active search, maybe start a new one
            self.set_status("No active search. Press / to start searching.", temporary=True)
            return
        
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.go_to_match(self.current_match_index)
        
        # Update status with match info
        match_num = self.current_match_index + 1
        total_matches = len(self.search_matches)
        self.set_status(f"Match {match_num}/{total_matches}. Press n/N to navigate.")

    def highlight_matches(self) -> None:
        pass

    def go_to_match(self, match_index: int) -> None:
        """Navigate to a specific match."""
        if not self.search_matches or match_index < 0 or match_index >= len(self.search_matches):
            return
        
        row, col, cell_value = self.search_matches[match_index]
        
        
        # Move cursor to the match
        self.thetable.cursor_coordinate = type(self.thetable.cursor_coordinate)(row, col)
        self.current_cell = self.thetable.cursor_coordinate
        
        # Update input field with cell value (but don't give it focus)
        inp = self.query_one("#cell_input", Input)
        inp.value = cell_value
        
        # Show match info in status
        match_num = match_index + 1
        total_matches = len(self.search_matches)
        preview = cell_value[:30] + "..." if len(cell_value) > 30 else cell_value
        
        # Update coordinates display
        self.update_status_with_coords()
    
    def get_row_key(self, row_index: int):
        """Get row key for a given row index."""
        
        row_keys = list(self.thetable.rows.keys())
        if 0 <= row_index < len(row_keys):
            return row_keys[row_index]
        return None

    def get_column_key(self, col_index: int):
        """Get column key for a given column index."""
        
        col_keys = list(self.thetable.columns.keys())
        if 0 <= col_index < len(col_keys):
            return col_keys[col_index]
        return None

    def copy_selection(self) -> None:
        """Copy current selection based on cursor mode."""
        
        
        if not self.current_cell:
            self.set_status("No cell selected", temporary=True)
            return
        
        row, col = self.current_cell.row, self.current_cell.column
        
        if self.cursor_mode == "cell":
            # Copy single cell
            try:
                value = self.thetable.get_cell_at(self.current_cell)
                self.clipboard_cell = str(value) if value is not None else ""
                self.clipboard_type = "cell"
                pyperclip.copy(self.clipboard_cell)
                self.set_status(f"Copied cell: {self.clipboard_cell[:50]}..." if len(str(self.clipboard_cell)) > 50 else f"Copied cell: {self.clipboard_cell}")
            except:
                self.set_status("Failed to copy cell", temporary=True)
        
        elif self.cursor_mode == "row":
            # Copy entire row - collect all cell values
            try:
                row_data = []
                # Get all columns
                rowstr = ""
                for c in range(len(self.thetable.columns)-1):
                    cell_coord = type(self.current_cell)(row, c+1)
                    value = self.thetable.get_cell_at(cell_coord)
                    row_data.append(str(value) if value is not None else "")
                    rowstr += ","+str(value)
                
                self.clipboard_row = row_data
                pyperclip.copy(rowstr)
                self.clipboard_type = "row"
                self.set_status(f"Copied row {row + 1} with {len(self.clipboard_row)} cells")
            except Exception as e:
                self.set_status(f"Failed to copy row: {str(e)}", temporary=True)
        
        elif self.cursor_mode == "column":
            # Copy entire column - collect all cell values
            try:
                column_data = []
                # Get all rows
                colstr = ""
                for r in range(self.thetable.row_count):
                    cell_coord = type(self.current_cell)(r, col)
                    value = self.thetable.get_cell_at(cell_coord)
                    column_data.append(str(value) if value is not None else "")
                    colstr += str(value)+"\n"
                    
                
                self.clipboard_column = column_data
                self.clipboard_type = "column"
                pyperclip.copy(colstr)
                
                # Get column name for display
                col_keys = list(self.thetable.columns.keys())
                if col < len(col_keys):
                    col_name = self.thetable.columns[col_keys[col]].label
                    self.set_status(f"Copied column {col_name} with {len(self.clipboard_column)} cells")
                else:
                    self.set_status(f"Copied column with {len(self.clipboard_column)} cells")
            except Exception as e:
                self.set_status(f"Failed to copy column: {str(e)}", temporary=True)
        
        else:
            self.set_status(f"Unknown cursor mode: {self.cursor_mode}", temporary=True)

    def paste_selection(self) -> None:
        """Paste clipboard content at current position."""
        if not self.clipboard_type:
            self.set_status("Clipboard is empty", temporary=True)
            return
        
        if not self.current_cell:
            self.set_status("No cell selected", temporary=True)
            return
        
        start_row, start_col = self.current_cell.row, self.current_cell.column
        
        try:
            if self.clipboard_type == "cell":
                if self.clipboard_cell is not None:
                    self.thetable.update_cell_at(self.current_cell, self.clipboard_cell)
                    self.set_status(f"Pasted: {self.clipboard_cell[:50]}..." if len(str(self.clipboard_cell)) > 50 else f"Pasted: {self.clipboard_cell}")
            
            elif self.clipboard_type == "row":
                if self.clipboard_row is not None:
                    # Paste row values starting at current position
                    for col_offset, value in enumerate(self.clipboard_row):
                        #paste_col = start_col + col_offset
                        paste_col = col_offset+1
                        if paste_col < len(self.thetable.columns):
                            paste_coord = type(self.current_cell)(start_row, paste_col)
                            self.thetable.update_cell_at(paste_coord, value)
                    
                    self.set_status(f"Pasted row at R{start_row + 1}C{start_col + 1}")
            
            elif self.clipboard_type == "column":
                if self.clipboard_column is not None:
                    # Paste column values starting at current position
                    for row_offset, value in enumerate(self.clipboard_column):
                        #paste_row = start_row + row_offset
                        paste_row = row_offset
                        if paste_row < self.thetable.row_count:
                            paste_coord = type(self.current_cell)(paste_row, start_col)
                            self.thetable.update_cell_at(paste_coord, value)
                    
                    self.set_status(f"Pasted column at R{start_row + 1}C{start_col + 1}")
            
            # Update input field with current cell value
            if self.current_cell:
                value = self.thetable.get_cell_at(self.current_cell)
                inp = self.query_one("#cell_input", Input)
                inp.value = str(value)
            
            self.changed = True
            # Update status with coordinates
            self.update_status_with_coords()
        except Exception as e:
            self.set_status(f"Paste failed: {str(e)}", temporary=True)

    def cut_selection(self) -> None:
        """Cut (copy and delete) current selection based on cursor mode."""
        if not self.current_cell:
            self.set_status("No cell selected", temporary=True)
            return
        
        # First copy the selection
        self.copy_selection()
        
        # Then clear the cells based on mode
        if self.cursor_mode == "cell":
            # Cut single cell (set to empty)
            try:
                self.thetable.update_cell_at(self.current_cell, "")
                self.set_status("Cut cell (cleared content)", temporary=True)
            except:
                self.set_status("Failed to cut cell", temporary=True)
        
        elif self.cursor_mode == "row":
            # Cut entire row (clear all cells in the row)
            try:
                row = self.current_cell.row
                for col in range(len(self.thetable.columns)):
                    cell_coord = type(self.current_cell)(row, col)
                    self.thetable.update_cell_at(cell_coord, "")
                
                self.set_status(f"Cut (cleared) row {row + 1}")
            except Exception as e:
                self.set_status(f"Failed to cut row: {str(e)}", temporary=True)
        
        elif self.cursor_mode == "column":
            # Cut entire column (clear all cells in the column)
            try:
                col = self.current_cell.column
                for row in range(self.thetable.row_count):
                    cell_coord = type(self.current_cell)(row, col)
                    self.thetable.update_cell_at(cell_coord, "")
                
                # Get column name for display
                col_keys = list(self.thetable.columns.keys())
                if col < len(col_keys):
                    col_name = self.thetable.columns[col_keys[col]].label
                    self.set_status(f"Cut (cleared) column {col_name}")
                else:
                    self.set_status(f"Cut (cleared) column")
            except Exception as e:
                self.set_status(f"Failed to cut column: {str(e)}", temporary=True)
        self.changed = True
    
    def auto_width(self, min_width: int = 10, max_width: int = 50) -> None:
        """Auto-adjust column widths based on content."""
        self.set_cursor_mode("cell"),
        if not self.thetable.columns:
            return
        
        # Store cursor position
        cursor_pos = self.thetable.cursor_coordinate if hasattr(self.thetable, 'cursor_coordinate') else None
        
        # Store all data first
        column_keys = []
        column_data = {}  # Store column info: label, width
        
        # Get column information
        for col_key_obj in self.thetable.columns.keys():
            col_key = col_key_obj.value
            column_keys.append(col_key)
            column_data[col_key] = {
                'label': self.thetable.columns[col_key].label,
                'width': None
            }
        
        # Calculate max content length for each column
        for col_key in column_keys:
            if col_key == "row_number":
                column_data[col_key]['width'] = self.number_column_width
                continue
            
            max_len = 0
            
            # Check column label
            col_label = column_data[col_key]['label']
            if col_label:
                max_len = max(max_len, len(str(col_label)))
            
            # Check all cells in this column
            for row_key in self.thetable.rows:
                try:
                    cell_value = self.thetable.get_cell(row_key, col_key)
                    if cell_value is not None:
                        cell_str = str(cell_value)
                        max_len = max(max_len, len(cell_str))
                except:
                    pass
            
            # Calculate width with constraints
            width = max_len + 2  # Add padding
            width = max(min_width, min(width, max_width))
            column_data[col_key]['width'] = width
        
        # Store all row data
        all_rows = []
        for row_key in self.thetable.rows:
            row_data = []
            for col_key in column_keys:
                row_data.append(self.thetable.get_cell(row_key, col_key))
            all_rows.append(row_data)
        
        # Clear and rebuild table with new widths
        self.thetable.clear(columns=True)
        
        # Add columns with calculated widths
        for col_key in column_keys:
            data = column_data[col_key]
            self.thetable.add_column(data['label'], key=col_key, width=data['width'])
        
        # Add all rows back
        for row_data in all_rows:
            self.thetable.add_row(*row_data)
        
        # Try to restore cursor position
        if cursor_pos and cursor_pos.row < self.thetable.row_count and cursor_pos.column < len(self.thetable.columns):
            try:
                self.thetable.cursor_coordinate = cursor_pos
                self.current_cell = cursor_pos
            except:
                # If cursor position is invalid, move to (0, 0)
                self.thetable.cursor_coordinate = type(cursor_pos)(0, 0)
                self.current_cell = self.thetable.cursor_coordinate
        
        # Update input field with current cell value
        if self.current_cell:
            value = self.thetable.get_cell_at(self.current_cell)
            inp = self.query_one("#cell_input", Input)
            inp.value = str(value)
        
        # Force a full refresh
        self.thetable.refresh(layout=True)
        
        self.set_status(f"Auto-adjusted column widths (min: {min_width}, max: {max_width})")

    def prompt_reset_widths(self) -> None:
        """Prompt user for column width."""
        inp = self.query_one("#cell_input", Input)
        inp.value = ""
        inp.placeholder = "Enter column width (default: 15)"
        inp.focus()
        self.pending_width_reset = True
    
    def reset_widths(self, default_width: int = 15) -> None:
        """Reset all column widths to default value."""
        
        
        if not self.thetable.columns:
            return
        
        self.set_cursor_mode("cell")
        # Store cursor position
        cursor_pos = self.thetable.cursor_coordinate if hasattr(self.thetable, 'cursor_coordinate') else None
        
        # Store all data first
        column_keys = []
        for col_key_obj in self.thetable.columns.keys():
            column_keys.append(col_key_obj.value)
        
        # Store all row data
        all_rows = []
        for row_key in self.thetable.rows:
            row_data = []
            for col_key in column_keys:
                row_data.append(self.thetable.get_cell(row_key, col_key))
            all_rows.append(row_data)
        
        # Store column labels
        column_labels = {}
        for col_key in column_keys:
            column_labels[col_key] = self.thetable.columns[col_key].label
        
        # Clear and rebuild table with default widths
        self.thetable.clear(columns=True)
        
        # Re-add columns with default widths
        for col_key in column_keys:
            if col_key == "row_number":
                self.thetable.add_column(column_labels[col_key], key=col_key, width=self.number_column_width)
            else:
                self.thetable.add_column(column_labels[col_key], key=col_key, width=default_width)
        
        # Re-add all rows
        for row_data in all_rows:
            self.thetable.add_row(*row_data)
        
        # Try to restore cursor position
        if cursor_pos and cursor_pos.row < self.thetable.row_count and cursor_pos.column < len(self.thetable.columns):
            try:
                self.thetable.cursor_coordinate = cursor_pos
                self.current_cell = cursor_pos
            except:
                # If cursor position is invalid, move to (0, 0)
                self.thetable.cursor_coordinate = type(cursor_pos)(0, 0)
                self.current_cell = self.thetable.cursor_coordinate
        
        # Update input field with current cell value
        if self.current_cell:
            value = self.thetable.get_cell_at(self.current_cell)
            inp = self.query_one("#cell_input", Input)
            inp.value = str(value)
        
        # Force a full refresh
        self.thetable.refresh(layout=True)
        
        # Update status
        self.update_status_with_coords()
        
        self.set_status(f"Reset all columns to width {default_width}")
    
    def renumber_columns(self) -> None:
        """Renumber column keys to maintain spreadsheet letter sequence"""
        
        
        if not self.thetable.columns:
            return
        
        # Get all column keys in current display order
        column_keys = list(self.thetable.columns.keys())
        
        # Create mapping from old keys to new sequential keys
        key_mapping = {}
        new_idx = 0
        
        for old_key in column_keys:
            if old_key == "row_number":
                key_mapping[old_key] = old_key
            elif old_key.startswith("col_") or old_key.startswith("col_new_"):
                # Renumber to sequential col_0, col_1, etc.
                new_key = f"col_{new_idx}"
                key_mapping[old_key] = new_key
                new_idx += 1
            else:
                # Keep other keys as-is
                key_mapping[old_key] = old_key
        
        # Check if we need to actually rename anything
        if all(k == key_mapping[k] for k in key_mapping):
            return  # No renaming needed
        
        # Store all data
        all_data = {}
        for row_key in self.thetable.rows:
            row_data = {}
            for col_key in column_keys:
                row_data[col_key] = self.thetable.get_cell(row_key, col_key)
            all_data[row_key] = row_data
        
        # Clear and rebuild with new keys
        self.thetable.clear(columns=True)
        
        # Add columns with new keys
        for old_key in column_keys:
            new_key = key_mapping[old_key]
            col = self.thetable.columns.get(old_key)  # Actually we need to get from stored columns
            
            # We need to store column info before clearing
            # Let's store column labels before clearing
            pass
        
        # Actually, let's use a different approach
        # Store column labels before clearing
        column_info = []
        for old_key in column_keys:
            col_obj = self.thetable.columns[old_key]
            column_info.append((old_key, col_obj.label, col_obj.width if hasattr(col_obj, 'width') else None))
        
        # Re-add columns with new keys
        self.thetable.clear(columns=True)
        
        for old_key, label, width in column_info:
            new_key = key_mapping[old_key]
            if new_key == "row_number":
                self.thetable.add_column(label, key=new_key, width=width or self.number_column_width)
            else:
                self.thetable.add_column(label, key=new_key, width=width)
        
        # Add rows with new keys
        for row_key, row_data in all_data.items():
            new_row = []
            for old_key in column_keys:
                new_row.append(row_data[old_key])
            self.thetable.add_row(*new_row)

    def set_status(self, message: str, temporary: bool = True) -> None:
        """Set status message, optionally temporary (default: temporary)"""
        if temporary:
            # Show temporary message
            self.query_one("#status_line", Static).update(message)
            # Reset to coordinates after delay
            self.set_timer(self.message_delay, self.update_status_with_coords)
        else:
            # For permanent messages
            self.query_one("#status_line", Static).update(message)
        
    def get_display_coordinates(self, row: int, col: int) -> tuple[str, str]:
        """Get display coordinates (1-indexed for user)"""
        # Adjust for row number column
        display_row = row + 1  # 1-indexed for user
        display_col = col + 1  # 1-indexed for user
        
        
        col_keys = list(self.thetable.columns.keys())
        col_name = col_keys[col] if col < len(col_keys) else f"C{display_col}"
        
        return f"R{display_row}C{display_col}", col_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TermCell | CSV Editor/Spread sheet")
    parser.add_argument("file", nargs="?", help="CSV file to open")
    parser.add_argument("-d", "--delimiter", default=",", help="CSV delimiter character (default: ,)")
    parser.add_argument("-t", "--tab", action="store_true", help="Use tab as delimiter (overrides -d)")
    
    args = parser.parse_args()
    
    delimiter = args.delimiter
    if args.tab:
        delimiter = "\t"
    
    # Get filename from args
    filename = args.file
    
    # Pass delimiter and filename to CSVEditor
    app = CSVEditor(delimiter=delimiter, filename=filename)
    app.run()
