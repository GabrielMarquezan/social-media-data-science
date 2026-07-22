from social_media.src.nlp.preprocessing import clean_text


def test_clean_text_removes_urls_and_mentions():
    text = "Olha esse link https://example.com e @usuario!"
    assert clean_text(text) == "olha esse link e!"
