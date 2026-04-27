# Contributing to Janken Duel 🎮

Thanks for your interest!

## Getting Started

1. Fork the repo
2. Clone your fork
3. Install dependencies:
   
    ```bash
    uv sync
    ```

4. Run the game:

   ```bash
   uv run main.py
   ```

## How to Contribute

### 🐛 Bug Reports

* Use the issue template
* Include steps to reproduce
* Mention OS + Python version

### ✨ Features

* Check roadmap first
* Open an issue before large changes

### 🛠 Code Changes

* Keep changes small and focused
* Follow existing structure (`game/` modules)
* Avoid breaking game loop or state machine

## Style Guidelines

* Python 3.11+
* Keep logic modular (match current architecture)
* Prefer readability over cleverness

## Areas That Need Help

* UI polish / animations
* AI improvements
* Sound design tweaks
* Multiplayer support

## 🌿 Branching Strategy

- The `master` branch is **stable / release-ready**
- All development happens in the `develop` branch

👉 Please create PRs **against `develop`**, not `master`

### Workflow

1. Fork the repo
2. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

3. Make changes
4. Push and open a PR targeting `develop`

---

Thanks for contributing 🚀
