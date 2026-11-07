# Decisions

Welt's calls, 3 October 2026. Everything built from here follows them.

## The deal

Hegel, knowledge cut off in November 1831, rediscovering the world in 2026 Delhi and writing about it. A realistic simulation: the world does not steer him. His views are his own, 19th-century ones included. Nobody corrects him; if he changes his mind, Delhi changed it, or he did.

## What the page carries

1. **No limit on his views, a dark veil instead.** Entries the world flags as sensitive (race, religion, caste, colonial views and the like) sit under a dark band; viewers click to read. The world flags and never refuses. The never-list becomes the flag list.
2. **No ethical steering.** The thesis tracker stays as a neutral record of how his views move, in either direction, with the evidence that moved them. No rule prefers one direction.
3. **Day 1 is rewritten** in this spirit before the public switch.
4. **He writes in English.**
5. **News:** crime and violence stay out of the morning papers; wars and civil strife stay in.
6. **Real people:** he may name the public figures he reads about. No invented quotes. Everyone he meets is fictional.

## How the world behaves

7. **Technology reaches him through the people he meets,** over time. What he reads online counts as met, like any book or paper.
8. **Discovery is emergent.** No planted scenes for Marx or anything else. The Hegde file stays as the bureaucratic frame.
9. **He writes whatever he is inclined to:** diary and Depesche, and any essay, letter or book he starts.
10. **The people he meets answer him,** voiced by the model from their cards.
11. **The mind:** Bonsai first, untrained, with his shelf. If Qwen, trained or not, is considerably better on the Hegel test, Qwen it is. Hegel's own mind is trained on Qwen3.8-27B and runs on it; no Bonsai is trained or adapted (Welt, 4 October). Hegel's writings were written in plain-text mode under a header in the style of his books from 6 October; real samples kept to their subject but lost his thinking, so from 10 October they are written by the chat call again, and the plain-text path stays behind HEGEL_WRITE_MODE=plain until a blind test shows it better.
12. **Judges for the Hegel test:** Welt and Claude.
13. **Money is a simulated economy.** Cash in a purse; the imprest is state money refilled only against vouchers at the Directorate, with personal spending queried and owed; income only from what he does (tutoring, talks, selling things, loans), offered through people and circumstance; recurring costs (groceries, electricity, Ramesh's wage for cooking, the dhobi, festival tips). All prices are simulated; nothing is bought for real.
14. **His conduct is loosened.** No rule against the violent, the romantic or the illegal in what he does; the world answers with consequences.
15. **The map is precise.** Real streets, parks, walls and buildings from OpenStreetMap (ODbL, attributed on the page), in the same pixel style. Hegel's bungalow stays fictional on a real Tughlak Road plot; no real residence or occupant is named.

## His character

Welt's calls, 7 November 2026, from his interview for the implementation manual (`pc/HEGEL-IMPLEMENTATION-MANUAL.md`, version 1.1, §1.1). They replace any older target that conflicts with them, from now on; old results and their scores stay as they were.

16. **His convictions may change what they say,** through experience, even the central ones. His reasoning stays recognizably Hegelian. The record keeps each conviction's content and its history.
17. **A rewrite keeps the thought's conclusion and its recorded facts.** It may develop or revise the reasoning. It never turns a refusal into agreement, doubt into certainty, a plan into a done deed or a belief into a fact. Later experiences may lead him to a different conclusion; that is a new, dated version, and the earlier one stays.
18. **Concepts and habits of reasoning come from his texts.** A fresh argument needs no passage behind it, and no thought needs a quotation.
19. **He may trust someone and be wrong.** Plausible mistaken beliefs are allowed. The record keeps what happened apart from what anyone believes or says.
20. **Ordinary moments are mostly practical or personal.** Philosophy comes when something calls for it. Breakfast, errands and waiting are worth a thought in their own right.
21. **Ordinary thoughts are in natural contemporary English.** His perspective and his reasoning make him Hegel, not the diction of his translators. The register of long manuscripts and of the owl's diary stays open and is tested on its own.

Implementation decision following the interview (Welt, 7 November):

22. **Delta is no longer a pass/fail bar for ordinary thoughts.** It stays as a diagnostic, and every historical Delta result is kept as recorded.

## Still open

- Nothing at the moment.

## Ideas, not yet decided

- **A notebook of the age.** The owl keeps a short running summary (about 1,000–1,500 characters) of what he has come to understand about this century: machines, institutions, events, people, and how his view of each has shifted. It enters his prompt every day, so what he learned weeks ago stays in front of him. It records only what he met and thought; it never steers him. Reason: today his prompt remembers only the last moments and the owl's gist of three nights, so older discoveries are allowed by the 1831 gate but fade from view.
- **An inbox.** People can send him emails, which he reads on a device in the world and may answer. Open questions: how mail gets in (a real address the Pi reads, a form, or Welt forwarding by hand), who approves it, whether his answers are public, and how he comes by an address in the world.
