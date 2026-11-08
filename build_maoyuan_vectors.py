"""Run from the gallery repository root using its existing model dependencies."""
import cat_match_v2 as matcher

if __name__ == "__main__":
    matcher.initialize_model(rebuild=True)
    matcher.save_vectors()
    assert matcher.load_vectors(matcher.model.get_sentence_embedding_dimension()) is not None
    print("Validated:", matcher.CACHE_PATH)
