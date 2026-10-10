"""Give each call its own response contract without changing the character or facts."""
import re

CONTRACTS = {
    'choice': ('This call records the answer to the specific yes-or-no question in the user message. '
               'Return only the requested object with answer yes or no. Do not return another world decision.'),
    'day-planning': ('This call plans the day before any step is executed. Return only the plan object requested in the user message: '
                     'a list of times and intentions. Do not return a world decision. These are intentions, not completed events.'),
    'writing': ('This call writes the work itself after a decision to write. Return only the writing object requested in the user message: '
                'title, kind, to, continues, text. Do not return a world decision. The text is the work, not an explanation of your plan.'),
    'planning': ('This call plans a sitting after a decision to write. Return only the sitting object requested in the user message: '
                 'title, kind, to, continues, about. Do not return another world decision or the work itself.'),
    'argument': ('This call writes an argumentative note about the supplied passage. Return only the requested prose. '
                 'Do not return a world decision or JSON. Stay within the supplied evidence and the requested length.'),
}


def for_task(messages, task):
    """Copy a conversation, replacing only the standard system answer section.

    Earlier decisions remain in the history as decisions, not factual evidence.
    Any later system sections (including memory policy) are retained. Custom
    personas without the standard heading retain their text and receive an
    explicit task override. The source conversation is never modified.
    """
    if task not in CONTRACTS:
        raise ValueError('Unknown response task: ' + task)
    result = [dict(m) for m in messages]
    if not result or result[0].get('role') != 'system':
        raise ValueError('A task-specific character call requires a system persona')
    system = result[0]['content']
    system = re.sub(r'^## Your answer\n.*?(?=^## |\Z)', '', system, flags=re.M | re.S).rstrip()
    result[0]['content'] = system + '\n\n## This call\n\n' + CONTRACTS[task] + '\n'
    return result
