from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED
from rich.theme import Theme
import logging
import os
import sys
from typing import Any, Optional, Tuple
from pyfiglet import Figlet

class ModernLogger:
    """
    Modern colorful logger with smooth gradient styling inspired by Vue CLI,
    built on top of the rich library.
    """

    # Emoji prefixes for each level - with fallback
    LEVEL_ICONS = {
        "DEBUG": "🐛 ",
        "INFO": "ℹ️ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌ ",
        "CRITICAL": "💀 "
    }
    
    # Text fallbacks for terminals that don't support emojis well
    LEVEL_ICONS_FALLBACK = {
        "DEBUG": "[DEBUG]",
        "INFO": "[INFO] ",
        "WARNING": "[WARN] ",
        "ERROR": "[ERROR]",
        "CRITICAL": "[CRIT] "
    }

    # Hardcoded gradient endpoints
    GRADIENT_START = "#41B883"  # Vue green
    GRADIENT_END   = "#6574CD"  # Vue purple

    def __init__(
        self,
        name: str = "app",
        level: str = "info",
        log_file: Optional[str] = None,
        show_path: bool = False,
        rich_tracebacks: bool = True,
        use_emoji: bool = None  # Auto-detect if None
    ):
        # Auto-detect emoji support
        if use_emoji is None:
            use_emoji = self._detect_emoji_support()
        self.use_emoji = use_emoji
        
        # Enable rich tracebacks without showing line numbers
        install_rich_traceback(show_locals=True, suppress=[], max_frames=100, extra_lines=3, word_wrap=False)

        # Map text levels to logging levels
        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        log_level = levels.get(level.lower(), logging.INFO)

        # Define custom theme (directly using color/effect strings)
        custom_theme = Theme({
            "info": "bold cyan",
            "warning": "bold yellow",
            "error": "bold red",
            "critical": "bold white on red",
            "success": "#4CAF50",
            "vue_primary": "#42B883",
            "vue_secondary": "#35495E",
            "logging.time": "dim white",
            "logging.level.debug": "grey70",
            "logging.level.info": "bold cyan",
            "logging.level.warning": "bold yellow",
            "logging.level.error": "bold red",
            "logging.level.critical": "bold white on red",
        })

        # Set up console and handler with better width handling
        try:
            terminal_width = os.get_terminal_size().columns
            # Clamp width to reasonable range
            console_width = max(80, min(terminal_width, 120))
        except OSError:
            # Fallback for environments without proper terminal
            console_width = 100
            
        self.console = Console(
            theme=custom_theme, 
            highlight=False,  # Disable highlighting to prevent interference
            width=console_width,  # Use detected/clamped width
            force_terminal=True,
            stderr=False,  # Use stdout to prevent mixed output
            legacy_windows=False  # Better Windows compatibility
        )
        
        rich_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_level=True,
            show_path=show_path,
            markup=True,
            rich_tracebacks=rich_tracebacks,
            log_time_format="[%H:%M:%S]",
        )

        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()
        self.logger.addHandler(rich_handler)

        if log_file:
            self._setup_file_handler(log_file)

    def _detect_emoji_support(self) -> bool:
        """Detect if the terminal/environment supports emoji properly."""
        # Check various indicators
        if os.getenv('TERM_PROGRAM') in ['iTerm.app', 'Terminal.app']:
            return True
        if os.getenv('WT_SESSION'):  # Windows Terminal
            return True
        if sys.platform == 'win32' and os.getenv('TERM_PROGRAM') != 'vscode':
            return False  # Conservative for Windows CMD/PowerShell
        return True  # Default to True for Unix-like systems

    def _setup_file_handler(self, log_file: str) -> None:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(fh)

    def _create_gradient_text(self, text: str) -> Text:
        """
        Create a smooth gradient across the text from GRADIENT_START to GRADIENT_END.
        """
        def hex_to_rgb(h: str) -> Tuple[int,int,int]:
            return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))

        start_rgb = hex_to_rgb(self.GRADIENT_START)
        end_rgb   = hex_to_rgb(self.GRADIENT_END)
        length = len(text)
        grad_text = Text()

        for i, ch in enumerate(text):
            t = i / (length - 1) if length > 1 else 0
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
            color = f"#{r:02X}{g:02X}{b:02X}"
            grad_text.append(ch, style=color)

        return grad_text

    def _get_level_icon(self, level: str) -> str:
        """Get level icon with emoji fallback."""
        if self.use_emoji:
            return self.LEVEL_ICONS.get(level, "")
        else:
            return self.LEVEL_ICONS_FALLBACK.get(level, f"[{level}]")

    # —— Logging Level Methods —— #

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(f"{self._get_level_icon('DEBUG')} {message}", *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.info(f"{self._get_level_icon('INFO')} {message}", *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(f"{self._get_level_icon('WARNING')} {message}", *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.error(f"{self._get_level_icon('ERROR')} {message}", *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.critical(f"{self._get_level_icon('CRITICAL')} {message}", *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.exception(f"{self._get_level_icon('ERROR')} {message}", *args, **kwargs)

    # —— Rich Print Methods —— #

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.console.print(*args, **kwargs)

    def progress(self, total: int = 100, description: str = "Processing") -> Tuple[Progress, int]:
        """
        Create a clean, robust progress bar that works well in all environments.
        """
        # Simplified layout to avoid alignment issues
        progress = Progress(
            SpinnerColumn("dots", style="vue_secondary"),
            TextColumn("[bold vue_primary]{task.description}", justify="left"),
            BarColumn(
                complete_style=self.GRADIENT_START, 
                finished_style=self.GRADIENT_END,
                bar_width=40  # Fixed width to prevent layout issues
            ),
            TextColumn("[bold vue_secondary]{task.percentage:>3.0f}%", justify="right"),
            TextColumn("[dim]|[/dim]", style="dim"),
            TextColumn("{task.completed:>4}/{task.total}", justify="right"),
            console=self.console,
            expand=False,
            transient=False
        )
        task_id = progress.add_task(description, total=total)
        return progress, task_id

    def simple_progress(self, total: int = 100, description: str = "Processing") -> Tuple[Progress, int]:
        """
        Create a minimal progress bar for problematic environments.
        """
        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("{task.completed}/{task.total}"),
            console=self.console,
            expand=False,
            transient=False
        )
        task_id = progress.add_task(description, total=total)
        return progress, task_id

    def stage(self, message: str) -> None:
        """
        Display a prominent stage marker with gradient panel.
        """
        try:
            panel = Panel(
                self._create_gradient_text(f" {message} "),
                box=ROUNDED,
                border_style="vue_primary",
                expand=False,
                padding=(0, 2)
            )
            self.console.print(panel, justify="left")
            self.console.print()
        except Exception:
            # Fallback to simple text if panel fails
            self.console.print(f"\n=== {message} ===\n", style="bold vue_primary")

    def highlight(self, message: str) -> None:
        """
        Print a star marker followed by gradient text.
        """
        try:
            star = "★" if self.use_emoji else "*"
            txt = Text(f" {star} ", style=f"bold {self.GRADIENT_START}")
            txt.append(self._create_gradient_text(message))
            self.console.print(txt)
        except Exception:
            # Fallback to simple text
            self.console.print(f" * {message}", style="bold vue_primary")

    def success(self, message: str) -> None:
        """
        Print a green checkmark with message.
        """
        try:
            check = "✓" if self.use_emoji else "OK"
            txt = Text()
            txt.append(f" {check} ", style="bold green")
            txt.append(message, style="green")
            self.console.print(txt)
        except Exception:
            # Fallback
            self.console.print(f" [OK] {message}", style="bold green")

    def error_box(self, message: str) -> None:
        try:
            panel = Panel(
                message,
                title="ERROR",
                title_align="left",
                border_style="bold red",
                box=ROUNDED,
                padding=(1, 2)
            )
            self.console.print(panel)
        except Exception:
            # Fallback
            self.console.print(f"\n[ERROR] {message}\n", style="bold red")

    def section(self, message: str) -> None:
        """
        Print a gradient-colored rule with section title.
        """
        try:
            self.console.print()
            header = self._create_gradient_text(f" {message} ")
            self.console.rule(header, style="vue_secondary", align="center")
            self.console.print()
        except Exception:
            # Fallback
            self.console.print(f"\n{'='*20} {message} {'='*20}\n", style="bold vue_primary")

    def info_panel(self, title: str, message: str) -> None:
        try:
            panel = Panel(
                message,
                title=title,
                title_align="left",
                border_style="vue_primary",
                box=ROUNDED,
                padding=(1, 2)
            )
            self.console.print(panel)
        except Exception:
            # Fallback
            self.console.print(f"\n[{title}] {message}\n", style="bold vue_primary")

    def gradient_text(self, message: str) -> None:
        """
        Print a standalone smooth-gradient text.
        """
        try:
            self.console.print(self._create_gradient_text(message))
        except Exception:
            # Fallback
            self.console.print(message, style="bold vue_primary")

    def table(self, title: Optional[str] = None) -> Table:
        tbl = Table(
            title=title,
            box=ROUNDED,
            title_style="bold vue_primary",
            border_style="vue_primary",
            header_style="bold",
            min_width=60  # Ensure minimum width
        )
        return tbl

    # —— File Save Notification —— #

    def file_saved(self, file_path: str, file_name: str=None) -> None:
        """
        Print "File saved" with path as clickable link and emoji indicator.
        """
        try:
            # Convert to absolute path to create valid URI
            abs_path = Path(file_path).resolve()
            uri = abs_path.as_uri()
            disk_icon = "💾" if self.use_emoji else "[SAVE]"
            # Use Rich Markup to generate linked text
            if file_name:
                self.console.print(
                    f"{disk_icon} ({file_name}) File saved: [link={uri}][bold blue]{file_path}[/bold blue][/link]"
                )
            else:
                self.console.print(
                    f"{disk_icon} File saved: [link={uri}][bold blue]{file_path}[/bold blue][/link]"
                )
        except Exception:
            # Fallback without link if URI conversion fails
            disk_icon = "💾" if self.use_emoji else "[SAVE]"
            if file_name:
                self.console.print(
                    f"{disk_icon} ({file_name}) File saved: [bold blue]{file_path}[/bold blue]"
                )
            else:
                self.console.print(
                    f"{disk_icon} File saved: [bold blue]{file_path}[/bold blue]"
                )
    
        
    def banner(self, project_name: str, title: str, description: str, font: str = "slant") -> None:
        """
        Print an ASCII Art Banner at program startup with gradient styling,
        and a project description panel using the theme colors.
        """
        try:
            fig = Figlet(font=font)
            art = fig.renderText(project_name)

            # Apply character-level gradient to each line
            for line in art.splitlines():
                grad_line = self._create_gradient_text(line)
                self.console.print(grad_line)

            panel = Panel(
                description,
                title=f"[bold vue_primary]{title}",
                border_style="vue_primary",
                box=ROUNDED,
                padding=(1, 2),
            )
            self.console.print(panel)
        except Exception as e:
            # Fallback to simple text banner
            self.console.print(f"\n{'='*50}", style="bold vue_primary")
            self.console.print(f"{project_name}", style="bold vue_primary")
            self.console.print(f"{title}", style="vue_primary")
            self.console.print(f"{description}", style="dim")
            self.console.print(f"{'='*50}\n", style="bold vue_primary")

