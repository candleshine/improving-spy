
## 📚 Week 4 Homework Assignment: Build an Input Validator Agent

### 🎯 Learning Objectives

By completing this assignment, students will:

- ✅ Use `ToolOutput` with Pydantic models for **structured output**
- ✅ Implement a **modular agent** that processes input before the Game Master
- ✅ Apply `message_history` and agent patterns from Lesson 4
- ✅ Enforce **genre consistency** and **input safety** in an AI app
- ✅ Practice **error handling** and user feedback

---

### 🧩 Assignment Brief

> In our `Chronicle Engine`, players can type any action — even ones that break genre or logic (e.g., “rub my magic lamp” in a spy thriller).
>
> Your task is to **build a validator agent** that runs *before* the Game Master and checks whether the player’s input is:
>
> - ✅ Genre-appropriate (no magic in a spy game)
> - ✅ Logically possible (no “fly to the moon” unless in sci-fi)
> - ✅ Safe and on-topic
>
> If the input is invalid, the validator should **block it** and return a helpful message.
>
> If valid, the input proceeds to the Game Master.

---

### ✅ Requirements

1. **Create a Pydantic model**:

   ```python
   from pydantic import BaseModel

   class ValidationResult(BaseModel):
       valid: bool
       reason: str
       suggested_correction: str | None = None
   ```

2. **Build a validator agent** using `ToolOutput`:
   - Model: `ollama:llama3.1` or `openai:gpt-4o-mini`
   - Output type: `ToolOutput(ValidationResult)`
   - System prompt: clearly defines validation rules

3. **Integrate into the game loop**:
   - Run validator **before** Game Master
   - If invalid, send rejection message via WebSocket
   - If valid, proceed to GM

4. **Test it**:
   - Try invalid inputs: `"summon a dragon"`, `"hack the mainframe with a toaster"`
   - Verify corrections are suggested
   - Confirm valid inputs still work

---

### 💡 Example Prompt for the Validator

```text
You are a content validator for a spy-themed RPG.
Reject inputs that:
- Break genre (e.g., magic, fantasy, sci-fi in a Cold War thriller)
- Are impossible (e.g., "fly", "become invisible")
- Are off-topic or nonsensical
- Use tools or items not in the world

Be strict but helpful. Suggest realistic alternatives when possible.
```

---

### 🧪 Sample Test Cases

| Input | Expected Outcome |
|------|------------------|
| `"I search the desk"` | ✅ Valid |
| `"I rub my magic lamp"` | ❌ Invalid → "There's no magic in this world." |
| `"I hack the KGB server"` | ✅ Valid (plausible in genre) |
| `"I turn into a bat"` | ❌ Invalid → "You're a human agent, not a vampire." |

---

### 📦 Deliverables

Students should submit:

1. `engine/validator.py` with the `InputValidator` class
2. Updated `main.py` with validator integration
3. A short README explaining:
   - How the validator works
   - One example of input it blocks
   - Why structured output (`ToolOutput`) is better than raw text

---

### 📚 Why This Works as Homework

| Concept | How It’s Taught |
|--------|-----------------|
| `ToolOutput` | Enforces schema, prevents parsing errors |
| `message_history` | Not needed here — shows when *not* to use it |
| Agent modularity | Separates validation from narration |
| Real-world AI safety | Teaches input sanitization |
| Ollama/local models | Encourages privacy-aware design |

It’s **focused**, **practical**, and **aligned with the Pydantic AI docs** — especially the sections on:

- [Structured output](https://ai.pydantic.dev/api/output/)
- [Message history](https://ai.pydantic.dev/message-history/)
- [Testing with `FunctionModel`](https://ai.pydantic.dev/message-history/#testing-history-processors)

---

### ✅ Final Note to Students

> “This isn’t just about blocking silly inputs — it’s about **building trustworthy AI systems**. In production, you can’t let users derail your app with off-topic or harmful prompts. This validator is your first line of defense.”
