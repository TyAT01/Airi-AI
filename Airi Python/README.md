# Project AIRI Python

This is a modular Python implementation of the AIRI project.

## Architecture

- **`core/`**: Core AI logic and state management.
  - `orchestrator.py`: The central hub.
  - `character.py`: Persona and reaction history.
  - `notebook.py`: Task and focus management.
  - `memory.py`: RAG and long-term memory.
  - `body.py`: Animation and expression control.
  - `consciousness.py`: High-level AI state.
  - `model_drivers/`: Hardware and model-specific drivers (MediaPipe, LipSync).
  - `stage/`: Navigation and layout state.
- **`communication/`**: WebSocket server and protocol schemas.
- **`llm/`**: Modular LLM clients and providers.
- **`perception/`**: Audio (STT) and Vision processing.
- **`expression/`**: Audio (TTS) and Speech pipelines.
- **`integrations/`**: External service connectors (Discord, Twitter).
- **`plugins/`**: Modular plugin system.
- **`scripts/`**: Utility scripts for development and deployment.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables:
   - `OPENAI_API_KEY`
   - `ELEVENLABS_API_KEY`
3. Run the main entry point:
   ```bash
   python main.py
   ```

## Verification

Run the comprehensive integration test:
```bash
python verify_integration.py
```
