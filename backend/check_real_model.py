from app.services.model_service import _load_real_model

if __name__ == "__main__":
    model = _load_real_model()
    print("REAL_MODEL_LOAD_OK", model.name)
