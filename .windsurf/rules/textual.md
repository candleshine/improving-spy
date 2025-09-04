---
trigger: manual
---

# Textual UI Development Best Practices Guide  

This guide outlines best practices for creating clean, maintainable, and user-friendly terminal applications using [Textual](https://textual.textualize.io), a powerful Python framework for building rich text-based user interfaces.

---

## ✅ 1. **Structure Your App Correctly**

### Use Proper Class Inheritance
Always subclass `App` from `textual.app`. Define your main application logic in a dedicated class.

```python
from textual.app import App

class MyApp(App):
    pass

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

> 💡 **Why?** This keeps your app modular and allows safe imports without immediate execution.

---

## 🧱 2. **Compose Widgets Intentionally**

### Prefer `compose()` Over Manual Mounting
Use the `compose()` method to define the initial structure of your UI. Return a generator of widgets using `yield`.

```python
from textual.app import ComposeResult
from textual.widgets import Button, Label

class MyAppComponent(App):
    def compose(self) -> ComposeResult:
        yield Label("Welcome!")
        yield Button("Continue", id="continue")
```

> ✅ **Best Practice:** Composition is declarative, predictable, and aligns with modern UI patterns (like React or Vue).

---

## 🔌 3. **Use Events Properly**

### Handle Events with `on_*` Methods
Respond to user interaction via event handlers prefixed with `on_`.

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    self.exit("button_clicked")
```

### Prefer Async When Needed
If integrating async libraries (e.g., `httpx`, `asyncio.sleep`), use `async`/`await`.

```python
async def on_key(self) -> None:
    await self.mount(SomeWidget())
    # Now safe to query newly mounted widget
```

> ⚠️ Only use `async` when necessary. Regular functions are sufficient for simple logic.

---

## 🎨 4. **Style with External CSS (`.tcss`)**

### Use `CSS_PATH` for Maintainability
Keep styling separate from logic by using `.tcss` files.

```python
class MyApp(App):
    CSS_PATH = "styles.tcss"
```

Example `styles.tcss`:
```css
Screen {
    layout: grid;
    grid-size: 3;
    padding: 2;
}

Button {
    width: 100%;
    height: 3;
}

#submit-button {
    background: green;
    color: white;
}
```

> ✅ **Best Practice:** External CSS enables live reloading (`textual dev`) and cleaner separation of concerns.

---

## 🧩 5. **Use IDs and Classes for Targeted Styling & Queries**

Always assign meaningful `id` or `classes` to widgets you plan to style or interact with.

```python
yield Button("Save", id="save-btn", classes="action primary")
```

Then query them safely:
```python
self.query_one("#save-btn", Button)
```

> 🛑 Avoid brittle assumptions about widget order. Use IDs instead of `query(Button)[0]`.

---

## 🧹 6. **Handle Dynamic Widget Mounting Safely**

When adding widgets at runtime, **await `mount()`** if you need to interact with children immediately.

```python
async def on_key(self) -> None:
    await self.mount(Welcome())
    self.query_one(Button).label = "Done!"
```

> ❌ Never assume a widget is fully mounted right after `self.mount()` unless awaited.

---

## 🏷️ 7. **Set Title and Subtitle for UX Clarity**

Use `TITLE` and `SUB_TITLE` class variables or update dynamically.

```python
class MyApp(App):
    TITLE = "Document Editor"
    SUB_TITLE = "file.txt - Press Ctrl+S to save"
```

Include the `Header()` widget to display these:
```python
from textual.widgets import Header

def compose(self) -> ComposeResult:
    yield Header()  # Shows title/subtitle automatically
```

> ✅ **UX Tip:** Keep users informed about context and state.

---

## 🚪 8. **Exit Gracefully with Typed Returns**

Use generic typing (`App[T]`) to indicate what `run()` returns.

```python
class QuestionApp(App[str]):
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit(event.button.id)  # returns "yes" or "no"

app = QuestionApp()
result = app.run()  # Type-safe: result is str | None
```

> ✅ Enables better type checking with `mypy` and clearer intent.

---

## 📦 9. **Organize Large Apps with Screens and Widgets**

### Break UI into Reusable Components
Create custom widgets and screens for complex interfaces.

```python
class EditorScreen(Screen):
    def compose(self) -> ComposeResult:
        yield TextArea()
        yield Button("Save", id="save")

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(EditorScreen())
```

> ✅ Promotes reusability, testability, and readability.

---

## 🔐 10. **Support App Suspension (Unix/Linux/macOS)**

Allow users to temporarily leave your app (e.g., to edit in `vim`).

```python
from textual.binding import Binding

class MyApp(App):
    BINDINGS = [Binding("ctrl+z", "suspend_process", "Suspend")]
    
    def compose(self) -> ComposeResult:
        yield Label("Press Ctrl+Z to suspend to shell")
```

Or programmatically suspend:
```python
def run_editor(self):
    with self.suspend():
        os.system("vim config.txt")
```

> ✅ Respects user workflow in terminal environments.

---

## 🧪 11. **Use Inline Mode for Tool-Like Apps**

For CLI-integrated tools, run in inline mode:

```python
app.run(inline=True)
```

> ✅ Keeps output below the prompt; ideal for automation or quick utilities.

> ⚠️ Not supported on Windows.

---

## 🎨 12. **Respect ANSI Colors When Appropriate**

For inline or minimal full-screen tools, preserve system ANSI colors:

```python
class MyApp(App):
    def __init__(self):
        super().__init__(ansi_color=True)  # Preserve terminal theme
```

> ✅ Better integration with user’s terminal preferences.

---

## 🧼 13. **Write Clean, Typed, and Documented Code**

### Use Type Hints
Even though optional, they improve clarity and catch bugs early.

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    ...
```

### Add Docstrings
Help AI and humans understand intent.

```python
def on_key(self, event: Key) -> None:
    """Change background color when number keys are pressed."""
    if event.key.isdigit():
        self.screen.styles.background = COLORS[int(event.key)]
```

---

## 🛠️ 14. **Leverage Development Tools**

Use `textual dev` for live-reload during development:
```bash
textual dev myapp.py
```

Enable hot-reloading of `.tcss` files for instant feedback.

> ✅ Speeds up UI iteration significantly.

---

## 📚 Summary: Key Principles

| Principle | Recommendation |
|--------|----------------|
| **Separation of Concerns** | Logic in Python, styling in `.tcss` |
| **Declarative UI** | Use `compose()` with `yield` |
| **Type Safety** | Use `App[T]`, type hints, and `mypy` |
| **User Experience** | Set title/subtitle, support suspend, give feedback |
| **Maintainability** | Break into widgets/screens, use IDs/classes |
| **Async Safety** | `await mount()` when querying new widgets |

---

## 🚀 Final Tip: Start Simple, Scale Smart

Begin with a minimal `App`, then grow:
1. Add widgets via `compose()`
2. Style with `.tcss`
3. Respond to events
4. Split into components
5. Add routing/screens as needed

