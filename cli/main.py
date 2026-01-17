from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.align import Align

from agent.controller import AgentController


console = Console()

# RGB Color Theme
COLORS = {
    "primary": "#FF3366",      # Hot pink-red
    "secondary": "#FF6B6B",    # Coral red
    "accent": "#FF1744",       # Bright red
    "highlight": "#FF5252",    # Red accent
    "dim": "#8B3A3A",          # Dark red
    "success": "#00FF88",      # Neon green
    "warning": "#FFD700",      # Gold
    "info": "#00D4FF",         # Cyan
    "text": "#FFFFFF",         # White
    "muted": "#666666",        # Gray
}

# ASCII Art Logo
LOGO = r"""
    __    ____  ________    __       ___    ____
   / /   / __ \/ ____/ /   / /      /   |  /  _/
  / /   / / / / /   / /   / /      / /| |  / /  
 / /___/ /_/ / /___/ /___/ /___   / ___ |_/ /   
/_____/\____/\____/_____/_____/  /_/  |_/___/   
                                                
     [ P R A T I K ' S   A S S I S T A N T ]    
"""

DIVIDER = "=" * 56
THIN_DIVIDER = "-" * 56


def gradient_text(text: str, start_color: str = "#FF3366", end_color: str = "#FF6B6B") -> Text:
    """Create a gradient-like effect on text."""
    styled = Text()
    styled.append(text, style=Style(color=start_color, bold=True))
    return styled


def print_banner(cwd: Path):
    """Print the welcome banner with ASCII art."""
    console.print()
    
    # Logo with gradient effect
    logo_text = Text()
    for i, line in enumerate(LOGO.strip().split('\n')):
        # Alternate between colors for gradient effect
        if i < 3:
            logo_text.append(line + "\n", style=Style(color=COLORS["primary"], bold=True))
        elif i < 5:
            logo_text.append(line + "\n", style=Style(color=COLORS["secondary"], bold=True))
        else:
            logo_text.append(line + "\n", style=Style(color=COLORS["accent"]))
    
    console.print(Align.center(logo_text))
    
    # Divider
    console.print(f"[{COLORS['dim']}]{DIVIDER}[/]", justify="center")
    console.print()
    
    # Working directory
    console.print(f"  [{COLORS['muted']}]WORKING DIR[/] [{COLORS['text']}]>[/] [{COLORS['info']}]{cwd}[/]")
    console.print()
    
    # Commands box
    cmd_panel = Panel(
        f"[{COLORS['secondary']}]CHAT[/]   [{COLORS['muted']}]->[/] Conversational mode\n"
        f"[{COLORS['secondary']}]AGENT[/]  [{COLORS['muted']}]->[/] Coding tasks mode\n"
        f"[{COLORS['secondary']}]EXIT[/]   [{COLORS['muted']}]->[/] Quit the assistant",
        title=f"[bold {COLORS['primary']}]:: COMMANDS ::[/]",
        border_style=COLORS["dim"],
        padding=(0, 2),
    )
    console.print(cmd_panel)
    console.print()


def print_mode_switch(mode: str):
    """Print mode switch notification."""
    mode_upper = mode.upper()
    console.print(f"\n  [{COLORS['dim']}]>>[/] [{COLORS['success']}]SWITCHED TO {mode_upper} MODE[/] [{COLORS['dim']}]<<[/]\n")


def print_exit():
    """Print exit message."""
    console.print(f"\n[{COLORS['dim']}]{THIN_DIVIDER}[/]")
    console.print(f"  [{COLORS['warning']}]>> SESSION TERMINATED <<[/]")
    console.print(f"[{COLORS['dim']}]{THIN_DIVIDER}[/]\n")


def run():
    """
    Entry point for the `ai` CLI command.
    """
    cwd = Path.cwd()
    agent = AgentController()

    print_banner(cwd)

    try:
        while True:
            # Custom prompt with RGB style
            prompt = Text()
            prompt.append("\n  ", style="")
            prompt.append("[", style=Style(color=COLORS["dim"]))
            prompt.append("ai", style=Style(color=COLORS["primary"], bold=True))
            prompt.append("]", style=Style(color=COLORS["dim"]))
            prompt.append(" > ", style=Style(color=COLORS["secondary"]))
            
            user_input = console.input(prompt)

            if user_input.strip().lower() in {"exit", "quit"}:
                print_exit()
                break

            # Handle mode switching commands
            if user_input.strip().lower() == "chat":
                agent.current_mode = "chat"
                print_mode_switch("chat")
                continue
            elif user_input.strip().lower() == "agent":
                agent.current_mode = "agent"
                print_mode_switch("agent")
                continue

            if not user_input.strip():
                continue

            agent.handle_user_input(user_input)

    except KeyboardInterrupt:
        console.print(f"\n\n  [{COLORS['accent']}]>> INTERRUPTED - EXITING <<[/]\n")
