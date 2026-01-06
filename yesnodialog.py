from textual.screen import ModalScreen 
from textual.containers import Container, Center, Horizontal
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual import events

class YesNoDialog(ModalScreen[bool]):  # Changed from Screen to ModalScreen
    """
    A modal dialog that asks a yes/no question.
    Returns True for Yes, False for No.
    """
    
    CSS = """
    YesNoDialog {
        align: center middle;
    }
    
    #dialog-container {
        width: 70%;
        height: 14;
        padding: 2;
        background: $surface;
        border: panel $primary;
        border-title-color: $text;
        border-title-background: $primary;
    }
    
    #message {
        text-align: center;
        padding: 1;
        color: $text;
    }
    
    #buttons {
        align: center middle;
    }
    
    Button {
        margin: 0 1;
        min-width: 8;
    }
    
    #yes {
        background: $success;
    }
    
    #no {
        background: $error;
    }
    
    #key-hint {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    """
    
    def __init__(self, message: str, title: str = "Confirm") -> None:
        super().__init__()
        self.message = message
        self.title = title

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            yield Static(self.message, id="message")
            yield Static("(Press Y for Yes, N for No, Esc for No)", id="key-hint")
            with Horizontal(id="buttons"):
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="error", id="no")

    def on_mount(self) -> None:
        """Set dialog title when mounted."""
        self.query_one("#dialog-container").border_title = self.title
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts."""
        key = event.key.lower()
        if key == "y":
            self.dismiss(True)
            event.stop()
        elif key in ["n", "escape"]:
            self.dismiss(False)
            event.stop()
        elif key == "tab" or key == "down" or key == "right" or key == "space":
            # Cycle focus between buttons
            event.stop()
            self.focus_next()
        elif key == "shift+tab" or key == "up" or key == "left":
            # Cycle focus backwards
            event.stop()
            self.focus_previous()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)
