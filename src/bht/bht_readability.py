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
    texts = ["This is an example sentence for readability testing. It has some complex words.", "This is easy.", "She that liveth in pleasure is one who indulges in luxurious, lavish living, giving herself to pleasure and worldly desires.", "While alive in the flesh, has no real life in the Spirit.", "In this pivotal moment, as Jesus approaches the completion of his task, he unveils the immense love and eagerness he has for our salvation. It is a testament to his unwavering commitment that he requests something to drink only when everything has been accomplished. By fulfilling the prophecies that foretold his suffering and the offer of vinegar, Jesus strengthens our faith and exemplifies the depth of his thirst for the redemption of his people.", "Jesus, in intense present agony of thirst, spoke the words I thirst to fulfill Scripture and leave no pre-appointed particular of His suffering unfulfilled. Thirst symbolized a deeper refreshment to the soul, and Jesus desired to promote our salvation through His infinite love. He chose to drink vinegar to show that He was the person whom David represented and to strengthen our faith.", "Believers express a natural reluctance to undergo the act of death, desiring to be clothed with their heavenly body and have their mortal part swallowed up by life. This groaning arises from being burdened with the body, which hinders spiritual exercises.", "The believers in the tabernacle of their bodies find themselves groaning and burdened, not due to the sufferings and trials they face, but because they desire something greater - to be clothed upon with a heavenly body. Their groaning stems from their longing for a transformation, not a desire to be completely rid of their current bodies. Faith recognizes the value and purpose of the physical body, and thus, there is no disdain for it. Rather, believers eagerly anticipate being gloriously adorned with an immortal, incorruptible, and spiritual body."]
    for text in texts:
        display_readability_metrics(text)
