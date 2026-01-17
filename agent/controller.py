from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.syntax import Syntax

from llm.ollama_client import OllamaClient
from llm.prompts import BASE_SYSTEM_PROMPT, CODER_PROMPT
from agent.planner import Planner
from agent.chat_handler import ChatModeHandler
from tools.file_tools import FileTools, FileToolError
from tools.diff_tools import DiffTools
from memory.manager import MemoryManager


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
    "diff_add": "#00FF88",     # Green for additions
    "diff_del": "#FF4444",     # Red for deletions
}


def sanitize_code_output(text: str) -> str:
    """Remove Markdown code fences if the model outputs them."""
    lines = text.strip().splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()


def escape_rich_markup(text: str) -> str:
    """Escape Rich markup characters to prevent rendering errors."""
    if text is None:
        return ""
    # Escape brackets that could be interpreted as Rich markup
    text = text.replace("[", "\\[")
    return text


def find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


class AgentController:
    def __init__(self):
        self.console = Console()
        self.llm = OllamaClient()
        self.planner = Planner(self.llm)

        self.project_root = find_project_root()
        self.file_tools = FileTools(self.project_root)
        
        # Memory management
        self.memory_manager = MemoryManager(llm_client=self.llm)
        self.chat_handler = ChatModeHandler(self.llm, self.memory_manager)
        
        # Mode tracking - "chat" or "agent"
        self.current_mode = "agent"  # Default to agent mode

    def handle_user_input(self, user_input: str):
        """Route user input based on current mode."""
        # RESPECT THE CURRENT MODE FIRST
        if self.current_mode == "chat":
            self._handle_chat_mode(user_input)
        elif self.current_mode == "agent":
            self._handle_agent_mode(user_input)
        else:
            # Fallback: auto-detect mode
            if self._should_use_chat_mode(user_input):
                self._handle_chat_mode(user_input)
            else:
                self._handle_agent_mode(user_input)

    def _should_use_chat_mode(self, user_input: str) -> bool:
        """Determine if the input should be handled in chat mode (for auto-detection)."""
        user_input_lower = user_input.lower().strip()
        
        # Check for explicit chat commands
        if user_input_lower.startswith('chat') or user_input_lower.startswith('tell me') or user_input_lower.startswith('explain'):
            return True
        
        # Check if it's a question
        question_indicators = ['who', 'what', 'when', 'where', 'why', 'how', 'is', 'are', 'can', 'could', 'would', 'should', 'do', 'does', 'did']
        words = user_input_lower.split()
        if words and words[0] in question_indicators or '?' in user_input:
            # Exclude questions about coding tasks
            coding_indicators = ['create', 'make', 'write', 'change', 'modify', 'add', 'update', 'fix', 'implement', 'build', 'code', 'function', 'class', 'file', 'module']
            if any(indicator in user_input_lower for indicator in coding_indicators):
                return False
            return True
        
        # Check for explicit agent commands
        if any(keyword in user_input_lower for keyword in ['create', 'make', 'write', 'change', 'modify', 'add', 'update', 'fix', 'implement', 'build']):
            return False
        
        return False

    def _handle_chat_mode(self, user_input: str):
        """Handle chat mode conversation - no planning, just conversation."""
        try:
            # Process chat and get response
            response = self.chat_handler.process_chat(user_input)
            
            # Display response using Text object (no markup parsing)
            self.console.print()
            
            # Create response text without markup parsing
            response_text = Text(response)
            
            response_panel = Panel(
                response_text,
                title=f"[bold {COLORS['info']}]:: RESPONSE ::[/bold {COLORS['info']}]",
                border_style=COLORS["info"],
                padding=(0, 1),
            )
            self.console.print(response_panel)
            
        except Exception as e:
            error_msg = Text(f"[X] ERROR: {str(e)}")
            self.console.print()
            self.console.print(f"  ", end="")
            self.console.print(error_msg, style=Style(color=COLORS["accent"], bold=True))

    def _handle_agent_mode(self, user_input: str):
        """Handle agent mode for coding tasks."""
        try:
            # 1. Planning
            self._print_status("PLANNING", "Analyzing task...")

            plan = self.planner.create_plan(user_input)
            if not plan:
                self._print_error("Failed to generate a plan.")
                return

            self._display_plan(plan)

            # 2. Read target file (simple heuristic for now)
            target_file = "cli/main.py"

            try:
                original_code = self.file_tools.read_file(target_file)
            except FileToolError as e:
                self._print_error(str(e))
                return

            # 3. Propose changes
            self._print_status("GENERATING", "Creating code changes...")

            plan_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))

            coder_prompt = f"""
Plan:
{plan_text}

File: {target_file}
Current content:
{original_code}

Return the FULL modified file content.
"""
            modified_code = self.llm.generate(
                prompt=coder_prompt,
                system=f"{BASE_SYSTEM_PROMPT}\n\n{CODER_PROMPT}",
                temperature=0.1,
            )

            modified_code = sanitize_code_output(modified_code)

            # Auto-retry once if Markdown still leaked
            if "```" in modified_code:
                self._print_warning("Model output contained Markdown. Retrying...")

                retry_prompt = coder_prompt + "\n\nREMINDER: Output RAW SOURCE CODE ONLY."

                modified_code = self.llm.generate(
                    prompt=retry_prompt,
                    system=f"{BASE_SYSTEM_PROMPT}\n\n{CODER_PROMPT}",
                    temperature=0.05,
                )

                modified_code = sanitize_code_output(modified_code)

            diff = DiffTools.generate_diff(
                original=original_code,
                modified=modified_code,
                filename=target_file,
            )

            if not diff.strip():
                self._print_warning("No changes detected.")
                return

            # 4. Show diff - use Text object to avoid markup parsing
            self.console.print()
            
            # Use Syntax highlighting for diff (handles escaping automatically)
            diff_syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
            
            diff_panel = Panel(
                diff_syntax,
                title=f"[bold {COLORS['primary']}]:: PROPOSED CHANGES ::[/bold {COLORS['primary']}]",
                subtitle=f"[{COLORS['muted']}]{target_file}[/{COLORS['muted']}]",
                border_style=COLORS["secondary"],
                padding=(0, 1),
            )
            self.console.print(diff_panel)

            # 5. Explicit confirmation
            confirm_prompt = Text()
            confirm_prompt.append("\n  ", style="")
            confirm_prompt.append("[", style=Style(color=COLORS["dim"]))
            confirm_prompt.append("?", style=Style(color=COLORS["warning"], bold=True))
            confirm_prompt.append("]", style=Style(color=COLORS["dim"]))
            confirm_prompt.append(" Apply changes? ", style=Style(color=COLORS["text"]))
            confirm_prompt.append("(yes/no)", style=Style(color=COLORS["muted"]))
            confirm_prompt.append(": ", style=Style(color=COLORS["secondary"]))
            
            confirm = self.console.input(confirm_prompt).strip().lower()

            if confirm not in {"yes", "y"}:
                self.console.print(f"  ", end="")
                self.console.print(">> Changes discarded <<", style=Style(color=COLORS["muted"]))
                return

            # 6. Apply safely
            self.file_tools.write_file(
                target_file,
                modified_code,
                overwrite=True,
            )

            self._print_success("Changes successfully applied!")
            
        except Exception as e:
            self._print_error(str(e))

    def _print_status(self, label: str, message: str):
        """Print a styled status message."""
        status = Text()
        status.append("\n  ", style="")
        status.append("[", style=Style(color=COLORS["dim"]))
        status.append(label, style=Style(color=COLORS["primary"], bold=True))
        status.append("]", style=Style(color=COLORS["dim"]))
        status.append(f" {message}", style=Style(color=COLORS["muted"]))
        self.console.print(status)

    def _print_error(self, message: str):
        """Print an error message."""
        error = Text()
        error.append("\n  ", style="")
        error.append("[X] ERROR: ", style=Style(color=COLORS["accent"], bold=True))
        error.append(message, style=Style(color=COLORS["text"]))
        self.console.print(error)

    def _print_warning(self, message: str):
        """Print a warning message."""
        warning = Text()
        warning.append("  ", style="")
        warning.append("[!] WARNING: ", style=Style(color=COLORS["warning"], bold=True))
        warning.append(message, style=Style(color=COLORS["text"]))
        self.console.print(warning)

    def _print_success(self, message: str):
        """Print a success message."""
        success = Text()
        success.append("  ", style="")
        success.append("[+] ", style=Style(color=COLORS["success"], bold=True))
        success.append(message, style=Style(color=COLORS["success"]))
        self.console.print(success)

    def _display_plan(self, plan: list[str]):
        """Display the execution plan with styled output."""
        self.console.print()
        
        # Build plan text using Text objects (no markup parsing issues)
        plan_content = Text()
        for i, step in enumerate(plan):
            if i > 0:
                plan_content.append("\n")
            plan_content.append(f"{i+1:02d}", style=Style(color=COLORS["secondary"]))
            plan_content.append(" | ", style=Style(color=COLORS["dim"]))
            plan_content.append(step, style=Style(color=COLORS["text"]))
        
        plan_panel = Panel(
            plan_content,
            title=f"[bold {COLORS['primary']}]:: EXECUTION PLAN ::[/bold {COLORS['primary']}]",
            border_style=COLORS["dim"],
            padding=(0, 1),
        )
        self.console.print(plan_panel)
