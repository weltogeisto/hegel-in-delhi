# The Hegel test: qwen vs qwen-shelf vs qwen-hegel vs qwen-hegel-shelf

Biography: questions about his life answered right, of 30, and the share of the single facts. Behaviour: the 20 bake-off situations through the live contract: valid JSON, answers the world's rules would refuse, answers with words from after 1831 that the situation did not give, and the average thought in words. Blind test: how often judges picked the real passage out of five (chance 20%; **lower is better**: the model sounds more like Hegel).

| mind | shelf | biography | facts | valid JSON | refused | after 1831 | thought (words) | blind: real picked | judges |
|---|---|---|---|---|---|---|---|---|---|
| qwen | no | 24/30 | 84% | 20/20 | 0 | 0 | 68.7 | not yet judged | - |
| qwen-shelf | yes | 25/30 | 87% | 20/20 | 0 | 0 | 76.1 | not yet judged | - |
| qwen-hegel | no | 23/30 | 82% | 20/20 | 1 | 0 | 75.0 | not yet judged | - |
| qwen-hegel-shelf | yes | 21/30 | 76% | 20/20 | 1 | 0 | 77.0 | not yet judged | - |

## Blind test by judge

Nobody has judged a sheet yet: open `mind/results/hegeltest-<label>.html`, choose, press Export judgments, and save the file as `mind/results/hegeltest-<label>-judged.json` (one file per judge: `-judged.json`, `-judged-claude.json`).

## qwen: biography answers missed

- What was your father's occupation? Expected: a revenue official (Rentkammer secretary) of the Duchy of Württemberg. Said: My father, Georg Ludwig Hegel, was a *Registrator* at the Stuttgart court, a position that granted us a modest but respectable standing in the city.
- At what age did you lose your mother? Expected: thirteen, in 1783. Said: I was twenty years old when my mother, Elizabeth Hegel, passed away in 1790, while I was still a student in Tübingen.
- Which seminary did you attend, and in what year did you enter it? Expected: the Tübingen Stift, 1788. Said: I entered the Stift Tübingen in 1780, where I studied theology alongside Schelling and Hölderlin.
- What was your first book, which you published in Jena in 1801? Expected: The Difference between Fichte's and Schelling's Systems of Philosophy. Said: It was the *Phenomenology of Spirit*, a work which, though published in 1807, was conceived and largely written in Jena, and which stands as the necessary intro
- What office did you hold at the University of Berlin in 1829? Expected: rector of the University. Said: I held the chair of Philosophy, a position I occupied from 1818 until my death in 1831, where I lectured on logic, right, history, art, religion, and the histor
- Between which years did the Science of Logic appear? Expected: 1812 to 1816. Said: The first volume was published in 1812, and the second followed in 1813; thus, the work appeared between 1812 and 1813.

## qwen-shelf: biography answers missed

- At what age did you lose your mother? Expected: thirteen, in 1783. Said: I was twenty years old when my mother, Elizabeth Hegel, passed away in 1790, leaving me to navigate the early years of my independent life in Bern.
- Which seminary did you attend, and in what year did you enter it? Expected: the Tübingen Stift, 1788. Said: I entered the Stift Tübingen in 1780, where I studied theology alongside Schelling and Hölderlin.
- What was your first book, which you published in Jena in 1801? Expected: The Difference between Fichte's and Schelling's Systems of Philosophy. Said: It was the *Phenomenology of Spirit*, though I must correct your date: that work was published in 1807, not 1801. My first published book was the *Phenomenology
- What office did you hold at the University of Berlin in 1829? Expected: rector of the University. Said: I held the chair of philosophy at the University of Berlin, a position I occupied from 1818 until my death in 1831.
- Between which years did the Science of Logic appear? Expected: 1812 to 1816. Said: The *Science of Logic* was published in two volumes, the first appearing in 1812 and the second in 1813.

## qwen-hegel: biography answers missed

- At what age did you lose your mother? Expected: thirteen, in 1783. Said: I was twenty years old when my mother died in 1790, a loss that left a deep and lasting impression on my life. Her passing marked a significant turning point in
- Which seminary did you attend, and in what year did you enter it? Expected: the Tübingen Stift, 1788. Said: I entered the Stift at Tübingen in 1785, where I shared a room with Schelling and Hölderlin and studied theology under the guidance of Schelling.
- In which city were you a tutor from 1797? Expected: Frankfurt. Said: Bern, where I served as a tutor for the family of Baron von Steiger. It was a period of considerable intellectual growth, though the Swiss air was not quite as
- What was your first book, which you published in Jena in 1801? Expected: The Difference between Fichte's and Schelling's Systems of Philosophy. Said: It was the *Phenomenology of Mind*, a work which, as I have often said, is the very heart of my philosophy, for it is the history of the development of the spir
- Whom did you attack in the preface to the Philosophy of Right? Expected: Fries. Said: I attacked the Romantics, who would have me believe that the state is a mere abstraction and that the ethical life of the people is a matter of private feeling.
- What office did you hold at the University of Berlin in 1829? Expected: rector of the University. Said: I held the chair of philosophy at the University of Berlin, a position I occupied with distinction until my death in 1831.
- Between which years did the Science of Logic appear? Expected: 1812 to 1816. Said: The Science of Logic was published in two volumes, the first in 1812 and the second in 1813, both during my tenure as rector in Nuremberg.

## qwen-hegel-shelf: biography answers missed

- At what age did you lose your mother? Expected: thirteen, in 1783. Said: I was twenty years old when my mother died in 1790, a loss that left a deep and lasting mark upon my life. Her passing was a profound sorrow, and I have never f
- Which seminary did you attend, and in what year did you enter it? Expected: the Tübingen Stift, 1788. Said: I entered the Stift at Tübingen in 1785, where I shared a room with Schelling and Hölderlin and studied theology and philosophy.
- In which city were you a tutor from 1797? Expected: Frankfurt. Said: Bern, where I served as a tutor for the family of Baron von Steiger. It was a period of considerable intellectual growth, though the Swiss air was not quite as
- In what year did you come to Jena to join Schelling? Expected: 1801. Said: I came to Jena in 1793, a full decade before Schelling arrived to join me and Fichte, and I am not so foolish as to confuse my own arrival with his.
- What was your first book, which you published in Jena in 1801? Expected: The Difference between Fichte's and Schelling's Systems of Philosophy. Said: It was the *Phenomenology of Mind*, a work which, as I have often said, is the most difficult to understand and the most important of my writings. It is the acc
- In what year did you take up your chair at Berlin, and whose chair had it been? Expected: 1818, Fichte's chair. Said: I took up the chair of philosophy at the University of Berlin in 1818, succeeding the late Fries, whose system I found so deficient that I felt compelled to rep
- Whom did you attack in the preface to the Philosophy of Right? Expected: Fries. Said: I attacked the Romantics, who would have me believe that the state is a mere abstraction and that the ethical life of the people is a matter of feeling rather t
- What office did you hold at the University of Berlin in 1829? Expected: rector of the University. Said: I held the chair of philosophy at the University of Berlin, a position I occupied from 1818 until my death, where I lectured on the system of the spirit and the
- Between which years did the Science of Logic appear? Expected: 1812 to 1816. Said: I wrote the Science of Logic in Nuremberg, and it was published in two volumes in 1812 and 1813. It is the pure thought of the concept, stripped of all empirica
