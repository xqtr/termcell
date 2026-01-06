from textual.screen import Screen 
from textual.containers import Container, ScrollableContainer, Horizontal
from textual.app import ComposeResult
from textual.widgets import Footer, Input, Static, Button, Label, Header, DirectoryTree, Select
from textual import on
import os
from pathlib import Path
from typing import ClassVar, List, Optional

class FilteredDirectoryTree(DirectoryTree):
    """A directory tree that filters files by extension"""
    
    # Default extensions to show
    DEFAULT_EXTENSIONS: ClassVar[List[str]] = ['.csv', '.txt', '.tsv']
    
    def __init__(self, path: str | Path, extensions: Optional[List[str]] = None, **kwargs) -> None:
        super().__init__(path, **kwargs)
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.show_all_files = False  # Toggle to show all files
    
    def filter_paths(self, paths: List[Path]) -> List[Path]:
        """Filter paths to show only directories and filtered files"""
        filtered = []
        for path in paths:
            if path.is_dir():
                filtered.append(path)
            elif self.show_all_files:
                filtered.append(path)
            else:
                # Check if file has allowed extension
                if any(path.name.lower().endswith(ext) for ext in self.extensions):
                    filtered.append(path)
        return filtered
    
    def _add_path(self, tree_path: Path, node) -> None:
        """Override to add filtered paths"""
        try:
            # Get directory contents
            directory_paths = [
                Path(os.path.join(tree_path, filename))
                for filename in os.listdir(tree_path)
                if not filename.startswith('.')
            ]
            
            # Filter the paths
            filtered_paths = self.filter_paths(directory_paths)
            
            # Sort directories first, then files
            directories = sorted([p for p in filtered_paths if p.is_dir()])
            files = sorted([p for p in filtered_paths if p.is_file()])
            
            # Add directories
            for path in directories:
                node.add(path.name, data=path, icon="📁", allow_expand=True)
            
            # Add files
            for path in files:
                icon = "📄"
                node.add(path.name, data=path, icon=icon, allow_expand=False)
                
        except (PermissionError, OSError):
            node.add("(Permission denied)", allow_expand=False, icon="⚠️")


class OpenFileDialog(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.title = "Open File"
        self.current_extensions = ['.csv', '.txt', '.tsv']
        self.show_all = False
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            with Container(id="fixed_top", classes="dialog-top"):
                yield Static("Select a file to open:", classes="dialog-label")
                with Horizontal(id="path_controls"):
                    yield Button("^ Up", id="go_up", classes="nav-button")
                    yield Select(
                        options=[
                            ("CSV files only", "csv"),
                            ("TXT files only", "txt"), 
                            ("CSV & TXT files", "csv_txt"),
                            ("All files", "all")
                        ],
                        prompt="Filter...",
                        id="file_filter",
                        classes="filter-select"
                    )
                    yield Button("Toggle All Files", id="toggle_all", classes="nav-button", variant="default")
                #with Horizontal(id="filter_controls"):
                    yield Input(id="path_input", value=str(Path.cwd()), classes="dialog-input")
            with Container(id="tree_container"):
                yield FilteredDirectoryTree(
                    path=Path.cwd(), 
                    id="tree",
                    extensions=self.current_extensions
                )
            with Container(id="buttons_container", classes="dialog-bottom"):
                with Horizontal(id="button_row"):
                    yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#tree").focus()
        # Set initial filter to CSV & TXT
        self.query_one("#file_filter", Select).value = "csv_txt"
    
    def update_tree_filter(self) -> None:
        """Update the tree with current filter settings"""
        tree = self.query_one("#tree", FilteredDirectoryTree)
        tree.extensions = self.current_extensions
        tree.show_all_files = self.show_all
        
        # Refresh the tree view
        current_path = tree.path
        tree.path = current_path  # This will trigger a refresh
    
    @on(Select.Changed, "#file_filter")
    def on_filter_changed(self, event: Select.Changed) -> None:
        """Handle filter selection change"""
        filter_value = event.value
        
        if filter_value == "csv":
            self.current_extensions = ['.csv']
            self.show_all = False
        elif filter_value == "txt":
            self.current_extensions = ['.txt']
            self.show_all = False
        elif filter_value == "csv_txt":
            self.current_extensions = ['.csv', '.txt', '.tsv']
            self.show_all = False
        elif filter_value == "all":
            self.current_extensions = []
            self.show_all = True
        
        self.update_tree_filter()
    
    @on(Button.Pressed, "#toggle_all")
    def toggle_all_files(self) -> None:
        """Toggle between showing all files and filtered files"""
        tree = self.query_one("#tree", FilteredDirectoryTree)
        self.show_all = not self.show_all
        
        # Update filter dropdown to reflect change
        select = self.query_one("#file_filter", Select)
        if self.show_all:
            select.value = "all"
        else:
            # Reset to current filter
            if self.current_extensions == ['.csv']:
                select.value = "csv"
            elif self.current_extensions == ['.txt']:
                select.value = "txt"
            else:
                select.value = "csv_txt"
        
        tree.show_all_files = self.show_all
        self.update_tree_filter()
        
        # Update button text
        button = self.query_one("#toggle_all", Button)
        button.label = "Show Filtered" if self.show_all else "Show All Files"
    
    def key_backspace(self) -> None:
        """Go to parent directory when backspace is pressed in tree"""
        tree = self.query_one("#tree", FilteredDirectoryTree)
        if tree.has_focus:
            self.go_up_pressed()
    
    def key_escape(self) -> None:
        """Close dialog when Escape is pressed"""
        self.cancel_pressed()
        
    @on(Button.Pressed, "#go_up")
    def go_up_pressed(self) -> None:
        """Navigate to parent directory"""
        tree = self.query_one("#tree", FilteredDirectoryTree)
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
                    tree = self.query_one("#tree", FilteredDirectoryTree)
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
        tree = self.query_one("#tree", FilteredDirectoryTree)
        tree.path = event.path
        self.query_one("#path_input", Input).value = str(event.path)
        tree.focus()

    @on(DirectoryTree.FileSelected, "#tree")
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(str(event.path))

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)


# # CSS for styling the filter controls (add to your main app's CSS or here)
# FILTER_DIALOG_CSS = """
# #dialog-container {
    # padding: 1;
    # background: $surface;
    # border: panel $primary;
    # width: 80%;
    # height: 80%;
# }

# #fixed_top {
    # height: auto;
    # margin-bottom: 1;
# }

# #path_controls {
    # height: auto;
    # margin-bottom: 1;
# }

# #filter_controls {
    # height: auto;
    # margin-bottom: 1;
# }

# .filter-select {
    # width: 30;
    # margin-right: 1;
# }

# .nav-button {
    # width: auto;
    # margin-right: 1;
# }

# #tree_container {
    # height: 1fr;
    # border: solid $primary;
# }

# #buttons_container {
    # height: auto;
    # margin-top: 1;
# }

# #button_row {
    # height: auto;
    # align: right;
# }
# """


# CSS += """
    # #dialog-container {
        # width: 100%;
        # height: 100%;
        # layout: vertical;
    # }
    # .dialog-top {
        # height: 6;
        # padding: 1;
        # /* border: solid $accent; */
        # background: $panel;
    # }
    # .dialog-label {
        # margin-bottom: 0;
        # color: $text;
    # }
    # .nav-button {
        # width: auto;
        # min-width: 5;
        # margin-right: 1;
    # }
    # .dialog-input {
        # width: 100%;
        # margin-bottom: 0;
    # }
    # #tree_container {
        # width: 100%;
        # height: 1fr;
        # /* border: solid $accent; */
    # }
    # #tree {
        # width: 100%;
        # height: 100%;
    # }
    # .dialog-bottom {
        # height: auto;
        # padding:1;
        # /* border: solid $accent; */
        # background: $panel;
    # }
    # #path_input {
        # border: blank;
    # }
    # #buttons_container {
        # height: auto;
    # }
    # #button_row {
        # width: 100%;
        # align: center middle;
        # height: auto;
        # color: $primary;
    # }
    
    # #button_row > Button {
        # margin: 0 1;
    # }
    
    # """
