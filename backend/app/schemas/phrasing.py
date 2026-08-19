"""A sentence the server wrote, carrying what it takes to write it again.

Some of what this app says can only be composed on the server, because that is
where the policy and the bill are: "your room is ₹8,000 a day and you are
covered for ₹5,000" is not a label, it is a sentence about two numbers that
only exist after adjudication.

Sending only the finished English makes that text permanently English. Sending
only a key loses the sentence for anyone whose language has not been written
yet. So all three travel: the key that says which sentence this is, the English
as composed, and the values that were written into it.

The reader's own language is looked up under the key and the values are put
back into it there. Where there is no translation, the English arrives already
complete, which is the same fallback the rest of the interface has, and nothing
ever renders a key.

Amounts are formatted here rather than passed as numbers. A rupee figure is
grouped the same way in every language this app speaks, and a family reading
one off this screen has to be able to point at the same figure on a bill.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Phrase(BaseModel):
    key: str
    """Which sentence this is. Stable across wordings of the same fact, and
    distinct where two wordings are genuinely different sentences."""

    text: str
    """The sentence in English, with its values already in place."""

    values: dict[str, str] = Field(default_factory=dict)
    """What was written into it, by the name the translation uses."""

    def __str__(self) -> str:
        return self.text


def phrase(key: str, text: str, **values: str) -> Phrase:
    """Shorthand for building one at a call site, where it reads better."""
    return Phrase(key=key, text=text, values=values)
