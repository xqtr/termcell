from textual.screen import Screen 
from textual.containers import Container, ScrollableContainer, Horizontal
from textual.app import ComposeResult
from textual.widgets import Footer, Input, Static, Button, Label, Header, DirectoryTree, Select
from textual import on
import os
from pathlib import Path
from typing import ClassVar, List, Optional
from textual.suggester import Suggester

class FileSuggester(Suggester):
    async def get_suggestion(self, value: str) -> str | None:
        path = next(Path().glob(f"{value}*"), None)
        return str(path) if path else None
        
class SimpleDirectoryTree(DirectoryTree):
    """A simplified directory tree without parent navigation to avoid TreeNode issues"""
    
    def on_mount(self) -> None:
        """Focus the tree when mounted"""
        self.focus()

class SaveFileDialog(Screen):
    CSS = """
    #filename_controls {
        height: auto;
    }
    
       
    #tree_container {
        height: 1fr;
        border: solid $primary;
        border-title-color: $text-muted;
    }
    
    #ok {
        background: $success;
        color: $text;
    }
    
    #cancel {
        background: $error;
        color: $text;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.title = "Save As"

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            with Container(id="fixed_top", classes="dialog-top"):
                yield Static("Save File As:", classes="dialog-label")
                with Horizontal(id="path_controls"):
                    yield Button("^ Up", id="go_up", classes="nav-button")
                    yield Input(id="path_input", value=str(Path.cwd()), classes="dialog-input")
                with Horizontal(id="filename_controls"):
                    #yield Label("Filename:", classes="dialog-label")
                    yield Input(
                        id="filename", 
                        placeholder="Enter filename...", 
                        classes="dialog-input",
                        suggester=FileSuggester(use_cache=False)
                    )
            with Container(id="tree_container"):
                yield SimpleDirectoryTree(path=Path.cwd(), id="tree")
            with Container(id="buttons_container", classes="dialog-bottom"):
                with Horizontal(id="button_row"):
                    yield Button("OK", variant="primary", id="ok")
                    yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#tree").focus()
    
    def key_backspace(self) -> None:
        """Go to parent directory when backspace is pressed in tree"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        if tree.has_focus:
            self.go_up_pressed()
            
    def key_escape(self) -> None:
        """Close dialog when Escape is pressed"""
        self.cancel_pressed()
        
    @on(Button.Pressed, "#go_up")
    def go_up_pressed(self) -> None:
        """Navigate to parent directory"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        current_path = Path(tree.path)
        parent_path = current_path.parent
        
        # Only navigate if we're not at the root
        if parent_path != current_path:
            tree.path = parent_path
            self.query_one("#path_input", Input).value = str(parent_path)
            tree.focus()

    @on(Input.Submitted, "#path_input")
    def change_path(self, event: Input.Submitted) -> None:
        new_path = event.input.value.strip()
        if new_path:
            try:
                p = Path(new_path).expanduser().absolute()
                if p.is_dir():
                    tree = self.query_one("#tree", SimpleDirectoryTree)
                    tree.path = p
                    event.input.value = str(p)
                    tree.focus()
                else:
                    self.notify(f"Directory not found: {new_path}", severity="error")
                    self.bell()
            except Exception as e:
                self.notify(f"Invalid path: {e}", severity="error")
                self.bell()

    @on(DirectoryTree.DirectorySelected, "#tree")
    def dir_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        tree = self.query_one("#tree", SimpleDirectoryTree)
        tree.path = event.path
        self.query_one("#path_input", Input).value = str(event.path)
        tree.focus()

    @on(DirectoryTree.FileSelected, "#tree")
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.query_one("#filename", Input).value = event.path.name
        self.query_one("#path_input", Input).value = str(event.path.parent)
        self.query_one("#filename").focus()

    @on(Button.Pressed, "#ok")
    def ok_pressed(self) -> None:
        path_val = self.query_one("#path_input", Input).value.strip()
        filename = self.query_one("#filename", Input).value.strip()
        if path_val and filename:
            # Auto-add .csv extension if no extension provided
            if not Path(filename).suffix:
                filename += ".csv"
            full_path = Path(path_val) / filename
            
            # Check if file exists
            if full_path.exists():
                # Show overwrite confirmation
                from yesnodialog import YesNoDialog  # Import here to avoid circular dependency
                self.app.push_screen(
                    YesNoDialog(f"File '{filename}' already exists. Overwrite?"),
                    callback=lambda overwrite: self._handle_overwrite(overwrite, full_path)
                )
            else:
                self.dismiss(str(full_path))
        else:
            self.notify("Please provide both path and filename", severity="error")
            self.bell()

    def _handle_overwrite(self, overwrite: bool, full_path: Path) -> None:
        """Handle the result of the overwrite confirmation"""
        if overwrite:
            self.dismiss(str(full_path))
        # else do nothing - stay in the save dialog

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)
