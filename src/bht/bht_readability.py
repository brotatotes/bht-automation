from textstat import flesch_reading_ease, flesch_kincaid_grade, gunning_fog, automated_readability_index, dale_chall_readability_score

def calculate_flesch_kincaid_grade(text):
    return flesch_kincaid_grade(text)

def calculate_flesch_kincaid_ease(text):
    return flesch_reading_ease(text)

def calculate_gunning_fog(text):
    return gunning_fog(text)

def calculate_automated_readability_index(text):
    return automated_readability_index(text)

def calculate_dale_chall_readability(text):
    return dale_chall_readability_score(text)

def display_readability_metrics(text):
    print("Text:", text)

    fke_score = calculate_flesch_kincaid_ease(text)
    print("Flesch-Kincaid Ease Score:", fke_score)

    fk_score = calculate_flesch_kincaid_grade(text)
    print("Flesch-Kincaid Grade Level:", fk_score)

    fog_index = calculate_gunning_fog(text)
    print("Gunning Fog Index:", fog_index)

    ari = calculate_automated_readability_index(text)
    print("Automated Readability Index:", ari)

    dale_chall_score = calculate_dale_chall_readability(text)
    print("Dale-Chall Readability Score:", dale_chall_score)

    print()

# Example usage:
if __name__ == "__main__":
    texts = ["This is an example sentence for readability testing. It has some complex words.", "This is easy.", "She that liveth in pleasure is one who indulges in luxurious, lavish living, giving herself to pleasure and worldly desires.", "While alive in the flesh, has no real life in the Spirit."]
    for text in texts:
        display_readability_metrics(text)
