"""Train and save the quantum intent classifier (run once: python train_ml_model.py)."""
from ml_intent import MODEL_PATH, _train_model, save_model

if __name__ == "__main__":
    print("Training QuantumIntentModel on notebook corpus...")
    model = _train_model(epochs=100)
    save_model(model)
    print(f"Saved to {MODEL_PATH}")
